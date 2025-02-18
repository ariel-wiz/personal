// bank-scraper.js
import { createScraper } from 'israeli-bank-scrapers';
import fs from 'fs/promises';
import crypto from 'crypto';
import _ from 'lodash';
import moment from 'moment';

// Exit codes
const EXIT_CODES = {
    SUCCESS: 0,
    CONFIG_ERROR: 1,
    SCRAPING_ERROR: 2,
    DECRYPT_ERROR: 3,
    FILE_SYSTEM_ERROR: 4
};

const TRANSACTION_STATUS_COMPLETED = 'completed';

class Logger {
    info(message, data = null) {
        console.log(JSON.stringify({ level: 'INFO', message, data }));
    }

    error(message, error = null) {
        const errorObj = {
            level: 'ERROR',
            message,
            error: error ? {
                name: error.name,
                message: error.message,
                stack: error.stack
            } : null
        };
        console.error(JSON.stringify(errorObj));
    }

    debug(message, data = null) {
        console.log(JSON.stringify({ level: 'DEBUG', message, data }));
    }
}

const logger = new Logger();

async function getAllCredentials() {
    try {
        // Execute keychain dump command
        const { exec } = await import('child_process');
        const { promisify } = await import('util');
        const execAsync = promisify(exec);

        const { stdout } = await execAsync(
            `security dump-keychain | grep -A 4 "\"bank-scraper\""`
        );

        logger.debug(`Found keychain data: ${stdout.length} bytes`);

        const credentials = [];
        const lines = stdout.split('\n');

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            if (line.includes(`"acct"<blob>=`)) {
                const accountName = line.split('"')[3];

                if (accountName !== 'encryption-key') {
                    try {
                        const { stdout: credentialJson } = await execAsync(
                            `security find-generic-password -s "bank-scraper" -a "${accountName}" -w`
                        );
                        const parsedCred = JSON.parse(credentialJson.trim());
                        logger.debug(`Retrieved credentials for ${accountName}`, {
                            structure: Object.keys(parsedCred)
                        });
                        credentials.push(parsedCred);
                    } catch (error) {
                        logger.error(`Failed to retrieve credential for ${accountName}`, error);
                    }
                }
            }
        }

        return credentials;
    } catch (error) {
        logger.error('Failed to retrieve credentials', error);
        throw error;
    }
}

async function getEncryptionKey() {
    try {
        const { exec } = await import('child_process');
        const { promisify } = await import('util');
        const execAsync = promisify(exec);

        const { stdout } = await execAsync(
            `security find-generic-password -s "bank-scraper" -a "encryption-key" -w`
        );
        logger.debug('Retrieved encryption key', { length: stdout.trim().length });
        return stdout.trim();
    } catch (error) {
        logger.error('Failed to retrieve encryption key', error);
        throw error;
    }
}

function decrypt(encrypted, key, iv, authTag) {
    try {
        const decipher = crypto.createDecipheriv('aes-256-gcm', Buffer.from(key, 'hex'), Buffer.from(iv, 'hex'));
        decipher.setAuthTag(Buffer.from(authTag, 'hex'));
        let decrypted = decipher.update(encrypted, 'hex', 'utf8');
        decrypted += decipher.final('utf8');
        return decrypted;
    } catch (error) {
        logger.error('Decryption failed', error);
        throw error;
    }
}

async function postProcessTransactions(accountToScrape, scrapeResult) {
    logger.debug(`Processing transactions for ${accountToScrape.key}`);
    logger.debug(`Scrape result: ${JSON.stringify(scrapeResult)}`);

    if (scrapeResult.accounts) {
        try {
            let transactions = scrapeResult.accounts.flatMap((transactionAccount) => {
                logger.debug(`Processing account ${transactionAccount.accountNumber}`);

                return transactionAccount.txns
                    .map(transaction =>
                        enrichTransaction(transaction, accountToScrape.key, transactionAccount.accountNumber)
                    )
                    .filter(t => t !== null);
            });

            logger.debug(`Found ${transactions.length} transactions before filtering`);

            // Filter completed transactions
            transactions = transactions.filter(transaction =>
                transaction.status === TRANSACTION_STATUS_COMPLETED
            );

            logger.debug(`${transactions.length} transactions after filtering for completed status`);

            // Sort transactions
            transactions.sort(transactionsDateComparator);

            // Write transactions to file before returning
            try {
                await fs.writeFile(process.argv[2], JSON.stringify(transactions, null, 2));
                logger.info(`Successfully wrote ${transactions.length} transactions to ${process.argv[2]}`);
            } catch (error) {
                logger.error('Failed to write transactions to file', error);
            }

            return transactions;
        } catch (error) {
            logger.error('Error processing transactions', error);
            return [];
        }
    }

    logger.debug('No accounts found in scrape result');
    return [];
}

function enrichTransaction(transaction, companyId, accountNumber) {
    try {
        const hash = calculateTransactionHash(transaction, companyId, accountNumber);
        return {
            ...transaction,
            accountNumber,
            hash,
            memo: transaction.memo || '',
            status: transaction.status || TRANSACTION_STATUS_COMPLETED
        };
    } catch (error) {
        logger.error(`Failed to enrich transaction`, {
            error: error.message,
            transaction: JSON.stringify(transaction)
        });
        return null;
    }
}

function calculateTransactionHash(transaction, companyId, accountNumber) {
    const hashString = `${transaction.date}_${transaction.chargedAmount}_${transaction.description}_${transaction.memo}_${companyId}_${accountNumber}`;
    return hashString
        .replace(/`/g, "'")
        .replace(/00\dZ/, '000Z')
        .replace(/[\u0000-\u001F\u007F-\u009F\u200E]/g, '')
        .replace('‏', '');
}

function transactionsDateComparator(t1, t2) {
    const date1 = moment(t1.date);
    const date2 = moment(t2.date);
    if (date1.isAfter(date2)) return 1;
    if (date1.isBefore(date2)) return -1;
    return 1;
}

async function scrapeBank(decryptedCreds) {
    try {
        logger.debug('Starting bank scrape with credentials', {
            companyId: decryptedCreds.companyId,
            username: decryptedCreds.username,
            hasPassword: !!decryptedCreds.password
        });

        // Validate credentials format
        if (!decryptedCreds.companyId || !decryptedCreds.username || !decryptedCreds.password) {
            throw new Error(`Invalid credential format. Required fields missing: ${
                ['companyId', 'username', 'password']
                    .filter(field => !decryptedCreds[field])
                    .join(', ')
            }`);
        }

        const startDate = moment().subtract(30, 'days').startOf('day').toDate();

        const options = {
            companyId: decryptedCreds.companyId,
            startDate,
            showBrowser: false,
            verbose: true,
            timeout: 60000
        };

        const scraper = createScraper(options);

        logger.debug(`Starting to scrape ${decryptedCreds.companyId}`);
        const scrapeResult = await scraper.scrape(decryptedCreds);
        logger.debug(`Scrape result: ${JSON.stringify(scrapeResult)}`);

        if (!scrapeResult.success) {
            throw new Error(`${scrapeResult.errorType}: ${scrapeResult.errorMessage}`);
        }

        const processedTransactions = await postProcessTransactions(
            { key: decryptedCreds.companyId },
            scrapeResult
        );

        logger.debug(`Successfully scraped ${processedTransactions.length} transactions from ${decryptedCreds.companyId}`);
        return processedTransactions;
    } catch (error) {
        logger.error(`Error scraping ${decryptedCreds.companyId}`, error);
        return null;
    }
}

async function main() {
    try {
        const scriptStartTime = Date.now();
        const [,, outputPath] = process.argv;

        if (!outputPath) {
            logger.error('Missing required outputPath argument');
            return EXIT_CODES.CONFIG_ERROR;
        }

        logger.info('Starting bank scraper');

        // Get encryption key
        logger.debug('Retrieving encryption key');
        const key = await getEncryptionKey();
        logger.debug(`Retrieved encryption key (Length: ${key.length})`);

        // Get credentials
        logger.debug('Retrieving credentials from keychain');
        const credentials = await getAllCredentials();
        logger.debug('Retrieved credentials', {
            count: credentials.length,
            companies: credentials.map(c => c.companyId)
        });

        if (credentials.length === 0) {
            throw new Error('No credentials found');
        }

        const totalAccounts = credentials.length;
        let successfulScrapes = 0;
        let failedScrapes = 0;
        let allTransactions = [];
        let scrapeResults = [];

        for (let i = 0; i < totalAccounts; i++) {
            const cred = credentials[i];
            const startTime = Date.now();
            try {
                logger.debug(`${i + 1}/${totalAccounts} - Starting to scrape ${cred.companyId}`);

                // Decrypt the password
                const decryptedCred = {
                    ...cred,
                    password: decrypt(cred.password, key, cred.iv, cred.authTag)
                };

                const transactions = await scrapeBank(decryptedCred);
                const timeTaken = ((Date.now() - startTime) / 1000).toFixed(2);

                if (transactions && transactions.length > 0) {
                    allTransactions.push(...transactions);
                    logger.info(`${i + 1}/${totalAccounts} - Successfully scraped ${cred.companyId} (Time: ${timeTaken}s)`);
                    successfulScrapes++;
                } else {
                    logger.error(`${i + 1}/${totalAccounts} - Failed scraping ${cred.companyId} (Time: ${timeTaken}s) - No transactions found`);
                    failedScrapes++;
                }
                scrapeResults.push({ company: cred.companyId, success: true, timeTaken });
            } catch (error) {
                const timeTaken = ((Date.now() - startTime) / 1000).toFixed(2);
                logger.error(`${i + 1}/${totalAccounts} - Failed scraping ${cred.companyId} (Time: ${timeTaken}s) - Error: ${error.message}`);
                scrapeResults.push({ company: cred.companyId, success: false, timeTaken });
                failedScrapes++;
            }
        }

        if (allTransactions.length > 0) {
            await fs.writeFile(outputPath, JSON.stringify(allTransactions, null, 2));
            logger.info(`Results saved to ${outputPath}`);
        }

        const totalExecutionTime = Date.now() - scriptStartTime;
        const minutes = Math.floor(totalExecutionTime / 60000);
        const seconds = ((totalExecutionTime % 60000) / 1000).toFixed(2);

        if (successfulScrapes === totalAccounts) {
            logger.info(`✅ All ${totalAccounts}/${totalAccounts} accounts were successfully scraped in ${minutes}m ${seconds}s.`);
        } else {
            logger.info(`⚠️ ${successfulScrapes}/${totalAccounts} accounts were successfully scraped. Total execution time: ${minutes}m ${seconds}s.`);
        }

        return failedScrapes > 0 ? EXIT_CODES.SCRAPING_ERROR : EXIT_CODES.SUCCESS;
    } catch (error) {
        logger.error(`Script failed with unexpected error: ${error.message}`);
        return EXIT_CODES.SCRAPING_ERROR;
    }
}

// Run the script
main().then(exitCode => {
    process.exit(exitCode);
}).catch(error => {
    logger.error('Fatal error', error);
    process.exit(EXIT_CODES.SCRAPING_ERROR);
});
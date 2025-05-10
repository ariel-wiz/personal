import { createScraper } from 'israeli-bank-scrapers';
import fs from 'fs/promises';
import crypto from 'crypto';
import _ from 'lodash';
import moment from 'moment';

// Exit codes
const EXIT_CODES = {
    SUCCESS: 0,               // All accounts scraped successfully
    PARTIAL_SUCCESS: 1,       // Some accounts scraped successfully
    COMPLETE_FAILURE: 2,      // No accounts scraped successfully
    CONFIG_ERROR: 3,          // Configuration error
    DECRYPT_ERROR: 4,         // Decryption error
    FILE_SYSTEM_ERROR: 5      // File system error
};

const TRANSACTION_STATUS_COMPLETED = 'completed';

// Track successful and failed account scraping attempts
const successfulAccounts = [];
const failedAccounts = [];

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
                logger.debug(`Successfully wrote ${transactions.length} transactions to ${process.argv[2]}`);
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

async function getPackageVersion() {
    try {
        const { exec } = await import('child_process');
        const { promisify } = await import('util');
        const execAsync = promisify(exec);

        const { stdout } = await execAsync(
            `npm list israeli-bank-scrapers --json`
        );

        const npmList = JSON.parse(stdout);

        if (npmList && npmList.dependencies && npmList.dependencies['israeli-bank-scrapers']) {
            return npmList.dependencies['israeli-bank-scrapers'].version;
        } else {
            logger.debug('Package information not found in npm list output');
            return 'unknown';
        }
    } catch (error) {
        logger.error('Failed to get package version from npm list', error);
        return 'unknown';
    }
}

async function scrapeBank(decryptedCreds) {
    try {
        logger.debug('Starting bank scrape with credentials', {
            companyId: decryptedCreds.companyId,
            username: decryptedCreds.username,
            hasPassword: !!decryptedCreds.password,
            hasCardLast6: !!decryptedCreds.card6Digits
        });

//        logger.debug(`Decrypted credentials for company ${decryptedCreds.companyId} - username: "${decryptedCreds.username}", password: "${decryptedCreds.password}", card last 6 digits: "${decryptedCreds.card6Digits?.trim() || 'N/A'}"`);

        // Validate credentials format
        if (!decryptedCreds.companyId || !decryptedCreds.username || !decryptedCreds.password) {
            throw new Error(`Invalid credential format. Required fields missing: ${
                ['companyId', 'username', 'password']
                    .filter(field => !decryptedCreds[field])
                    .join(', ')
            }`);
        }

////         Check if the bank is Beinleumi
//        if (decryptedCreds.companyId !== 'max') {
//            logger.info(`Skipping ${decryptedCreds.companyId} as it's not Beinleumi bank`);
//            return {
//                success: true,
//                errorType: 'SKIP',
//                errorMessage: 'Not a Beinleumi bank account - skipping',
//                companyId: decryptedCreds.companyId,
//                username: decryptedCreds.username
//            };
//        }

        const startDate = moment().subtract(30, 'days').startOf('day').toDate();

        const options = {
            companyId: decryptedCreds.companyId,
            startDate,
            showBrowser: true,
            verbose: true,
            timeout: 60000
        };

        const scraper = createScraper(options);

        logger.debug(`Starting to scrape ${decryptedCreds.companyId}`);
        const scrapeResult = await scraper.scrape(decryptedCreds);
        logger.debug(`Scrape result: ${JSON.stringify(scrapeResult)}`);

        if (!scrapeResult.success) {
            return {
                success: false,
                errorType: scrapeResult.errorType,
                errorMessage: scrapeResult.errorMessage,
                companyId: decryptedCreds.companyId
            };
        }

        const processedTransactions = await postProcessTransactions(
            { key: decryptedCreds.companyId },
            scrapeResult
        );

        logger.debug(`Successfully scraped ${processedTransactions.length} transactions from ${decryptedCreds.companyId}`);
        return processedTransactions;
    } catch (error) {
        logger.error(`Error scraping ${decryptedCreds.companyId}`, error);
        return {
            success: false,
            errorType: error.name || 'GENERIC',
            errorMessage: error.message,
            companyId: decryptedCreds.companyId
        };
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

        const version = await getPackageVersion();
        logger.info(`Starting bank scraper using israeli-bank-scrapers version: ${version}`);

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

                if (cred.cardLast6 && cred.cardIv && cred.cardAuthTag) {
                    decryptedCred.card6Digits = decrypt(cred.cardLast6, key, cred.cardIv, cred.cardAuthTag);
                    decryptedCred.id = cred.username;
                }

                const transactions = await scrapeBank(decryptedCred);
                const timeTaken = ((Date.now() - startTime) / 1000).toFixed(2);

                if (Array.isArray(transactions)) {
                    allTransactions.push(...transactions);
                    logger.info(`${i + 1}/${totalAccounts} - Successfully scraped ${cred.companyId} (Time: ${timeTaken}s)`);
                    successfulAccounts.push(cred.companyId);
                } else if (transactions.errorMessage) {
                    // Handle error case
                    logger.info(`${i + 1}/${totalAccounts} - Failed scraping ${cred.companyId} - Error details: ${transactions.errorMessage} (Time: ${timeTaken}s)`);
                    failedAccounts.push({ companyId: cred.companyId, error: transactions.errorMessage });
                } else {
                    logger.info(`${i + 1}/${totalAccounts} - Failed scraping ${cred.companyId} - Error details: No transactions found (Time: ${timeTaken}s)`);
                    failedAccounts.push({ companyId: cred.companyId, error: 'No transactions found' });
                }
                scrapeResults.push({ company: cred.companyId, success: Array.isArray(transactions), timeTaken });
            } catch (error) {
                const timeTaken = ((Date.now() - startTime) / 1000).toFixed(2);
                logger.info(`${i + 1}/${totalAccounts} - Failed scraping ${cred.companyId} - ${error.message} (Time: ${timeTaken}s)`);
                logger.error(`${i + 1}/${totalAccounts} - Failed scraping ${cred.companyId} (Time: ${timeTaken}s) - Error: ${error.message}`);
                scrapeResults.push({ company: cred.companyId, success: false, timeTaken });
                failedAccounts.push({ companyId: cred.companyId, error: error.message });
            }
        }

        if (allTransactions.length > 0) {
            await fs.writeFile(outputPath, JSON.stringify(allTransactions, null, 2));
            logger.info(`Results saved to ${outputPath}`);
        }

        const totalExecutionTime = Date.now() - scriptStartTime;
        const minutes = Math.floor(totalExecutionTime / 60000);
        const seconds = ((totalExecutionTime % 60000) / 1000).toFixed(2);

        // Determine exit code based on success status
        let exitCode;
        if (successfulAccounts.length === totalAccounts) {
            logger.info(`✅ All ${totalAccounts}/${totalAccounts} accounts were successfully scraped in ${minutes}m ${seconds}s.`);
            exitCode = EXIT_CODES.SUCCESS; // All accounts successful
        } else if (successfulAccounts.length > 0) {
            logger.info(`⚠️ Only ${successfulAccounts.length}/${totalAccounts} accounts were successfully scraped in ${minutes}m ${seconds}s.`);
            logger.info(`Failed accounts: ${failedAccounts.map(a => a.companyId).join(', ')}`);
            exitCode = EXIT_CODES.PARTIAL_SUCCESS; // Some accounts successful
        } else {
            logger.info(`❌ No accounts were successfully scraped in ${minutes}m ${seconds}s.`);
            logger.info(`Failed accounts: ${failedAccounts.map(a => a.companyId).join(', ')}`);
            exitCode = EXIT_CODES.COMPLETE_FAILURE; // No accounts successful
        }

        return exitCode;
    } catch (error) {
        // Categorize errors for more specific exit codes
        logger.error(`Script failed with unexpected error: ${error.message}`, error);

        if (error.message.includes('config') || error.message.includes('argument')) {
            return EXIT_CODES.CONFIG_ERROR;
        } else if (error.message.includes('decrypt') || error.message.includes('crypto')) {
            return EXIT_CODES.DECRYPT_ERROR;
        } else if (error.message.includes('file') || error.message.includes('write') || error.message.includes('read')) {
            return EXIT_CODES.FILE_SYSTEM_ERROR;
        } else {
            return EXIT_CODES.COMPLETE_FAILURE;
        }
    }
}

// Run the script
main().then(exitCode => {
    logger.debug(`Exiting with code: ${exitCode}`);

    // Ensure all console output is flushed before exit
    console.log(JSON.stringify({
        level: 'EXIT',
        code: exitCode,
        message: `Explicit exit with code ${exitCode}`
    }));

    // Force synchronous exit with the correct code
    process.exitCode = exitCode;

    // Give a small delay to ensure everything is flushed
    setTimeout(() => {
        process.exit(exitCode);
    }, 100);
}).catch(error => {
    logger.error('Fatal error', error);

    console.log(JSON.stringify({
        level: 'EXIT',
        code: EXIT_CODES.COMPLETE_FAILURE,
        message: `Error exit with code ${EXIT_CODES.COMPLETE_FAILURE}: ${error.message}`
    }));

    process.exitCode = EXIT_CODES.COMPLETE_FAILURE;

    setTimeout(() => {
        process.exit(EXIT_CODES.COMPLETE_FAILURE);
    }, 100);
});

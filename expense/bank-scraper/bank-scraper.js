// bank-scraper.js
import { createScraper } from 'israeli-bank-scrapers';
import fs from 'fs/promises';
import path from 'path';
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

// Custom logger that writes to stdout for Python to capture
class Logger {
    info(message) {
        console.log(JSON.stringify({ level: 'INFO', message }));
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

    debug(message) {
        console.log(JSON.stringify({ level: 'DEBUG', message }));
    }
}

const logger = new Logger();

const TRANSACTION_STATUS_COMPLETED = 'completed';

function calculateTransactionHash(transaction, companyId, accountNumber) {
    const hashString = `${transaction.date}_${transaction.chargedAmount}_${transaction.description}_${transaction.memo}_${companyId}_${accountNumber}`;
    return hashString
        .replace(/`/g, "'")
        .replace(/00\dZ/, '000Z')
        .replace(/[\u0000-\u001F\u007F-\u009F\u200E]/g, '')
        .replace('‏', '');
}

function enrichTransaction(transaction, companyId, accountNumber) {
    const hash = calculateTransactionHash(transaction, companyId, accountNumber);
    const enrichedTransaction = {
        ...transaction,
        accountNumber,
        hash,
    };
    return enrichedTransaction;
}

function transactionsDateComparator(t1, t2) {
    const date1 = moment(t1.date);
    const date2 = moment(t2.date);
    if (date1.isAfter(date2)) return 1;
    if (date1.isBefore(date2)) return -1;
    return 1;
}

async function postProcessTransactions(accountToScrape, scrapeResult) {
    if (scrapeResult.accounts) {
        let transactions = scrapeResult.accounts.flatMap((transactionAccount) => {
            return transactionAccount.txns.map((transaction) =>
                enrichTransaction(transaction, accountToScrape.key, transactionAccount.accountNumber),
            );
        });

        transactions = transactions.filter((transaction) => transaction.status === TRANSACTION_STATUS_COMPLETED);
        transactions.sort(transactionsDateComparator);
        return transactions;
    }
    return [];
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

async function decryptCredentials(credentials, keyPath = '.key') {
    try {
        const keyContent = await fs.readFile(keyPath, 'utf8');
        const key = keyContent.trim();
        
        if (credentials.password && credentials.iv && credentials.authTag) {
            credentials.password = decrypt(
                credentials.password,
                key,
                credentials.iv,
                credentials.authTag
            );
        }
        
        return credentials;
    } catch (error) {
        logger.error('Error decrypting credentials', error);
        throw error;
    }
}

async function scrapeBank(credentials, keyPath) {
    try {
        const decryptedCreds = await decryptCredentials(credentials, keyPath);
        const startDate = moment().subtract(30, 'days').startOf('day').toDate();

        const options = {
            companyId: decryptedCreds.companyId,
            startDate,
            showBrowser: false,
            verbose: true,
            timeout: 60000
        };

        const scraper = createScraper(options);
        
        logger.info(`Starting to scrape ${decryptedCreds.companyId}`);
        const scrapeResult = await scraper.scrape(decryptedCreds);

        if (!scrapeResult.success) {
            throw new Error(`${scrapeResult.errorType}: ${scrapeResult.errorMessage}`);
        }

        const processedTransactions = await postProcessTransactions(
            { key: decryptedCreds.companyId },
            scrapeResult
        );

        logger.info(`Successfully scraped ${decryptedCreds.companyId}`);
        return processedTransactions;
    } catch (error) {
        logger.error(`Error scraping ${credentials.companyId}`, error);
        return null;
    }
}

async function main() {
     try {
        // Get input paths from command line arguments
        const [,, configPath, outputPath, keyPath] = process.argv;
        
        if (!configPath || !outputPath) {
            logger.error('Missing required arguments: configPath and outputPath');
            return EXIT_CODES.CONFIG_ERROR;
        }

        // Load credentials
        logger.info(`Loading config from ${configPath}`);
        const configContent = await fs.readFile(configPath, 'utf8');
        const credentials = JSON.parse(configContent);

        if (!Array.isArray(credentials)) {
            logger.error('Config must be an array of credential objects');
            return EXIT_CODES.CONFIG_ERROR;
        }

        // Create output directory if needed
        const outputDir = path.dirname(outputPath);
        await fs.mkdir(outputDir, { recursive: true });

        // Scrape each bank
        let allTransactions = [];
        let hasErrors = false;
        
        for (const cred of credentials) {
            try {
                // Pass the key path to decryptCredentials
                const transactions = await scrapeBank(cred, keyPath);
                if (transactions && transactions.length > 0) {
                    allTransactions.push(...transactions);
                }
            } catch (error) {
                hasErrors = true;
                logger.error(`Failed to scrape ${cred.companyId}`, error);
            }
        }

        if (allTransactions.length === 0) {
            logger.error('No successful scraping results to save');
            return hasErrors ? EXIT_CODES.SCRAPING_ERROR : EXIT_CODES.SUCCESS;
        }

        // Save results as a **flattened list**
        await fs.writeFile(outputPath, JSON.stringify(allTransactions, null, 2));
        logger.info(`Results saved to ${outputPath}`);
        
        return hasErrors ? EXIT_CODES.SCRAPING_ERROR : EXIT_CODES.SUCCESS;
    } catch (error) {
        if (error.code === 'ENOENT') {
            logger.error('File not found error', error);
            return EXIT_CODES.FILE_SYSTEM_ERROR;
        }
        logger.error('Script failed with unexpected error', error);
        return EXIT_CODES.SCRAPING_ERROR;
    }
}

// Run the script and handle exit code
main().then(exitCode => {
    process.exit(exitCode);
}).catch(error => {
    logger.error('Fatal error', error);
    process.exit(EXIT_CODES.SCRAPING_ERROR);
});
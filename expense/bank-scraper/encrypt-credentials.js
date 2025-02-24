import { createInterface } from 'readline/promises';
import { CompanyTypes } from 'israeli-bank-scrapers';
import { getEncryptionKey, storeCredential, getAllCredentials, encrypt } from './keychain-utils.js';

const rl = createInterface({
    input: process.stdin,
    output: process.stdout
});

async function askQuestion(question, options) {
    console.log(question);
    options.forEach((option, index) => {
        console.log(`${index + 1}. ${option}`);
    });

    while (true) {
        const answer = await rl.question('Enter number: ');
        const index = parseInt(answer) - 1;
        if (index >= 0 && index < options.length) {
            return options[index];
        }
        console.log('Invalid selection. Please try again.');
    }
}

async function encryptCredentials() {
    try {
        console.log('Getting encryption key...');
        const key = await getEncryptionKey();
        console.log('Successfully retrieved encryption key');

        console.log('\nAvailable banks:');
        const banks = Object.entries(CompanyTypes).map(([name, id]) => ({
            name: name.charAt(0).toUpperCase() + name.slice(1),
            id: id
        }));

        const bankNames = banks.map(bank => `${bank.name} (${bank.id})`);
        const selectedBank = await askQuestion('Select your bank:', bankNames);
        const companyId = banks[bankNames.indexOf(selectedBank)].id;

        // Get credentials
        console.log('\nEnter your credentials:');
        const username = await rl.question('Username: ');
        const password = await rl.question('Password: ');

        // Create new credential object
        const newCredential = {
            companyId,
            username
        };

        console.log('\nEncrypting password...');
        const encrypted = encrypt(password, key);
        console.log('Password encrypted successfully');

        // Add encrypted data
        newCredential.password = encrypted.encrypted;
        newCredential.iv = encrypted.iv;
        newCredential.authTag = encrypted.authTag;

        // Store in keychain
        const accountName = `${companyId}-${username}`;
        console.log(`\nStoring credentials in keychain for account: ${accountName}`);
        await storeCredential(accountName, newCredential);
        console.log('Credentials stored successfully');

        // Verify storage
        console.log('\nVerifying stored credentials...');
        const allCredentials = await getAllCredentials();
        const storedCred = allCredentials.find(cred =>
            cred.companyId === companyId && cred.username === username
        );

        if (storedCred) {
            console.log('Credentials verified successfully');
            console.log('Stored credential structure:', {
                companyId: storedCred.companyId,
                username: storedCred.username,
                hasPassword: !!storedCred.password,
                hasIV: !!storedCred.iv,
                hasAuthTag: !!storedCred.authTag
            });
        } else {
            throw new Error('Failed to verify stored credentials');
        }

        console.log('\nCredential storage complete!');
        console.log(`Total number of stored credentials: ${allCredentials.length}`);

    } catch (error) {
        console.error('Error:', error.message);
        if (error.stack) {
            console.error('Stack trace:', error.stack);
        }
    } finally {
        rl.close();
    }
}

// Run the script
encryptCredentials();
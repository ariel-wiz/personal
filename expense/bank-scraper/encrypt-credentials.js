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

async function displayCredentialsList(credentials) {
    console.log('\nStored credentials:');
    credentials.forEach((cred, index) => {
        console.log(`${index + 1}. ${cred.companyId} - ${cred.username}`);
    });
    return credentials;
}

async function addNewCredential(key) {
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

    let cardLast6Encrypted;
    if (companyId === 'isracard') {
        const last6 = await rl.question('Last 6 digits of the credit card: ');
        if (!/^\d{6}$/.test(last6)) {
            throw new Error('Invalid input. Must be exactly 6 digits.');
        }

        console.log('Encrypting card last 6 digits...');
        cardLast6Encrypted = encrypt(last6, key);
        console.log('Card digits encrypted successfully');
    }

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

    if (cardLast6Encrypted) {
        newCredential.cardLast6 = cardLast6Encrypted.encrypted;
        newCredential.cardIv = cardLast6Encrypted.iv;
        newCredential.cardAuthTag = cardLast6Encrypted.authTag;
    }

    // Store in keychain
    const accountName = `${companyId}-${username}`;
    console.log(`\nStoring credentials in keychain for account: ${accountName}`);
    await storeCredential(accountName, newCredential);
    console.log('Credentials stored successfully');

    return { accountName, credential: newCredential };
}

async function editExistingCredential(key, credentials) {
    await displayCredentialsList(credentials);

    while (true) {
        const answer = await rl.question('\nEnter number of the account to edit: ');
        const index = parseInt(answer) - 1;

        if (index >= 0 && index < credentials.length) {
            const selectedCred = credentials[index];
            console.log(`\nEditing credentials for: ${selectedCred.companyId} - ${selectedCred.username}`);

            // Ask for new password
            const newPassword = await rl.question('Enter new password: ');

            console.log('\nEncrypting new password...');
            const encrypted = encrypt(newPassword, key);
            console.log('New password encrypted successfully');

            // Update credential with new password
            const updatedCredential = {
                ...selectedCred,
                password: encrypted.encrypted,
                iv: encrypted.iv,
                authTag: encrypted.authTag
            };

            // Store updated credential
            const accountName = `${selectedCred.companyId}-${selectedCred.username}`;
            console.log(`\nUpdating credentials in keychain for account: ${accountName}`);
            await storeCredential(accountName, updatedCredential);
            console.log('Credentials updated successfully');

            return { accountName, credential: updatedCredential };
        }

        console.log('Invalid selection. Please try again.');
    }
}

async function encryptCredentials() {
    try {
        console.log('Getting encryption key...');
        const key = await getEncryptionKey();
        console.log('Successfully retrieved encryption key');

        // Get all existing credentials
        const allCredentials = await getAllCredentials();
        console.log(`Found ${allCredentials.length} stored credentials`);

        // Ask whether to add new or edit existing credentials
        const operation = await askQuestion('What would you like to do?', [
            'Add a new credential',
            'Edit an existing credential'
        ]);

        let result;
        if (operation === 'Add a new credential') {
            result = await addNewCredential(key);
            console.log('\nCredential added successfully!');
        } else {
            if (allCredentials.length === 0) {
                console.log('No existing credentials found to edit. Please add a new credential first.');
                result = await addNewCredential(key);
                console.log('\nCredential added successfully!');
            } else {
                result = await editExistingCredential(key, allCredentials);
                console.log('\nCredential updated successfully!');
            }
        }

        // Verify storage
        console.log('\nVerifying stored credentials...');
        const updatedCredentials = await getAllCredentials();
        const storedCred = updatedCredentials.find(cred =>
            cred.companyId === result.credential.companyId &&
            cred.username === result.credential.username
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

        console.log('\nOperation complete!');
        console.log(`Total number of stored credentials: ${updatedCredentials.length}`);

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
// encrypt-credentials.js
import crypto from 'crypto';
import fs from 'fs/promises';
import { createInterface } from 'readline/promises';
import { CompanyTypes } from 'israeli-bank-scrapers';

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

async function loadExistingCredentials() {
    try {
        const content = await fs.readFile('.env', 'utf8');
        return JSON.parse(content);
    } catch (error) {
        // If file doesn't exist or is invalid, return empty array
        return [];
    }
}

async function encryptCredentials() {
    try {
        // Load existing encryption key or generate new one if it doesn't exist
        let key;
        try {
            key = (await fs.readFile('.key', 'utf8')).trim();
        } catch (error) {
            key = crypto.randomBytes(32).toString('hex');
            await fs.writeFile('.key', key);
        }

        // Load existing credentials
        const existingCredentials = await loadExistingCredentials();
        
        console.log('\nAvailable banks:');
        const banks = Object.entries(CompanyTypes).map(([name, id]) => ({
            name: name.charAt(0).toUpperCase() + name.slice(1), // Capitalize first letter
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

        // Encrypt password
        const encrypted = encrypt(password, key);
        
        // Add encrypted data
        newCredential.password = encrypted.encrypted;
        newCredential.iv = encrypted.iv;
        newCredential.authTag = encrypted.authTag;

        // Add new credentials to existing ones
        existingCredentials.push(newCredential);

        // Save updated credentials
        const encryptedConfig = JSON.stringify(existingCredentials, null, 2);
        await fs.writeFile('.env', encryptedConfig);

        console.log('\nCredentials encrypted and saved!');
        console.log(`Total number of stored credentials: ${existingCredentials.length}`);
        console.log('IMPORTANT: Keep your .key file secure and backup both .env and .key files');
        
    } catch (error) {
        console.error('Error:', error.message);
    } finally {
        rl.close();
    }
}

function encrypt(text, key) {
    const iv = crypto.randomBytes(16);
    const cipher = crypto.createCipheriv('aes-256-gcm', Buffer.from(key, 'hex'), iv);
    let encrypted = cipher.update(text, 'utf8', 'hex');
    encrypted += cipher.final('hex');
    const authTag = cipher.getAuthTag();
    return {
        iv: iv.toString('hex'),
        encrypted: encrypted,
        authTag: authTag.toString('hex')
    };
}

// Run the script
encryptCredentials();
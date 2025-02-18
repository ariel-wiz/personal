import { exec } from 'child_process';
import { promisify } from 'util';
import crypto from 'crypto';

const execAsync = promisify(exec);

const KEYCHAIN_SERVICE = 'bank-scraper';
const ENCRYPTION_KEY_ACCOUNT = 'encryption-key';

class KeychainError extends Error {
    constructor(message) {
        super(message);
        this.name = 'KeychainError';
    }
}

function log(level, message, error = null) {
    console.log(JSON.stringify({
        level,
        message,
        error: error ? {
            name: error.name,
            message: error.message,
            stack: error.stack
        } : null,
        timestamp: new Date().toISOString()
    }));
}

export async function getEncryptionKey() {
    try {
        log('DEBUG', 'Attempting to retrieve encryption key from keychain');
        const { stdout } = await execAsync(
            `security find-generic-password -s "${KEYCHAIN_SERVICE}" -a "${ENCRYPTION_KEY_ACCOUNT}" -w`
        );
        const key = stdout.trim();
        log('DEBUG', `Successfully retrieved encryption key (length: ${key.length})`);
        return key;
    } catch (error) {
        if (error.stderr?.includes('could not be found')) {
            log('INFO', 'No encryption key found, generating new one');
            const newKey = crypto.randomBytes(32).toString('hex');
            await storeEncryptionKey(newKey);
            return newKey;
        }
        log('ERROR', 'Failed to retrieve encryption key', error);
        throw new KeychainError(`Failed to retrieve encryption key: ${error.message}`);
    }
}

export async function storeEncryptionKey(key) {
    try {
        log('DEBUG', 'Attempting to store encryption key');

        try {
            log('DEBUG', 'Attempting to delete existing encryption key');
            await execAsync(
                `security delete-generic-password -s "${KEYCHAIN_SERVICE}" -a "${ENCRYPTION_KEY_ACCOUNT}"`
            );
            log('DEBUG', 'Successfully deleted existing encryption key');
        } catch (error) {
            log('DEBUG', 'No existing encryption key to delete');
        }

        await execAsync(
            `security add-generic-password -s "${KEYCHAIN_SERVICE}" -a "${ENCRYPTION_KEY_ACCOUNT}" -w "${key}"`
        );
        log('DEBUG', 'Successfully stored encryption key');
    } catch (error) {
        log('ERROR', 'Failed to store encryption key', error);
        throw new KeychainError(`Failed to store encryption key: ${error.message}`);
    }
}

export async function storeCredential(accountName, credential) {
    try {
        log('DEBUG', `Storing credentials for account: ${accountName}`);
        const credentialJson = JSON.stringify(credential);
        log('DEBUG', `Credential structure: ${Object.keys(credential).join(', ')}`);

        try {
            log('DEBUG', `Attempting to delete existing credential for ${accountName}`);
            await execAsync(
                `security delete-generic-password -s "${KEYCHAIN_SERVICE}" -a "${accountName}"`
            );
            log('DEBUG', `Successfully deleted existing credential for ${accountName}`);
        } catch (error) {
            log('DEBUG', `No existing credential to delete for ${accountName}`);
        }

        const escapedJson = credentialJson.replace(/"/g, '\\"');
        await execAsync(
            `security add-generic-password -s "${KEYCHAIN_SERVICE}" -a "${accountName}" -w "${escapedJson}"`
        );
        log('DEBUG', `Successfully stored credential for ${accountName}`);
    } catch (error) {
        log('ERROR', `Failed to store credential for ${accountName}`, error);
        throw new KeychainError(`Failed to store credential: ${error.message}`);
    }
}

export async function getAllCredentials() {
    try {
        log('INFO', 'Starting to retrieve all credentials from keychain');

        log('DEBUG', 'Executing keychain dump command');
        const { stdout } = await execAsync(
            `security dump-keychain | grep -A 4 "\"${KEYCHAIN_SERVICE}\""`
        );
        log('DEBUG', `Found ${stdout.split('\n').length} lines in keychain dump`);

        const credentials = [];
        const lines = stdout.split('\n');

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i];
            if (line.includes(`"acct"<blob>=`)) {
                const accountName = line.split('"')[3];
                log('DEBUG', `Found account in keychain: ${accountName}`);

                if (accountName !== ENCRYPTION_KEY_ACCOUNT) {
                    try {
                        log('DEBUG', `Retrieving credential data for ${accountName}`);
                        const { stdout: credentialJson } = await execAsync(
                            `security find-generic-password -s "${KEYCHAIN_SERVICE}" -a "${accountName}" -w`
                        );

                        const trimmedJson = credentialJson.trim();
                        log('DEBUG', `Retrieved raw credential data length: ${trimmedJson.length}`);

                        const parsedCred = JSON.parse(trimmedJson);
                        log('DEBUG', `Successfully parsed credential for ${accountName}`);
                        log('DEBUG', `Credential structure: ${Object.keys(parsedCred).join(', ')}`);

                        if (parsedCred && typeof parsedCred === 'object') {
                            credentials.push(parsedCred);
                            log('DEBUG', `Added credential for ${accountName} to list`);
                        }
                    } catch (error) {
                        log('ERROR', `Failed to retrieve/parse credential for ${accountName}`, error);
                    }
                }
            }
        }

        log('INFO', `Successfully retrieved ${credentials.length} credentials`);
        return credentials;
    } catch (error) {
        log('ERROR', 'Failed to retrieve credentials', error);
        throw new KeychainError(`Failed to retrieve credentials: ${error.message}`);
    }
}

export function encrypt(text, key) {
    try {
        log('DEBUG', 'Starting encryption process');
        const iv = crypto.randomBytes(16);
        const cipher = crypto.createCipheriv('aes-256-gcm', Buffer.from(key, 'hex'), iv);
        let encrypted = cipher.update(text, 'utf8', 'hex');
        encrypted += cipher.final('hex');
        const authTag = cipher.getAuthTag();

        const result = {
            iv: iv.toString('hex'),
            encrypted: encrypted,
            authTag: authTag.toString('hex')
        };

        log('DEBUG', 'Encryption successful', {
            ivLength: result.iv.length,
            encryptedLength: result.encrypted.length,
            authTagLength: result.authTag.length
        });

        return result;
    } catch (error) {
        log('ERROR', 'Encryption failed', error);
        throw error;
    }
}

export function decrypt(encrypted, key, iv, authTag) {
    try {
        log('DEBUG', 'Starting decryption process');
        log('DEBUG', 'Decryption parameters', {
            encryptedLength: encrypted.length,
            keyLength: key.length,
            ivLength: iv.length,
            authTagLength: authTag.length
        });

        const decipher = crypto.createDecipheriv('aes-256-gcm', Buffer.from(key, 'hex'), Buffer.from(iv, 'hex'));
        decipher.setAuthTag(Buffer.from(authTag, 'hex'));
        let decrypted = decipher.update(encrypted, 'hex', 'utf8');
        decrypted += decipher.final('utf8');

        log('DEBUG', 'Decryption successful');
        return decrypted;
    } catch (error) {
        log('ERROR', 'Decryption failed', error);
        throw new KeychainError('Decryption failed');
    }
}
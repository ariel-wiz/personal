const { app, BrowserWindow } = require('electron');
const crypto = require('crypto');
const path = require('path');
const keytar = require('keytar');
const fs = require('fs');

const ALGORITHM = 'aes-256-ctr';
const SERVICE_NAME = 'Caspion';

async function getSalt() {
  return keytar.getPassword(SERVICE_NAME, 'crypto');
}

async function decrypt(text) {
  try {
    const salt = await getSalt();
    if (!salt) {
      throw new Error('No encryption key found in keyring');
    }

    // Use exact same crypto implementation as Caspion
    const decipher = crypto.createDecipher(ALGORITHM, salt);
    const decrypted = decipher.update(text, 'hex', 'utf8');
    return decrypted + decipher.final('utf8');
  } catch (e) {
    if (!text) {
      console.info('Failed to decrypt an empty string');
      return null;
    }
    console.error('Failed to decrypt', e);
    throw e;
  }
}

function getUserDataPath() {
  if (process.platform === 'darwin') {
    return path.join(app.getPath('home'), 'Library', 'Application Support', 'Caspion');
  } else if (process.platform === 'win32') {
    return path.join(process.env.APPDATA, 'Caspion');
  } else {
    return path.join(app.getPath('home'), '.config', 'Caspion');
  }
}

async function decryptConfig() {
  try {
    const configPath = path.join(getUserDataPath(), 'config.encrypt');
    console.log('Reading config from:', configPath);

    const encryptedData = fs.readFileSync(configPath, 'utf8');
    console.log('Successfully read encrypted config file');

    const decryptedData = await decrypt(encryptedData.trim());
    const config = JSON.parse(decryptedData);

    console.log('\nStored Bank Credentials:\n');
    if (config?.scraping?.accountsToScrape) {
      for (const account of config.scraping.accountsToScrape) {
        console.log(`Bank: ${account.name} (${account.key})`);
        console.log('Credentials:');
        for (const [field, value] of Object.entries(account.loginFields)) {
          console.log(`  ${field}: ${value}`);
        }
        console.log('Active:', account.active !== false);
        console.log('-'.repeat(40));
      }
    }
  } catch (error) {
    console.error('Failed to decrypt configuration:', error);
  }
  app.quit();
}

// Start the app
app.whenReady().then(decryptConfig);

// Handle window close
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
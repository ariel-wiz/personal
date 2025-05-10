#!/usr/bin/env python3
import subprocess
import json
import logging
import sys
import os
import re
from collections import defaultdict
from pathlib import Path
from datetime import datetime, date
from typing import Dict, Any, List, Tuple, Optional, Union

from expense.expense_constants import BANK_SCRAPER_NODE_SCRIPT_PATH, BANK_SCRAPER_DIRECTORY, \
    BANK_SCRAPER_OUTPUT_DIR, \
    BANK_SCRAPER_OUTPUT_FILE_PATH, CREATE_EXPENSE_FILE_IF_ALREADY_MODIFIED_TODAY, \
    BANK_SCRAPER_RETRIES
from logger import logger


class ScraperError(Exception):
    pass


def check_node_installation():
    """Check if Node.js is installed and get its version"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.debug(f"Node.js version: {result.stdout.strip()}")

            # Try multiple approaches to get the israeli-bank-scrapers version
            version = "unknown"

            # Method 1: Use npm list with --json flag for more reliable parsing
            npm_json_result = subprocess.run(
                ['npm', 'list', 'israeli-bank-scrapers', '--json', '--depth=0'],
                cwd=BANK_SCRAPER_DIRECTORY,
                capture_output=True, text=True
            )

            if npm_json_result.returncode == 0:
                try:
                    npm_data = json.loads(npm_json_result.stdout)
                    if (npm_data.get('dependencies') and
                            npm_data['dependencies'].get('israeli-bank-scrapers') and
                            npm_data['dependencies']['israeli-bank-scrapers'].get('version')):
                        version = npm_data['dependencies']['israeli-bank-scrapers']['version']
                        logger.debug(f"Found version from npm list --json: {version}")
                except json.JSONDecodeError:
                    logger.debug("Could not parse JSON output from npm list")

            # Method 2: If Method 1 fails, try traditional npm list with string parsing
            if version == "unknown":
                npm_result = subprocess.run(
                    ['npm', 'list', 'israeli-bank-scrapers'],
                    cwd=BANK_SCRAPER_DIRECTORY,
                    capture_output=True, text=True
                )

                if npm_result.returncode == 0:
                    import re
                    match = re.search(r'israeli-bank-scrapers@([\d\.]+)', npm_result.stdout)
                    if match:
                        version = match.group(1)
                        logger.debug(f"Found version from npm list regex: {version}")

            # Method 3: If Methods 1 and 2 fail, try npm view
            if version == "unknown":
                npm_view_result = subprocess.run(
                    ['npm', 'view', 'israeli-bank-scrapers', 'version'],
                    cwd=BANK_SCRAPER_DIRECTORY,
                    capture_output=True, text=True
                )

                if npm_view_result.returncode == 0 and npm_view_result.stdout.strip():
                    version = npm_view_result.stdout.strip()
                    logger.debug(f"Found version from npm view: {version}")

            # Method 4: Check if the package is installed globally
            if version == "unknown":
                npm_global_result = subprocess.run(
                    ['npm', 'list', '-g', 'israeli-bank-scrapers'],
                    capture_output=True, text=True
                )

                if npm_global_result.returncode == 0:
                    import re
                    match = re.search(r'israeli-bank-scrapers@([\d\.]+)', npm_global_result.stdout)
                    if match:
                        version = match.group(1)
                        logger.debug(f"Found version from global npm list: {version}")

            logger.debug(f"israeli-bank-scrapers version: {version}")
            return True
        else:
            logger.error("Node.js check failed")
            return False
    except Exception as e:
        logger.error(f"Error checking Node.js installation: {e}")
        return False


def verify_script_paths():
    """Verify all required script paths exist"""
    logger.debug("Verifying script paths...")
    paths = {
        "Node Script": BANK_SCRAPER_NODE_SCRIPT_PATH,
        "Output Directory": BANK_SCRAPER_OUTPUT_DIR,
        "Scraper Directory": BANK_SCRAPER_DIRECTORY
    }

    for name, path in paths.items():
        exists = os.path.exists(path)
        logger.debug(f"{name} path ({path}) exists: {exists}")
        if not exists and name != "Output Directory":  # Output dir will be created if missing
            raise ScraperError(f"{name} not found at: {path}")


def is_file_modified_today(file_path: str) -> bool:
    try:
        logger.debug(f"Checking if file was modified today: {file_path}")
        mod_time = os.path.getmtime(file_path)
        mod_date = datetime.fromtimestamp(mod_time).date()
        is_today = mod_date == date.today()
        logger.debug(f"File modification date: {mod_date}, is today: {is_today}")
        return is_today
    except FileNotFoundError:
        logger.debug(f"File not found: {file_path}")
        return False
    except Exception as e:
        logger.error(f"Error checking file modification time: {e}")
        return False


def find_credential_files(directory: str) -> List[Path]:
    try:
        logger.debug("Checking keychain for credentials")
        check_keychain = subprocess.run(
            ['security', 'find-generic-password', '-s', 'bank-scraper'],
            capture_output=True,
            text=True
        )

        logger.debug(f"Keychain check return code: {check_keychain.returncode}")
        logger.debug(f"Keychain check stdout: {check_keychain.stdout}")
        logger.debug(f"Keychain check stderr: {check_keychain.stderr}")

        if check_keychain.returncode == 0:
            logger.info("Found credentials in keychain")
            return ['keychain']

        logger.debug(f"Falling back to file-based credentials in directory: {directory}")
        cred_dir = Path(directory)
        if not cred_dir.exists():
            raise ScraperError(f"Credentials directory not found: {directory}")

        env_files = list(cred_dir.glob("**/*.env"))
        logger.debug(f"Found {len(env_files)} .env files: {[str(f) for f in env_files]}")

        return env_files
    except Exception as e:
        logger.error(f"Error searching for credentials: {e}", exc_info=True)
        raise ScraperError(f"Error searching for credentials: {e}")


def parse_scraper_output(line: str) -> Dict:
    """Parse and structure scraper output line"""
    try:
        log_entry = json.loads(line)
        return {
            'level': log_entry.get('level', 'INFO').upper(),
            'message': log_entry.get('message', ''),
            'error': log_entry.get('error'),
            'data': log_entry.get('data'),
            'timestamp': log_entry.get('timestamp')
        }
    except json.JSONDecodeError:
        return {'level': 'INFO', 'message': line}


def get_failed_credentials(stdout: str, stderr: str) -> List[Dict[str, str]]:
    """
    Extract failed account information from scraper output.
    Prioritizes structured JSON error objects that contain both companyId and username.

    Args:
        stdout: Standard output from scraper process
        stderr: Standard error from scraper process

    Returns:
        List of dictionaries containing failed account information
    """
    logger.debug("Starting to extract failed credentials from scraper output")

    # Combine stdout and stderr
    all_output = stdout.splitlines() + stderr.splitlines()
    failed_accounts = []
    processed_accounts = set()  # Keep track of processed accounts by company_id:username

    # First pass: look for structured JSON error objects (highest priority)
    for line in all_output:
        try:
            # Parse JSON data
            json_data = json.loads(line)

            # Check if this is an error object with the fields we need
            if (isinstance(json_data, dict) and
                    not json_data.get('success', True) and
                    json_data.get('companyId')):

                company_id = json_data.get('companyId', '')
                username = json_data.get('username', '')
                error_message = json_data.get('errorMessage', 'Unknown error')

                # Create a unique key to avoid duplicates
                account_key = f"{company_id}:{username}"

                if account_key not in processed_accounts:
                    # Create the account_id (either company_id-username or just company_id)
                    account_id = f"{company_id}-{username}" if username else company_id

                    failed_accounts.append({
                        'company_id': company_id,
                        'username': username,
                        'specific_id': account_id,
                        'error': error_message
                    })

                    processed_accounts.add(account_key)
                    logger.debug(f"Added failed account from JSON: {account_id}")
        except json.JSONDecodeError:
            # Not JSON, continue to next line
            pass

    # Only if we didn't find any structured error objects, try parsing from log lines
    if not failed_accounts:
        for line in all_output:
            # Check for log line pattern like "Failed scraping X - Error details: Y"
            match = re.search(
                r'Failed scraping ([^\s-]+(?:-[^\s]+)?) - (Error details: )?(.+?)(?:\(Time:|$)',
                line)
            if match:
                account_id = match.group(1).strip()
                error_message = match.group(3).strip()

                # Skip obviously invalid account IDs
                if ('{' in account_id or '}' in account_id or
                        '"' in account_id or ':' in account_id):
                    continue

                # Split account_id into company_id and username if possible
                if '-' in account_id:
                    company_id, username = account_id.split('-', 1)
                else:
                    company_id, username = account_id, ''

                # Create unique key
                account_key = f"{company_id}:{username}"

                if account_key not in processed_accounts:
                    failed_accounts.append({
                        'company_id': company_id,
                        'username': username,
                        'specific_id': account_id,
                        'error': error_message
                    })

                    processed_accounts.add(account_key)
                    logger.debug(f"Added failed account from log: {account_id}")

    # Log the discovered failed accounts
    for account in failed_accounts:
        if account.get('username'):
            logger.info(
                f"Failed account: {account['company_id']} (username: {account['username']}) - Error: {account.get('error', 'Unknown error')}")
        else:
            logger.info(
                f"Failed account: {account['company_id']} - Error: {account.get('error', 'Unknown error')}")

    return failed_accounts


def run_scraper_for_specific_accounts(accounts: List[str], output_path: str, timeout: int = 300) -> \
Tuple[bool, List[Dict[str, str]]]:
    """
    Run the bank scraper for a specific list of accounts only.

    Args:
        accounts: List of account identifiers (company_id or company_id-username) to scrape
        output_path: Path where to save the transaction data
        timeout: Timeout in seconds for the scraper process

    Returns:
        Tuple of (success_status, list_of_failed_accounts)
    """
    if not accounts:
        logger.warning("No accounts specified for targeted scraping")
        return False, []

    logger.info(f"Running scraper for specific accounts: {', '.join(accounts)}")

    # Get node executable
    node_exec = "/opt/homebrew/bin/node"
    if not os.path.exists(node_exec):
        node_exec = "/usr/local/bin/node"
        if not os.path.exists(node_exec):
            node_exec = "node"

    # Construct command
    command = [
        node_exec,
        BANK_SCRAPER_NODE_SCRIPT_PATH,
        output_path
    ]
    command.extend(accounts)

    logger.debug(f"Executing command with {timeout}s timeout: {' '.join(command)}")

    try:
        # Run with timeout
        completed_process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        # Parse output for failed accounts - use the new simpler function
        failed_accounts = get_failed_credentials(
            completed_process.stdout,
            completed_process.stderr
        )

        # Check transactions
        transactions_found = False
        try:
            if os.path.exists(output_path):
                with open(output_path, 'r') as f:
                    data = json.load(f)
                    if data:
                        transactions_found = True
                        logger.info(f"Found {len(data)} transactions in output file")
        except Exception as e:
            logger.error(f"Error reading output file: {e}")

        if not failed_accounts and transactions_found:
            return True, []
        else:
            logger.info(f"{len(failed_accounts)} accounts still failing after retry")
            return False, failed_accounts

    except subprocess.TimeoutExpired:
        logger.error(f"Retry scraper process timed out after {timeout} seconds")
        # Create failed account entries for each account due to timeout
        failed = []
        for account in accounts:
            parts = account.split('-', 1)
            company_id = parts[0]
            username = parts[1] if len(parts) > 1 else ''
            failed.append({
                'company_id': company_id,
                'username': username,
                'specific_id': account,
                'error': f"Timeout after {timeout} seconds"
            })
        return False, failed
    except Exception as e:
        logger.error(f"Error in retry scraper: {e}", exc_info=True)
        return False, [{'company_id': 'retry_error', 'error': str(e)}]


def retry_failed_accounts(failed_accounts: List[Dict[str, str]], output_path: str) -> List[
    Dict[str, str]]:
    """
    Retry scraping for failed accounts only.
    Simplified version that uses the specific_id directly from failed accounts.

    Args:
        failed_accounts: List of dictionaries containing failed account information
        output_path: Path to write transaction data

    Returns:
        List of accounts that still failed after retries
    """
    if not failed_accounts or BANK_SCRAPER_RETRIES <= 0:
        return failed_accounts

    # Extract specific account identifiers for retry
    specific_ids = []
    for account in failed_accounts:
        if 'specific_id' in account and account['specific_id']:
            account_id = account['specific_id']
            specific_ids.append(account_id)
            if ('{' not in account_id and '}' not in account_id and
                '"' not in account_id and ':' not in account_id):
                specific_ids.append(account_id)
                logger.debug(f"Using specific_id for retry: {account_id}")
        else:
            # Fallback if specific_id not available
            if 'company_id' in account and 'username' in account and account['username']:
                specific_id = f"{account['company_id']}-{account['username']}"
                specific_ids.append(specific_id)
                logger.debug(f"Created specific_id from company_id and username: {specific_id}")
            elif 'company_id' in account:
                specific_ids.append(account['company_id'])
                logger.debug(f"Using company_id only for retry: {account['company_id']}")

    # Remove duplicates
    specific_ids = list(set(specific_ids))

    if not specific_ids:
        logger.info("No specific accounts to retry")
        return failed_accounts

    logger.info(f"Will retry {len(specific_ids)} failed accounts: {', '.join(specific_ids)}")

    # Perform retries
    remaining_failed = specific_ids.copy()
    final_failed_accounts = []

    for retry_num in range(BANK_SCRAPER_RETRIES):
        if not remaining_failed:
            logger.info("All retried accounts succeeded!")
            break

        logger.info(
            f"Retry attempt {retry_num + 1}/{BANK_SCRAPER_RETRIES} for accounts: {', '.join(remaining_failed)}")
        timeout = 300 + (retry_num * 60)  # Increase timeout by 1 minute per retry

        # Run scraper for just the failed accounts
        success, retry_results = run_scraper_for_specific_accounts(remaining_failed, output_path,
                                                                   timeout)

        # Update list of accounts to retry - just use specific_id directly
        remaining_failed = [account['specific_id'] for account in retry_results]

        # For the final retry, keep track of failing accounts
        if retry_num == BANK_SCRAPER_RETRIES - 1 or not remaining_failed:
            final_failed_accounts = retry_results
            for account in final_failed_accounts:
                logger.debug(f"Still failing after all retries: {account['specific_id']}")

        logger.info(f"After retry {retry_num + 1}: {len(remaining_failed)} accounts still failing")

    return final_failed_accounts


def run_scraper(env_file: Path, output_path: str, timeout: int = 300) -> Tuple[
    Dict[str, Any], bool, List[Dict[str, str]]]:
    """
    Run the bank scraper with simplified error handling.

    Args:
        env_file: Path to credentials file or 'keychain'
        output_path: Path to save transaction data
        timeout: Timeout in seconds

    Returns:
        Tuple of (transaction_data, was_skipped, failed_accounts)
    """
    logger.debug(f"Starting scraper run with env_file: {env_file}, output_path: {output_path}")

    # Check if output already exists and is recent
    if os.path.exists(output_path):
        logger.debug(f"Output file exists: {output_path}")
        if not CREATE_EXPENSE_FILE_IF_ALREADY_MODIFIED_TODAY and is_file_modified_today(
                output_path):
            logger.info("Output file was already modified today")
            try:
                with open(output_path, 'r') as f:
                    data = json.load(f)
                logger.debug(f"Successfully loaded existing data with {len(data)} records")
                return data, True, []
            except Exception as e:
                logger.error(f"Error reading existing output file: {e}", exc_info=True)

    # Construct command
    logger.debug("Constructing scraper command")
    if env_file == 'keychain':
        node_command = [
            "/opt/homebrew/bin/node",
            BANK_SCRAPER_NODE_SCRIPT_PATH,
            output_path
        ]
    else:
        node_command = [
            "/opt/homebrew/bin/node",
            BANK_SCRAPER_NODE_SCRIPT_PATH,
            str(env_file),
            output_path,
            os.path.join(BANK_SCRAPER_DIRECTORY, ".key")
        ]

    logger.info(f"Executing command: {' '.join(node_command)}")

    try:
        # Run with timeout
        completed_process = subprocess.run(
            node_command,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        logger.debug(f"Scraper process completed with return code: {completed_process.returncode}")

        # Process output and extract error information
        has_error = False

        for line in completed_process.stdout.splitlines():
            try:
                # Try to parse as JSON
                try:
                    log_entry = json.loads(line)
                    # Log based on level
                    if 'level' in log_entry:
                        level = log_entry['level'].lower()
                        message = log_entry.get('message', '')
                        getattr(logger, level, logger.info)(message)

                        # Check for errors
                        if level == 'error' or (log_entry.get('error') is not None):
                            has_error = True
                except json.JSONDecodeError:
                    # Not JSON, just log as-is
                    logger.info(line)
            except Exception as parse_error:
                logger.warning(f"Error parsing output line: {parse_error}. Line: {line}")

        # Log any stderr
        if completed_process.stderr and "punycode" not in completed_process.stderr:
            logger.error(f"stderr output: {completed_process.stderr}")
            has_error = True

        # Get failed credentials using the simplified function
        failed_credentials = get_failed_credentials(completed_process.stdout,
                                                    completed_process.stderr)

        if failed_credentials:
            logger.info(f"Detected {len(failed_credentials)} failed accounts:")
            for account in failed_credentials:
                if account.get('username'):
                    logger.info(
                        f"  - Company ID: {account['company_id']}, Username: {account['username']}, Error: {account.get('error', 'Unknown error')}")
                else:
                    logger.info(
                        f"  - Company ID: {account['company_id']}, Error: {account.get('error', 'Unknown error')}")

            # Handle retries for failed accounts
            if BANK_SCRAPER_RETRIES > 0:
                retried_failed_credentials = retry_failed_accounts(failed_credentials, output_path)
                # Replace the original failed credentials with the ones that still failed after retries
                failed_credentials = retried_failed_credentials

        # Check for transaction data
        if os.path.exists(output_path):
            with open(output_path, 'r') as f:
                try:
                    data = json.load(f)
                    if data:
                        logger.debug(
                            f"Successfully loaded {len(data)} transactions from output file")
                        return data, False, failed_credentials
                except json.JSONDecodeError:
                    has_error = True
                    logger.error("Output file exists but contains invalid JSON")

        if has_error or completed_process.returncode != 0:
            raise ScraperError(f"Scraper failed with code {completed_process.returncode}")

        raise ScraperError("No transactions found")

    except subprocess.TimeoutExpired:
        logger.error(f"Scraper process timed out after {timeout} seconds")
        return {}, False, [{'company_id': 'all', 'specific_id': 'all',
                            'error': f"Timeout after {timeout} seconds"}]
    except Exception as e:
        logger.error(f"Error running scraper: {e}", exc_info=True)
        return {}, False, [{'company_id': 'all', 'specific_id': 'all', 'error': str(e)}]

def main():
    try:
        logger.info("Starting bank scraper main process")

        # Verify environment
        check_node_installation()
        verify_script_paths()

        os.makedirs(BANK_SCRAPER_OUTPUT_DIR, exist_ok=True)

        env_files = find_credential_files(BANK_SCRAPER_DIRECTORY)

        results, errors, skipped = {}, [], []
        all_failed_accounts = []

        for env_file in env_files:
            source_name = 'keychain' if env_file == 'keychain' else env_file.name
            try:
                logger.debug(f"Processing credential source: {source_name}")
                # Set a timeout for each run_scraper call
                try:
                    file_results, was_skipped, failed_accounts = run_scraper(env_file,
                                                                             BANK_SCRAPER_OUTPUT_FILE_PATH,
                                                                             timeout=300)
                    all_failed_accounts.extend(failed_accounts)

                    if was_skipped:
                        skipped.append(source_name)
                        logger.info(f"Skipped {source_name} - already processed today")
                    else:
                        results[source_name] = file_results
                        logger.debug(f"Successfully processed {source_name}")
                except TimeoutError:
                    logger.error(f"Scraper process for {source_name} timed out after 300 seconds")
                    errors.append((source_name, "Process timed out"))
                    all_failed_accounts.append({
                        'company_id': source_name,
                        'error': "Process timed out after 300 seconds"
                    })
                    continue

            except ScraperError as e:
                logger.error(f"Failed to process {source_name}: {e}")
                errors.append((source_name, str(e)))
                all_failed_accounts.append({
                    'company_id': source_name,
                    'error': str(e)
                })
                continue

        if errors:
            logger.info("\nErrors:")
            for filename, error in errors:
                logger.info(f"{filename}: {error}")

        if skipped:
            logger.info("\nSkipped sources:")
            for source in skipped:
                logger.info(source)

        if all_failed_accounts:
            logger.info("\nFailed accounts:")
            for account in all_failed_accounts:
                company_id = account.get('company_id', 'Unknown')
                username = account.get('username', '')
                error = account.get('error', 'Unknown error')

                account_info = f"{company_id}"
                if username:
                    account_info += f" (username: {username})"

                logger.info(f"{account_info} - Error: {error}")

        return len(errors) == 0
    except Exception as e:
        logger.error(f"Unexpected error in main process: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    # Check if specific accounts were passed as arguments
    accounts_to_scrape = sys.argv[1:] if len(sys.argv) > 1 else None

    if accounts_to_scrape:
        success, failed_accounts = run_scraper_for_specific_accounts(accounts_to_scrape,
                                                                     BANK_SCRAPER_OUTPUT_FILE_PATH)
        if failed_accounts:
            print("Failed accounts:")
            for account in failed_accounts:
                print(f"  - {account['company_id']}: {account.get('error', 'Unknown error')}")
        sys.exit(0 if success else 1)
    else:
        # Run normal flow
        success = main()
        sys.exit(0 if success else 1)

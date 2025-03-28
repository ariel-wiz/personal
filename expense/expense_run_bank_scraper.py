#!/usr/bin/env python3
import subprocess
import json
import logging
import sys
import os
from pathlib import Path
from datetime import datetime, date
from typing import Dict, Any, List, Tuple

from expense.expense_constants import BANK_SCRAPER_NODE_SCRIPT_PATH, BANK_SCRAPER_DIRECTORY, BANK_SCRAPER_OUTPUT_DIR, \
    BANK_SCRAPER_OUTPUT_FILE_PATH, CREATE_EXPENSE_FILE_IF_ALREADY_MODIFIED_TODAY
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


def run_scraper(env_file: Path, output_path: str, timeout: int = 300) -> Tuple[Dict[str, Any], bool]:
    logger.debug(f"Starting scraper run with env_file: {env_file}, output_path: {output_path}")

    if os.path.exists(output_path):
        logger.debug(f"Output file exists: {output_path}")
        if not CREATE_EXPENSE_FILE_IF_ALREADY_MODIFIED_TODAY and is_file_modified_today(output_path):
            logger.info("Output file was already modified today")
            try:
                with open(output_path, 'r') as f:
                    data = json.load(f)
                logger.debug(f"Successfully loaded existing data with {len(data)} records")
                return data, True
            except Exception as e:
                logger.error(f"Error reading existing output file: {e}", exc_info=True)

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
            timeout=timeout  # Add explicit timeout
        )

        logger.debug(f"Scraper process completed with return code: {completed_process.returncode}")

        has_error = False
        error_details = ""

        for line in completed_process.stdout.splitlines():
            try:
                log_entry = parse_scraper_output(line)

                if log_entry['error']:
                    error_message = log_entry['error'].get('message', 'Unknown error')
                    error_details += f"{log_entry['message']}: {error_message}\n"
                    logger.error(f"{log_entry['message']}: {error_message}")

                    if 'stack' in log_entry['error']:
                        logger.debug(f"Stack trace: {log_entry['error']['stack']}")

                    has_error = True
                else:
                    getattr(logger, log_entry['level'].lower(), logger.info)(log_entry['message'])

                if log_entry.get('data'):
                    logger.debug(f"Additional data: {log_entry['data']}")
            except Exception as parse_error:
                logger.warning(f"Error parsing output line: {parse_error}. Line: {line}")

        if completed_process.stderr and "punycode" not in completed_process.stderr:
            logger.error(f"stderr output: {completed_process.stderr}")
            has_error = True

        if os.path.exists(output_path):
            with open(output_path, 'r') as f:
                try:
                    data = json.load(f)
                    if data:
                        logger.debug(f"Successfully loaded {len(data)} transactions from output file")
                        return data, False
                except json.JSONDecodeError:
                    has_error = True
                    logger.error("Output file exists but contains invalid JSON")

        if has_error or completed_process.returncode != 0:
            raise ScraperError(f"Scraper failed with code {completed_process.returncode}")

        raise ScraperError("No transactions found")

    except subprocess.TimeoutExpired:
        logger.error(f"Scraper process timed out after {timeout} seconds")
        raise TimeoutError(f"Scraper process timed out after {timeout} seconds")
    except Exception as e:
        logger.error(f"Error running scraper: {e}", exc_info=True)
        raise ScraperError(f"Error running scraper: {e}")

def main():
    try:
        logger.info("Starting bank scraper main process")

        # Verify environment
        check_node_installation()
        verify_script_paths()

        os.makedirs(BANK_SCRAPER_OUTPUT_DIR, exist_ok=True)

        env_files = find_credential_files(BANK_SCRAPER_DIRECTORY)

        results, errors, skipped = {}, [], []

        for env_file in env_files:
            source_name = 'keychain' if env_file == 'keychain' else env_file.name
            try:
                logger.debug(f"Processing credential source: {source_name}")
                # Set a timeout for each run_scraper call
                try:
                    file_results, was_skipped = run_scraper(env_file, BANK_SCRAPER_OUTPUT_FILE_PATH, timeout=300)

                    if was_skipped:
                        skipped.append(source_name)
                        logger.info(f"Skipped {source_name} - already processed today")
                    else:
                        results[source_name] = file_results
                        logger.debug(f"Successfully processed {source_name}")
                except TimeoutError:
                    logger.error(f"Scraper process for {source_name} timed out after 300 seconds")
                    errors.append((source_name, "Process timed out"))
                    continue

            except ScraperError as e:
                logger.error(f"Failed to process {source_name}: {e}")
                errors.append((source_name, str(e)))
                continue

        if errors:
            logger.info("\nErrors:")
            for filename, error in errors:
                logger.info(f"{filename}: {error}")

        if skipped:
            logger.info("\nSkipped sources:")
            for source in skipped:
                logger.info(source)

        return len(errors) == 0
    except Exception as e:
        logger.error(f"Unexpected error in main process: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
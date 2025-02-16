#!/usr/bin/env python3
import subprocess
import json
import logging
import sys
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple
from datetime import datetime, date

from expense.expense_constants import BANK_SCRAPER_NODE_SCRIPT_PATH, BANK_SCRAPER_DIRECTORY, BANK_SCRAPER_OUTPUT_DIR, \
    BANK_SCRAPER_OUTPUT_FILE_PATH

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ScraperError(Exception):
    """Custom exception for scraper errors"""
    pass


def is_file_modified_today(file_path: str) -> bool:
    try:
        mod_time = os.path.getmtime(file_path)
        mod_date = datetime.fromtimestamp(mod_time).date()
        return mod_date == date.today()
    except FileNotFoundError:
        return False
    except Exception as e:
        logger.error(f"Error checking file modification time: {e}")
        return False


def find_credential_files(directory: str) -> List[Path]:
    try:
        cred_dir = Path(directory)
        if not cred_dir.exists():
            raise ScraperError(f"Credentials directory not found: {directory}")
        env_files = list(cred_dir.glob("**/*.env"))
        if not env_files:
            logger.warning(f"No .env files found in {directory}")
        else:
            logger.info(f"Found {len(env_files)} credential files")
        return env_files
    except Exception as e:
        raise ScraperError(f"Error searching for credential files: {e}")


def run_scraper(env_file: Path, output_path: str, CREATE_IF_MODIFIED_TODAY=None) -> Tuple[Dict[str, Any], bool]:
    if not CREATE_IF_MODIFIED_TODAY and os.path.exists(output_path) and is_file_modified_today(output_path):
        logger.info(f"Output file {output_path} was already created today. Skipping scraping.")
        try:
            with open(output_path, 'r') as f:
                return json.load(f), True
        except Exception as e:
            logger.error(f"Error reading existing output file: {e}")

    if not os.path.exists(BANK_SCRAPER_NODE_SCRIPT_PATH):
        raise ScraperError(f"Scraper script not found at {BANK_SCRAPER_NODE_SCRIPT_PATH}")

    try:
        logger.info(f"Processing {env_file.name}")
        node_command = [
            "node", str(BANK_SCRAPER_NODE_SCRIPT_PATH), str(env_file), str(output_path),
            os.path.join(BANK_SCRAPER_DIRECTORY, ".key")
        ]
        logger.info(f"Executing command: {' '.join(node_command)}")
        completed_process = subprocess.run(
            node_command, capture_output=True, text=True, timeout=300
        )
        for line in completed_process.stdout.splitlines():
            try:
                log_entry = json.loads(line)
                level = log_entry.get('level', 'INFO').upper()
                message = log_entry.get('message', '')
                error = log_entry.get('error')
                if error:
                    logger.error(f"{message}: {error.get('message', 'Unknown error')}")
                    if 'stack' in error:
                        logger.debug(f"Stack trace: {error['stack']}")
                else:
                    getattr(logger, level.lower(), logger.info)(message)
            except json.JSONDecodeError:
                logger.info(line)
        if completed_process.stderr and "punycode" not in completed_process.stderr:
            logger.error(f"stderr output: {completed_process.stderr}")
        if completed_process.returncode == 0 and os.path.exists(output_path):
            with open(output_path, 'r') as f:
                return json.load(f), False
        else:
            raise ScraperError(f"Scraper failed with code {completed_process.returncode}")
    except subprocess.TimeoutExpired:
        raise ScraperError("Scraper process timed out")
    except Exception as e:
        raise ScraperError(f"Error running scraper: {e}")


def main():
    try:
        os.makedirs(BANK_SCRAPER_OUTPUT_DIR, exist_ok=True)
        env_files = find_credential_files(BANK_SCRAPER_DIRECTORY)
        results, errors, skipped = {}, [], []
        for env_file in env_files:
            try:
                file_results, was_skipped = run_scraper(env_file, BANK_SCRAPER_OUTPUT_FILE_PATH)
                if was_skipped:
                    skipped.append(env_file.name)
                else:
                    results[env_file.name] = file_results
                    logger.info(f"Successfully processed {env_file.name}")
            except ScraperError as e:
                logger.error(f"Failed to process {env_file.name}: {e}")
                errors.append((env_file.name, str(e)))
                continue
        logger.info(f"\n----------------\nScraping Summary:\n----------------\n"
                    f"Successful: {len(results)}\nFailed: {len(errors)}\nSkipped: {len(skipped)}\n----------------")
        if errors:
            logger.info("\nErrors:")
            for filename, error in errors:
                logger.info(f"{filename}: {error}")
        return len(errors) == 0
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

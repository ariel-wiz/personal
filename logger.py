import logging

import logging
from typing import List
import atexit


class CollectLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.log_records: List[dict] = []
        # Register the collect_logs method to run at program exit
        atexit.register(self.collect_logs)

    def emit(self, record: logging.LogRecord):
        """Store the log record"""
        log_entry = {
            'timestamp': self.formatter.formatTime(record),
            'level': record.levelname,
            'message': self.format(record),
            'function': record.funcName
        }
        self.log_records.append(log_entry)

    def collect_logs(self):
        """Get all collected logs - called automatically at exit"""
        return self.log_records

    def get_message_logs(self):
        """Get only the message logs"""
        return [log['message'] for log in self.log_records]

    def clear_message_logs(self):
        """Clear the message logs"""
        self.log_records = []

    def get_message_logs_and_clear(self):
        """Get only the message logs"""
        log_messages = [log['message'] for log in self.log_records]
        self.clear_message_logs()
        return log_messages



def setup_logger():
    # Create a custom logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Create a console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # Create a custom formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(funcName)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Set the formatter for the console handler
    ch.setFormatter(formatter)

    # Add the console handler to the logger
    logger.addHandler(ch)

    # Add collection handler
    collect_handler = CollectLogHandler()
    collect_handler.setFormatter(formatter)
    logger.addHandler(collect_handler)

    return logger, collect_handler


logger, collect_handler = setup_logger()

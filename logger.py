import logging
from typing import List, Dict
import atexit
import time
from collections import defaultdict

logger_level = logging.DEBUG
BURST_THRESHOLD = 1  # Number of similar messages to trigger summarization


class RealtimeDedupHandler(logging.Handler):
    """Handler that summarizes consecutive repeated logs in real-time"""

    def __init__(self, stream=None, consecutive_threshold=2):
        super().__init__()
        # Create an internal StreamHandler for actual output
        self.stream_handler = logging.StreamHandler(stream)
        self.consecutive_threshold = consecutive_threshold

        # State for tracking consecutive messages
        self.current_key = None
        self.buffer = []  # Buffer to store consecutive messages
        self.last_summary = None  # Track the last summary to avoid duplicates

        # Register flush at exit
        atexit.register(self.flush)

    def get_message_key(self, record):
        """Create a key to identify similar messages"""
        # Use function name and message as the key
        return f"{record.funcName}:{record.msg}"

    def emit(self, record):
        """Process the record with deduplication logic"""
        # Get key for message categorization
        key = self.get_message_key(record)

        # Handle switching to a new message type
        if self.current_key is None or key != self.current_key:
            # Output summary of previous buffer if needed
            self._flush_buffer()

            # Start a new buffer with this message
            self.current_key = key
            self.buffer = [record]

            # For the first occurrence, output normally
            self.stream_handler.setFormatter(self.formatter)
            self.stream_handler.emit(record)
        else:
            # Same message type, add to buffer
            self.buffer.append(record)

            # If below threshold, output normally
            if len(self.buffer) < self.consecutive_threshold:
                self.stream_handler.setFormatter(self.formatter)
                self.stream_handler.emit(record)

    def _flush_buffer(self):
        """Process and output a summary for the buffered messages if needed"""
        if not self.buffer:
            return

        # Only proceed if we have enough messages to summarize
        if len(self.buffer) >= self.consecutive_threshold:
            last_record = self.buffer[-1]
            count = len(self.buffer)

            # Create the summary message
            summary_msg = f"{last_record.msg} (repeated {count} times)"

            # Check if this is different from the last summary we output
            if self.last_summary != summary_msg:
                summary_record = logging.LogRecord(
                    name=last_record.name,
                    level=last_record.levelno,
                    pathname=last_record.pathname,
                    lineno=last_record.lineno,
                    msg=summary_msg,
                    args=(),
                    exc_info=None
                )
                summary_record.funcName = last_record.funcName

                self.stream_handler.setFormatter(self.formatter)
                self.stream_handler.emit(summary_record)

                # Remember this summary to avoid duplicates
                self.last_summary = summary_msg

        # Clear the buffer for the next sequence
        self.buffer = []
        self.current_key = None

    def setFormatter(self, fmt):
        """Set formatter for both this handler and the internal stream handler"""
        super().setFormatter(fmt)
        self.stream_handler.setFormatter(fmt)

    def flush(self):
        """Flush the buffer and the stream"""
        self._flush_buffer()
        self.stream_handler.flush()

    def close(self):
        """Close the handler and release resources"""
        self._flush_buffer()
        self.stream_handler.close()
        super().close()


class CollectLogHandler(logging.Handler):
    """Handler that collects logs for later retrieval"""

    def __init__(self):
        super().__init__()
        self.log_records = []

        # Register collection at exit
        atexit.register(self.collect_logs)

    def emit(self, record):
        """Store the log record for later retrieval"""
        # Format the entry
        formatted_message = self.format(record)
        message_key = self.get_message_key(record)

        log_entry = {
            'timestamp': self.formatter.formatTime(record),
            'level': record.levelname,
            'message': formatted_message,
            'function': record.funcName,
            'key': message_key,
            'time': time.time()
        }

        # Store the record
        self.log_records.append(log_entry)

    def get_message_key(self, record):
        """Create a key to identify similar messages"""
        return f"{record.funcName}:{record.msg}"

    def collect_logs(self):
        """Get all collected logs - called automatically at exit"""
        return self.log_records

    def clear_message_logs(self):
        """Clear the message logs"""
        self.log_records = []

    def get_all_message_logs_and_clear(self, get_only_info_or_error=False, deduplicated=True):
        """Get message logs and clear storage"""
        if get_only_info_or_error:
            # Filter by log level
            filtered_records = [log for log in self.log_records if
                                log['level'] in ['INFO', 'ERROR']]

            if deduplicated:
                # Group by key and count
                key_counts = defaultdict(int)
                key_to_log = {}

                for log in filtered_records:
                    key = log['key']
                    key_counts[key] += 1
                    if key not in key_to_log:
                        key_to_log[key] = log

                # Create deduplicated logs
                logs = []
                for key, count in key_counts.items():
                    message = key_to_log[key]['message']
                    if count > 1:
                        message += f" (repeated {count} times)"
                    logs.append(message)
            else:
                logs = [log['message'] for log in filtered_records]
        else:
            if deduplicated:
                # Group by key and count
                key_counts = defaultdict(int)
                key_to_log = {}

                for log in self.log_records:
                    key = log['key']
                    key_counts[key] += 1
                    if key not in key_to_log:
                        key_to_log[key] = log

                # Create deduplicated logs
                logs = []
                for key, count in key_counts.items():
                    message = key_to_log[key]['message']
                    if count > 1:
                        message += f" (repeated {count} times)"
                    logs.append(message)
            else:
                logs = [log['message'] for log in self.log_records]

        self.clear_message_logs()
        return logs


def setup_logger():
    """Set up the logger with deduplication handlers"""
    # Create a custom logger
    logger = logging.getLogger(__name__)

    # Prevent propagation to root logger to avoid duplicate logs
    logger.propagate = False

    # Clear any existing handlers
    if logger.handlers:
        logger.handlers.clear()

    logger.setLevel(logger_level)

    # Create a custom formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(funcName)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Create our realtime dedup handler for console output
    realtime_dedup = RealtimeDedupHandler(consecutive_threshold=2)
    realtime_dedup.setLevel(logger_level)
    realtime_dedup.setFormatter(formatter)

    # Add the handler to the logger
    logger.addHandler(realtime_dedup)

    # Create a separate handler just for collecting logs
    collect_handler = CollectLogHandler()
    collect_handler.setFormatter(formatter)
    logger.addHandler(collect_handler)

    return logger, collect_handler

logger, collect_handler = setup_logger()
#!/bin/bash

# Log file
LOG_FILE="/Users/ariel/Documents/cron-files/run_cron_manager.log"

# Define full paths to commands
BREW="/opt/homebrew/bin/brew"
SUPERVISORCTL="/opt/homebrew/bin/supervisorctl"
MKDIR="/bin/mkdir"

# Timestamp for logs
timestamp() {
  /bin/date "+%Y-%m-%d %H:%M:%S"
}

# Make sure log directory exists with the right permissions
$MKDIR -p "$(dirname "$LOG_FILE")"
/bin/chmod 777 "$(dirname "$LOG_FILE")"

# Try to create the log file with permissions
touch "$LOG_FILE" 2>/dev/null || true
/bin/chmod 666 "$LOG_FILE" 2>/dev/null || true

# Alternative logging that writes to a different location if main log fails
log() {
  echo "$(timestamp) - $1" >> "$LOG_FILE" 2>/dev/null
  echo "$(timestamp) - $1" >> "/tmp/cron_fallback.log" 2>/dev/null
  echo "$(timestamp) - $1"
}

log "Starting run_cron_manager script"

# Check if supervisor is running
if ! $BREW services list | grep -q "supervisor.*started"; then
  log "Supervisor is not running. Starting supervisor..."
  $BREW services start supervisor
  sleep 3  # Give supervisor time to start
fi

# Run the cron manager using supervisor
log "Running cron_manager via supervisor..."
$SUPERVISORCTL start cron_manager

# Check status
sleep 2
STATUS=$($SUPERVISORCTL status cron_manager)
log "Current status: $STATUS"

# Exit with success
log "Script completed"
exit 0
#!/bin/bash

# Log file
LOG_FILE="/Users/ariel/Documents/cron-files/run_cron_manager.log"

# Timestamp for logs
timestamp() {
  date "+%Y-%m-%d %H:%M:%S"
}

# Log function
log() {
  echo "$(timestamp) - $1" >> "$LOG_FILE"
  echo "$(timestamp) - $1"
}

# Make sure log directory exists
mkdir -p "$(dirname "$LOG_FILE")"

log "Starting run_cron_manager script"

# Check if supervisor is running
if ! brew services list | grep -q "supervisor.*started"; then
  log "Supervisor is not running. Starting supervisor..."
  brew services start supervisor
  sleep 3  # Give supervisor time to start
fi

# Run the cron manager using supervisor
log "Running cron_manager via supervisor..."
supervisorctl start cron_manager

# Check status
sleep 2
STATUS=$(supervisorctl status cron_manager)
log "Current status: $STATUS"

# Exit with success
log "Script completed"
exit 0

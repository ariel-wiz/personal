#!/bin/bash
#
# Enhanced script for running the cron manager with better error handling
# and permission management
#

# Log file paths
LOG_DIR="/Users/ariel/Documents/cron-files"
LOG_FILE="${LOG_DIR}/run_cron_manager.log"
FALLBACK_LOG="/tmp/cron_fallback.log"

# Define full paths to commands
BREW="/opt/homebrew/bin/brew"
SUPERVISORCTL="/opt/homebrew/bin/supervisorctl"
MKDIR="/bin/mkdir"
CHMOD="/bin/chmod"
TOUCH="/usr/bin/touch"
WHOAMI="/usr/bin/whoami"

# Timestamp for logs
timestamp() {
  /bin/date "+%Y-%m-%d %H:%M:%S"
}

# Enhanced logging function that tries multiple locations
log() {
  message="$(timestamp) - $1"
  echo "$message" >> "$LOG_FILE" 2>/dev/null || echo "$message" >> "$FALLBACK_LOG" 2>/dev/null
  echo "$message"
}

# Ensure log directory exists with proper permissions
ensure_log_dir() {
  log "Ensuring log directory exists with proper permissions"
  $MKDIR -p "$LOG_DIR" 2>/dev/null || {
    log "ERROR: Failed to create log directory. Continuing with fallback logging."
    return 1
  }

  # Try to fix permissions
  $CHMOD 755 "$LOG_DIR" 2>/dev/null || {
    log "WARNING: Failed to set permissions on log directory."
  }

  # Try to create/touch the log file
  $TOUCH "$LOG_FILE" 2>/dev/null || {
    log "WARNING: Failed to touch log file."
  }

  # Try to set permissions on the log file
  $CHMOD 644 "$LOG_FILE" 2>/dev/null || {
    log "WARNING: Failed to set permissions on log file."
  }

  return 0
}

# Check if a process is running
is_process_running() {
  $SUPERVISORCTL status "$1" | grep -q "RUNNING"
  return $?
}

# Start supervisor if needed
ensure_supervisor_running() {
  if ! $BREW services list | grep -q "supervisor.*started"; then
    log "Supervisor is not running. Starting supervisor..."
    $BREW services start supervisor
    sleep 3  # Give supervisor time to start

    # Check if it started successfully
    if ! $BREW services list | grep -q "supervisor.*started"; then
      log "ERROR: Failed to start supervisor."
      return 1
    fi
  else
    log "Supervisor is already running."
  fi

  return 0
}

# Main function
main() {
  log "Starting run_cron_manager script as user $($WHOAMI)"

  # Ensure log directory and file exist with proper permissions
  ensure_log_dir

  # Ensure supervisor is running
  ensure_supervisor_running || {
    log "ERROR: Supervisor service is not running. Cannot continue."
    return 1
  }

  # Check if cron_manager is already running
  if is_process_running "cron_manager"; then
    log "cron_manager is already running. Stopping it first..."
    $SUPERVISORCTL stop cron_manager
    sleep 2
  fi

  # Start cron_manager
  log "Starting cron_manager via supervisor..."
  $SUPERVISORCTL start cron_manager

  # Check status
  sleep 2
  if is_process_running "cron_manager"; then
    STATUS=$($SUPERVISORCTL status cron_manager)
    log "Current status: $STATUS"
    log "Script completed successfully"
    return 0
  else
    log "ERROR: Failed to start cron_manager"
    return 1
  fi
}

# Run the main function
main
exit $?
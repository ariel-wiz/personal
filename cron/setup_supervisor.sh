#!/bin/bash
# Setup script for supervisor configuration

set -e
echo "=== Setting up Supervisor for Cron Manager ==="

# Paths
SUPERVISOR_CONF_DIR="/usr/local/etc/supervisor.d"
SUPERVISOR_CONF_FILE="${SUPERVISOR_CONF_DIR}/cron-manager.ini"
SCRIPTS_DIR="/Users/ariel/PycharmProjects/personal"
RUNNER_SCRIPT="${SCRIPTS_DIR}/cron/run_cron_manager.sh"
LAUNCHD_FILE="${HOME}/Library/LaunchAgents/com.ariel.run-cron-manager.plist"
LOG_DIR="/Users/ariel/Documents/cron-files"

# Step 1: Install supervisor if needed
if ! command -v supervisord &> /dev/null; then
    echo "Installing supervisor using Homebrew..."
    brew install supervisor
else
    echo "Supervisor is already installed."
fi

# Step 2: Create supervisor config directory if it doesn't exist
if [ ! -d "$SUPERVISOR_CONF_DIR" ]; then
    echo "Creating supervisor config directory..."
    mkdir -p "$SUPERVISOR_CONF_DIR"
fi

# Step 3: Create supervisor configuration
echo "Creating supervisor configuration file..."
cat > "$SUPERVISOR_CONF_FILE" << 'EOL'
[program:cron_manager]
command=/usr/local/bin/python3.8 /Users/ariel/PycharmProjects/personal/cron-manager.py
directory=/Users/ariel/PycharmProjects/personal
environment=PYTHONPATH="/Users/ariel/PycharmProjects/personal"
autostart=false
autorestart=false
startretries=1
startsecs=10
stopwaitsecs=30
stdout_logfile=/Users/ariel/Documents/cron-files/cron-manager.log
stderr_logfile=/Users/ariel/Documents/cron-files/cron-manager-error.log
EOL

# Step 4: Create runner script
echo "Creating runner script..."
cat > "$RUNNER_SCRIPT" << 'EOL'
#!/bin/bash
#
# This script runs the cron manager using supervisorctl
# It's designed to be called by launchd at 5am each morning
#

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

# Check again if supervisor is running
if ! brew services list | grep -q "supervisor.*started"; then
  log "ERROR: Failed to start supervisor. Exiting."
  exit 1
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
EOL

# Make script executable
chmod +x "$RUNNER_SCRIPT"

# Step 5: Create LaunchAgent file
echo "Creating LaunchAgent file..."
cat > "$LAUNCHD_FILE" << 'EOL'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ariel.run-cron-manager</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/ariel/PycharmProjects/personal/run_cron_manager.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>5</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/ariel/Documents/cron-files/run-cron-manager.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/ariel/Documents/cron-files/run-cron-manager-error.log</string>
    <key>RunAtLoad</key>
    <false/>
    <key>KeepAlive</key>
    <false/>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    </dict>
</dict>
</plist>
EOL

# Step 6: Create log directory if it doesn't exist
echo "Ensuring log directory exists..."
mkdir -p "$LOG_DIR"

# Step 7: Load LaunchAgent
echo "Loading LaunchAgent..."
launchctl unload "$LAUNCHD_FILE" 2>/dev/null || true
launchctl load -w "$LAUNCHD_FILE"

# Step 8: Start supervisor service
echo "Starting supervisor service..."
brew services start supervisor

echo "=== Setup complete! ==="
echo "The cron manager will run every day at 5:00 AM using supervisor."
echo "You can manually run it with: supervisorctl start cron_manager"
echo "You can check status with: supervisorctl status cron_manager"
echo "Logs will be available in: $LOG_DIR"
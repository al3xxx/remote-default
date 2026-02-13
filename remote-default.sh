#!/bin/bash
#
# Remote Default Browser (Bash version)
# Opens URLs on a remote host via SSH instead of locally.
# Useful for headless servers without a GUI.
#

set -euo pipefail

# Configuration file location
CONFIG_FILE="${XDG_CONFIG_HOME:-$HOME/.config}/remote-default/config"

# Log file location (will be set from config)
LOG_FILE=""
LOGGING_ENABLED=false
LOG_LEVEL="INFO"

# Log level values
declare -A LOG_LEVELS=(
    ["DEBUG"]=0
    ["INFO"]=1
    ["WARNING"]=2
    ["ERROR"]=3
    ["CRITICAL"]=4
)

# Function to log messages
log_message() {
    local level="$1"
    shift
    local message="$*"
    
    # Check if logging is enabled
    if [[ "$LOGGING_ENABLED" != "true" ]]; then
        return 0
    fi
    
    # Check if log file is set
    if [[ -z "$LOG_FILE" ]]; then
        return 0
    fi
    
    # Check log level
    local current_level="${LOG_LEVELS[$LOG_LEVEL]:-1}"
    local message_level="${LOG_LEVELS[$level]:-1}"
    
    if [[ $message_level -lt $current_level ]]; then
        return 0
    fi
    
    # Create log directory if it doesn't exist
    local log_dir
    log_dir="$(dirname "$LOG_FILE")"
    mkdir -p "$log_dir" 2>/dev/null || true
    
    # Write log message
    local timestamp
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "$timestamp - $level - $message" >> "$LOG_FILE" 2>/dev/null || true
    
    # Also output to stderr if DEBUG level
    if [[ "$LOG_LEVEL" == "DEBUG" ]]; then
        echo "$timestamp - $level - $message" >&2
    fi
}

# Function to handle errors
handle_error() {
    local exit_code=$?
    local line_number=$1
    log_message "ERROR" "Script failed at line $line_number with exit code $exit_code"
}

trap 'handle_error $LINENO' ERR

# Function to load configuration
load_config() {
    REMOTE_HOST=""
    SSH_KEY=""
    REMOTE_BROWSER="xdg-open"
    LOGGING_ENABLED=false
    LOG_LEVEL="INFO"
    LOG_FILE=""
    
    if [[ -f "$CONFIG_FILE" ]]; then
        while IFS='=' read -r key value; do
            # Skip comments and empty lines
            [[ "$key" =~ ^#.*$ ]] && continue
            [[ -z "$key" ]] && continue
            
            # Remove quotes and whitespace from value
            value=$(echo "$value" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^["'\'']//' -e 's/["'\'']$//')
            
            case "$key" in
                remote_host)
                    REMOTE_HOST="$value"
                    ;;
                ssh_key)
                    SSH_KEY="$value"
                    ;;
                remote_browser)
                    REMOTE_BROWSER="$value"
                    ;;
                logging_enabled)
                    if [[ "$value" =~ ^(true|yes|1|on)$ ]]; then
                        LOGGING_ENABLED=true
                    else
                        LOGGING_ENABLED=false
                    fi
                    ;;
                log_level)
                    LOG_LEVEL="${value^^}"  # Convert to uppercase
                    ;;
                log_file)
                    LOG_FILE="$value"
                    ;;
            esac
        done < "$CONFIG_FILE"
    fi
    
    # Set default log file if logging enabled but no file specified
    if [[ "$LOGGING_ENABLED" == "true" && -z "$LOG_FILE" ]]; then
        LOG_FILE="$HOME/.local/share/remote-default/remote-default.log"
    fi
    
    log_message "DEBUG" "Configuration loaded from $CONFIG_FILE"
}

# Function to save configuration
save_config() {
    local remote_host="$1"
    local ssh_key="${2:-}"
    local remote_browser="${3:-xdg-open}"
    local logging_enabled="${4:-false}"
    local log_level="${5:-INFO}"
    local log_file="${6:-}"
    
    mkdir -p "$(dirname "$CONFIG_FILE")"
    
    cat > "$CONFIG_FILE" <<EOF
# Remote Default Browser Configuration
remote_host=$remote_host
ssh_key=$ssh_key
remote_browser=$remote_browser

# Logging Configuration
logging_enabled=$logging_enabled
log_level=${log_level^^}
log_file=$log_file
EOF
    
    echo "Configuration saved to $CONFIG_FILE"
    
    # Reload configuration
    load_config
    log_message "INFO" "Configuration updated"
}

# Function to open URL on remote host
open_url() {
    local url="$1"
    
    log_message "INFO" "Attempting to open URL: $url"
    
    load_config
    
    # Validate configuration
    if [[ -z "$REMOTE_HOST" ]]; then
        log_message "ERROR" "Remote host not configured"
        echo "Error: Remote host not configured." >&2
        echo "Run: $0 --configure" >&2
        return 1
    fi
    
    # Validate URL
    if [[ -z "$url" ]]; then
        log_message "ERROR" "Invalid URL provided: $url"
        echo "Error: Invalid URL provided" >&2
        return 1
    fi
    
    log_message "DEBUG" "Remote host: $REMOTE_HOST"
    log_message "DEBUG" "Remote browser: $REMOTE_BROWSER"
    
    # Build SSH command
    local ssh_cmd="ssh"
    local ssh_opts=(-o BatchMode=yes -o ConnectTimeout=10 -o ServerAliveInterval=5 -o ServerAliveCountMax=3)
    
    if [[ -n "$SSH_KEY" ]]; then
        # Expand tilde in SSH key path
        SSH_KEY="${SSH_KEY/#\~/$HOME}"
        
        if [[ ! -f "$SSH_KEY" ]]; then
            log_message "ERROR" "SSH key not found: $SSH_KEY"
            echo "Error: SSH key not found: $SSH_KEY" >&2
            return 1
        fi
        
        # Check SSH key permissions
        local key_perms
        key_perms=$(stat -c '%a' "$SSH_KEY" 2>/dev/null || stat -f '%A' "$SSH_KEY" 2>/dev/null || echo "")
        if [[ -n "$key_perms" && "$key_perms" != "600" && "$key_perms" != "400" ]]; then
            log_message "WARNING" "SSH key has insecure permissions: $key_perms"
            echo "Warning: SSH key should have 600 permissions" >&2
        fi
        
        ssh_opts+=(-i "$SSH_KEY")
        log_message "DEBUG" "Using SSH key: $SSH_KEY"
    fi
    
    # Execute remote browser command
    local escaped_url
    escaped_url=$(printf '%q' "$url")
    
    log_message "INFO" "Connecting to $REMOTE_HOST..."
    log_message "DEBUG" "SSH command: ssh [options] $REMOTE_HOST '$REMOTE_BROWSER <url>'"
    
    local ssh_output
    local ssh_error
    local ssh_exit_code
    
    # Capture both stdout and stderr
    if ssh_output=$($ssh_cmd "${ssh_opts[@]}" "$REMOTE_HOST" "$REMOTE_BROWSER $escaped_url" 2>&1); then
        ssh_exit_code=0
        log_message "INFO" "Successfully opened URL on remote host"
        [[ -n "$ssh_output" ]] && log_message "DEBUG" "Output: $ssh_output"
        return 0
    else
        ssh_exit_code=$?
        log_message "ERROR" "SSH command failed with exit code $ssh_exit_code"
        
        if [[ -n "$ssh_output" ]]; then
            log_message "ERROR" "Error output: $ssh_output"
            echo "Error opening URL on remote host:" >&2
            echo "$ssh_output" >&2
        fi
        
        # Provide helpful error messages
        case $ssh_exit_code in
            255)
                log_message "ERROR" "SSH connection failed - check host, network, and authentication"
                echo "Hint: SSH connection failed. Check:" >&2
                echo "  - Remote host is reachable" >&2
                echo "  - SSH key is correct" >&2
                echo "  - SSH key permissions are 600" >&2
                ;;
            127)
                log_message "ERROR" "Remote browser command not found: $REMOTE_BROWSER"
                echo "Hint: Browser '$REMOTE_BROWSER' not found on remote host" >&2
                ;;
            124)
                log_message "ERROR" "SSH connection timed out"
                echo "Hint: Check if remote host is reachable and responsive" >&2
                ;;
        esac
        
        return $ssh_exit_code
    fi
}

# Function to configure settings
configure() {
    local remote_host="${1:-}"
    local ssh_key="${2:-}"
    local remote_browser="${3:-xdg-open}"
    local logging_enabled="${4:-false}"
    local log_level="${5:-INFO}"
    local log_file="${6:-}"
    
    if [[ -z "$remote_host" ]]; then
        read -rp "Enter remote host (user@hostname): " remote_host
    fi
    
    if [[ -z "$ssh_key" ]]; then
        read -rp "Enter path to SSH key (optional, press Enter to skip): " ssh_key
    fi
    
    save_config "$remote_host" "$ssh_key" "$remote_browser" "$logging_enabled" "$log_level" "$log_file"
}

# Function to install as default browser
install_browser() {
    log_message "INFO" "Installing as default browser"
    
    local script_path
    script_path="$(readlink -f "$0")"
    log_message "DEBUG" "Script path: $script_path"
    
    # Verify script is executable
    if [[ ! -x "$script_path" ]]; then
        log_message "ERROR" "Script is not executable: $script_path"
        echo "Error: Script is not executable: $script_path" >&2
        echo "Run: chmod +x $script_path" >&2
        return 1
    fi
    
    local desktop_dir="$HOME/.local/share/applications"
    local desktop_file="$desktop_dir/remote-default.desktop"
    
    mkdir -p "$desktop_dir" || {
        log_message "ERROR" "Failed to create desktop directory: $desktop_dir"
        echo "Error: Failed to create desktop directory" >&2
        return 1
    }
    
    # Create desktop entry
    log_message "DEBUG" "Creating desktop file: $desktop_file"
    
    if cat > "$desktop_file" <<EOF
[Desktop Entry]
Version=1.0
Name=Remote Default Browser
Comment=Opens URLs on remote host via SSH
Exec=$script_path %u
Type=Application
Terminal=false
MimeType=x-scheme-handler/http;x-scheme-handler/https;text/html;
StartupNotify=false
EOF
    then
        echo "Created desktop file: $desktop_file"
        log_message "INFO" "Desktop file created: $desktop_file"
    else
        log_message "ERROR" "Failed to create desktop file"
        echo "Error: Failed to create desktop file" >&2
        return 1
    fi
    
    # Update desktop database
    if command -v update-desktop-database &>/dev/null; then
        if update-desktop-database "$desktop_dir" 2>/dev/null; then
            log_message "DEBUG" "Desktop database updated"
        else
            log_message "WARNING" "update-desktop-database failed"
        fi
    else
        log_message "WARNING" "update-desktop-database not found"
        echo "Warning: update-desktop-database not found, skipping"
    fi
    
    # Set as default browser
    if command -v xdg-settings &>/dev/null; then
        log_message "DEBUG" "Setting as default browser with xdg-settings"
        if xdg-settings set default-web-browser remote-default.desktop 2>/dev/null; then
            echo "Set as default browser successfully"
            log_message "INFO" "Set as default browser successfully"
        else
            log_message "ERROR" "Failed to set as default browser"
            echo "Error setting as default browser" >&2
            echo "You may need to set it manually in your system settings" >&2
            return 1
        fi
    else
        log_message "ERROR" "xdg-settings command not found"
        echo "Warning: xdg-settings not found"
        echo "Manually set remote-default.desktop as default browser" >&2
    fi
    
    return 0
}

# Function to uninstall
uninstall_browser() {
    log_message "INFO" "Uninstalling remote-default browser"
    
    local desktop_file="$HOME/.local/share/applications/remote-default.desktop"
    
    if [[ -f "$desktop_file" ]]; then
        if rm -f "$desktop_file" 2>/dev/null; then
            echo "Removed desktop file: $desktop_file"
            log_message "INFO" "Removed desktop file: $desktop_file"
        else
            log_message "ERROR" "Failed to remove desktop file"
            echo "Error: Failed to remove desktop file" >&2
            return 1
        fi
    else
        echo "Desktop file not found"
        log_message "WARNING" "Desktop file not found"
    fi
    
    # Update desktop database
    if command -v update-desktop-database &>/dev/null; then
        local desktop_dir="$HOME/.local/share/applications"
        update-desktop-database "$desktop_dir" 2>/dev/null || true
        log_message "DEBUG" "Desktop database updated"
    fi
    
    echo "Uninstalled successfully"
    echo "Set a new default browser using your system settings"
    log_message "INFO" "Uninstallation complete"
}

# Function to show log
show_log() {
    load_config
    
    local log_file_path="$LOG_FILE"
    if [[ -z "$log_file_path" ]]; then
        log_file_path="$HOME/.local/share/remote-default/remote-default.log"
    fi
    
    echo "Log file: $log_file_path"
    echo "Logging enabled: $LOGGING_ENABLED"
    echo "Log level: $LOG_LEVEL"
    echo ""
    
    if [[ -f "$log_file_path" ]]; then
        local log_size
        log_size=$(stat -c '%s' "$log_file_path" 2>/dev/null || stat -f '%z' "$log_file_path" 2>/dev/null || echo "unknown")
        echo "Log file size: $log_size bytes"
        echo ""
        echo "Last 20 lines:"
        echo "--------------------------------------------------------------------------------"
        tail -n 20 "$log_file_path"
    else
        echo "Log file does not exist yet"
    fi
}

# Function to show help
show_help() {
    cat <<EOF
Remote Default Browser - Opens URLs on remote host via SSH

Usage:
    $0 [URL]                    Open URL on remote host
    $0 --configure              Configure remote host settings
    $0 --install                Install as default browser
    $0 --uninstall              Uninstall and remove desktop file
    $0 --show-log               Display log file location and recent entries
    $0 --help                   Show this help message

Configuration Options:
    --remote-host HOST          Set remote host (user@hostname)
    --ssh-key PATH              Set path to SSH private key
    --remote-browser CMD        Set browser command on remote (default: xdg-open)

Logging Options:
    --enable-logging            Enable logging
    --disable-logging           Disable logging
    --log-level LEVEL           Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    --log-file PATH             Set log file path

Examples:
    # Basic configuration
    $0 --configure
    
    # Configuration with logging
    $0 --remote-host user@example.com --ssh-key ~/.ssh/id_rsa --enable-logging --log-level DEBUG
    
    # Enable logging for existing config
    $0 --enable-logging --log-level INFO
    
    # Install and test
    $0 --install
    $0 https://example.com
    
    # View log
    $0 --show-log

Configuration file: $CONFIG_FILE
EOF
}

# Main script
main() {
    local url=""
    local do_configure=0
    local do_install=0
    local do_uninstall=0
    local do_show_log=0
    local remote_host=""
    local ssh_key=""
    local remote_browser="xdg-open"
    local logging_enabled=""
    local log_level=""
    local log_file=""
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case "$1" in
            --configure)
                do_configure=1
                shift
                ;;
            --install)
                do_install=1
                shift
                ;;
            --uninstall)
                do_uninstall=1
                shift
                ;;
            --show-log)
                do_show_log=1
                shift
                ;;
            --remote-host)
                remote_host="$2"
                do_configure=1
                shift 2
                ;;
            --ssh-key)
                ssh_key="$2"
                shift 2
                ;;
            --remote-browser)
                remote_browser="$2"
                shift 2
                ;;
            --enable-logging)
                logging_enabled="true"
                do_configure=1
                shift
                ;;
            --disable-logging)
                logging_enabled="false"
                do_configure=1
                shift
                ;;
            --log-level)
                log_level="${2^^}"  # Convert to uppercase
                do_configure=1
                shift 2
                ;;
            --log-file)
                log_file="$2"
                shift 2
                ;;
            --help|-h)
                show_help
                exit 0
                ;;
            -*)
                echo "Unknown option: $1" >&2
                show_help >&2
                exit 1
                ;;
            *)
                url="$1"
                shift
                ;;
        esac
    done
    
    # Load config for all operations
    load_config
    
    # Show log
    if [[ $do_show_log -eq 1 ]]; then
        show_log
        exit 0
    fi
    
    # Execute action
    if [[ $do_configure -eq 1 ]]; then
        # Use existing values as defaults if not provided
        [[ -z "$remote_host" ]] && remote_host="$REMOTE_HOST"
        [[ -z "$ssh_key" ]] && ssh_key="$SSH_KEY"
        [[ -z "$logging_enabled" ]] && logging_enabled="$LOGGING_ENABLED"
        [[ -z "$log_level" ]] && log_level="$LOG_LEVEL"
        [[ -z "$log_file" ]] && log_file="$LOG_FILE"
        
        configure "$remote_host" "$ssh_key" "$remote_browser" "$logging_enabled" "$log_level" "$log_file"
        exit $?
    elif [[ $do_install -eq 1 ]]; then
        install_browser
        exit $?
    elif [[ $do_uninstall -eq 1 ]]; then
        uninstall_browser
        exit $?
    elif [[ -n "$url" ]]; then
        open_url "$url"
        exit $?
    else
        show_help
        exit 0
    fi
}

# Run main function with error handling
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    set +e  # Temporarily disable exit on error for trap
    trap 'exit 130' INT  # Handle Ctrl+C gracefully
    main "$@"
    exit_code=$?
    exit $exit_code
fi

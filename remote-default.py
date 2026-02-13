#!/usr/bin/env python3
"""
Remote Default Browser
Opens URLs on a remote host via SSH instead of locally.
Useful for headless servers without a GUI.
"""

import sys
import subprocess
import shlex
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime


class RemoteDefaultBrowser:
    # Valid log levels
    LOG_LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    def __init__(self, config_file=None):
        if config_file is None:
            config_file = Path.home() / '.config' / 'remote-default' / 'config'
        self.config_file = Path(config_file)
        self.config = self.load_config()
        self.logger = self.setup_logging()
    
    def setup_logging(self):
        """Setup logging based on configuration."""
        logger = logging.getLogger('remote-default')
        logger.handlers.clear()  # Clear any existing handlers
        
        # Check if logging is enabled
        if not self.config.get('logging_enabled', False):
            logger.addHandler(logging.NullHandler())
            logger.setLevel(logging.CRITICAL)
            return logger
        
        # Get log level
        log_level_str = self.config.get('log_level', 'INFO').upper()
        log_level = self.LOG_LEVELS.get(log_level_str, logging.INFO)
        logger.setLevel(log_level)
        
        # Get log file location
        log_file = self.config.get('log_file', '')
        if log_file:
            log_path = Path(log_file).expanduser()
        else:
            # Default log location
            log_dir = Path.home() / '.local' / 'share' / 'remote-default'
            log_dir.mkdir(parents=True, exist_ok=True)
            log_path = log_dir / 'remote-default.log'
        
        try:
            # Ensure log directory exists
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create file handler with rotation
            handler = logging.FileHandler(log_path, mode='a', encoding='utf-8')
            
            # Format: timestamp - level - message
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
            # Also log to console if log level is DEBUG
            if log_level == logging.DEBUG:
                console_handler = logging.StreamHandler(sys.stderr)
                console_handler.setFormatter(formatter)
                logger.addHandler(console_handler)
            
            logger.info(f"Logging initialized - Level: {log_level_str}, File: {log_path}")
            
        except Exception as e:
            # If logging setup fails, continue without logging
            logger.addHandler(logging.NullHandler())
            print(f"Warning: Could not setup logging: {e}", file=sys.stderr)
        
        return logger
    
    def load_config(self):
        """Load configuration from file."""
        config = {
            'remote_host': None,
            'ssh_key': None,
            'remote_browser': 'xdg-open',
            'logging_enabled': False,
            'log_level': 'INFO',
            'log_file': ''
        }
        
        if not self.config_file.exists():
            return config
        
        try:
            with open(self.config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        
                        if key in config:
                            # Convert boolean values
                            if key == 'logging_enabled':
                                config[key] = value.lower() in ('true', 'yes', '1', 'on')
                            else:
                                config[key] = value
        except Exception as e:
            print(f"Warning: Error loading config file: {e}", file=sys.stderr)
        
        return config
    
    def save_config(self, remote_host, ssh_key=None, remote_browser='xdg-open',
                    logging_enabled=False, log_level='INFO', log_file=''):
        """Save configuration to file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                f.write("# Remote Default Browser Configuration\n")
                f.write(f"remote_host={remote_host}\n")
                if ssh_key:
                    f.write(f"ssh_key={ssh_key}\n")
                f.write(f"remote_browser={remote_browser}\n")
                f.write("\n# Logging Configuration\n")
                f.write(f"logging_enabled={'true' if logging_enabled else 'false'}\n")
                f.write(f"log_level={log_level.upper()}\n")
                if log_file:
                    f.write(f"log_file={log_file}\n")
            
            self.config = self.load_config()
            # Reinitialize logger with new config
            self.logger = self.setup_logging()
            print(f"Configuration saved to {self.config_file}")
            self.logger.info("Configuration updated")
            
        except Exception as e:
            print(f"Error saving configuration: {e}", file=sys.stderr)
            return 1
        
        return 0
    
    def open_url(self, url):
        """Open URL on remote host via SSH."""
        self.logger.info(f"Attempting to open URL: {url}")
        
        # Validate configuration
        if not self.config['remote_host']:
            error_msg = "Remote host not configured"
            self.logger.error(error_msg)
            print(f"Error: {error_msg}", file=sys.stderr)
            print("Run: remote-default --configure", file=sys.stderr)
            return 1
        
        # Validate URL format
        if not url or not isinstance(url, str):
            error_msg = "Invalid URL provided"
            self.logger.error(f"{error_msg}: {url}")
            print(f"Error: {error_msg}", file=sys.stderr)
            return 1
        
        self.logger.debug(f"Remote host: {self.config['remote_host']}")
        self.logger.debug(f"Remote browser: {self.config['remote_browser']}")
        
        # Build SSH command
        ssh_cmd = ['ssh']
        
        if self.config['ssh_key']:
            ssh_key_path = Path(self.config['ssh_key']).expanduser()
            if not ssh_key_path.exists():
                error_msg = f"SSH key not found: {ssh_key_path}"
                self.logger.error(error_msg)
                print(f"Error: {error_msg}", file=sys.stderr)
                return 1
            
            # Check SSH key permissions
            try:
                key_stat = ssh_key_path.stat()
                if key_stat.st_mode & 0o077:
                    self.logger.warning(f"SSH key has insecure permissions: {oct(key_stat.st_mode)}")
                    print(f"Warning: SSH key should have 600 permissions", file=sys.stderr)
            except Exception as e:
                self.logger.warning(f"Could not check SSH key permissions: {e}")
            
            ssh_cmd.extend(['-i', str(ssh_key_path)])
            self.logger.debug(f"Using SSH key: {ssh_key_path}")
        
        # Add SSH options for non-interactive use
        ssh_cmd.extend([
            '-o', 'BatchMode=yes',
            '-o', 'ConnectTimeout=10',
            '-o', 'ServerAliveInterval=5',
            '-o', 'ServerAliveCountMax=3',
            self.config['remote_host']
        ])
        
        # Remote command to open browser
        remote_cmd = f"{self.config['remote_browser']} {shlex.quote(url)}"
        ssh_cmd.append(remote_cmd)
        
        self.logger.debug(f"SSH command: {' '.join(ssh_cmd[:ssh_cmd.index(self.config['remote_host'])+1])} '<command>'")
        
        try:
            self.logger.info(f"Connecting to {self.config['remote_host']}...")
            result = subprocess.run(
                ssh_cmd, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            
            if result.returncode == 0:
                self.logger.info(f"Successfully opened URL on remote host")
                if result.stdout:
                    self.logger.debug(f"stdout: {result.stdout.strip()}")
                return 0
            else:
                error_msg = f"SSH command failed with exit code {result.returncode}"
                self.logger.error(error_msg)
                
                if result.stderr:
                    self.logger.error(f"stderr: {result.stderr.strip()}")
                    print(f"Error opening URL on remote host:", file=sys.stderr)
                    print(result.stderr, file=sys.stderr)
                
                # Provide helpful error messages based on exit code
                if result.returncode == 255:
                    self.logger.error("SSH connection failed - check host, network, and authentication")
                    print("Hint: SSH connection failed. Check:", file=sys.stderr)
                    print("  - Remote host is reachable", file=sys.stderr)
                    print("  - SSH key is correct", file=sys.stderr)
                    print("  - SSH key permissions are 600", file=sys.stderr)
                elif result.returncode == 127:
                    self.logger.error(f"Remote browser command not found: {self.config['remote_browser']}")
                    print(f"Hint: Browser '{self.config['remote_browser']}' not found on remote host", file=sys.stderr)
                
                return result.returncode
            
        except subprocess.TimeoutExpired as e:
            error_msg = "SSH connection timed out after 30 seconds"
            self.logger.error(error_msg)
            print(f"Error: {error_msg}", file=sys.stderr)
            print("Hint: Check if remote host is reachable and responsive", file=sys.stderr)
            return 1
            
        except FileNotFoundError as e:
            error_msg = "SSH command not found"
            self.logger.critical(f"{error_msg}: {e}")
            print(f"Error: {error_msg}", file=sys.stderr)
            print("Hint: Install openssh-client package", file=sys.stderr)
            return 1
            
        except PermissionError as e:
            error_msg = f"Permission denied: {e}"
            self.logger.error(error_msg)
            print(f"Error: {error_msg}", file=sys.stderr)
            return 1
            
        except Exception as e:
            error_msg = f"Unexpected error: {type(e).__name__}: {e}"
            self.logger.exception(error_msg)
            print(f"Error: {e}", file=sys.stderr)
            return 1
    
    def install(self):
        """Install as default browser on Linux."""
        self.logger.info("Installing as default browser")
        
        try:
            script_path = Path(__file__).resolve()
            self.logger.debug(f"Script path: {script_path}")
            
            # Verify script is executable
            if not os.access(script_path, os.X_OK):
                error_msg = f"Script is not executable: {script_path}"
                self.logger.error(error_msg)
                print(f"Error: {error_msg}", file=sys.stderr)
                print(f"Run: chmod +x {script_path}", file=sys.stderr)
                return 1
            
            # Create .desktop file
            desktop_content = f"""[Desktop Entry]
Version=1.0
Name=Remote Default Browser
Comment=Opens URLs on remote host via SSH
Exec={script_path} %u
Type=Application
Terminal=false
MimeType=x-scheme-handler/http;x-scheme-handler/https;text/html;
StartupNotify=false
"""
            
            desktop_dir = Path.home() / '.local' / 'share' / 'applications'
            desktop_dir.mkdir(parents=True, exist_ok=True)
            desktop_file = desktop_dir / 'remote-default.desktop'
            
            self.logger.debug(f"Creating desktop file: {desktop_file}")
            
            try:
                with open(desktop_file, 'w') as f:
                    f.write(desktop_content)
                print(f"Created desktop file: {desktop_file}")
                self.logger.info(f"Desktop file created: {desktop_file}")
            except PermissionError as e:
                error_msg = f"Permission denied creating desktop file: {e}"
                self.logger.error(error_msg)
                print(f"Error: {error_msg}", file=sys.stderr)
                return 1
            
            # Update desktop database
            try:
                result = subprocess.run(
                    ['update-desktop-database', str(desktop_dir)],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    self.logger.debug("Desktop database updated")
                else:
                    self.logger.warning(f"update-desktop-database returned {result.returncode}")
            except FileNotFoundError:
                self.logger.warning("update-desktop-database not found, skipping")
                print("Warning: update-desktop-database not found, skipping")
            except subprocess.TimeoutExpired:
                self.logger.warning("update-desktop-database timed out")
            except Exception as e:
                self.logger.warning(f"Could not update desktop database: {e}")
            
            # Set as default browser
            try:
                self.logger.debug("Setting as default browser with xdg-settings")
                result = subprocess.run(
                    ['xdg-settings', 'set', 'default-web-browser', 'remote-default.desktop'],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    check=True
                )
                print("Set as default browser successfully")
                self.logger.info("Set as default browser successfully")
                
            except subprocess.CalledProcessError as e:
                error_msg = "Failed to set as default browser"
                self.logger.error(f"{error_msg}: {e}")
                if e.stderr:
                    self.logger.error(f"stderr: {e.stderr}")
                print(f"Error: {error_msg}", file=sys.stderr)
                print("You may need to set it manually in your system settings", file=sys.stderr)
                return 1
                
            except FileNotFoundError:
                self.logger.error("xdg-settings command not found")
                print("Warning: xdg-settings not found", file=sys.stderr)
                print("Manually set remote-default.desktop as default browser", file=sys.stderr)
                
            except subprocess.TimeoutExpired:
                error_msg = "xdg-settings command timed out"
                self.logger.error(error_msg)
                print(f"Error: {error_msg}", file=sys.stderr)
                return 1
                
            except Exception as e:
                error_msg = f"Unexpected error setting default browser: {e}"
                self.logger.exception(error_msg)
                print(f"Error: {e}", file=sys.stderr)
                return 1
            
            return 0
            
        except Exception as e:
            error_msg = f"Installation failed: {type(e).__name__}: {e}"
            self.logger.exception(error_msg)
            print(f"Error: {e}", file=sys.stderr)
            return 1
    
    def uninstall(self):
        """Remove desktop file and reset default browser."""
        self.logger.info("Uninstalling remote-default browser")
        
        try:
            desktop_file = Path.home() / '.local' / 'share' / 'applications' / 'remote-default.desktop'
            
            if desktop_file.exists():
                try:
                    desktop_file.unlink()
                    print(f"Removed desktop file: {desktop_file}")
                    self.logger.info(f"Removed desktop file: {desktop_file}")
                except PermissionError as e:
                    error_msg = f"Permission denied removing desktop file: {e}"
                    self.logger.error(error_msg)
                    print(f"Error: {error_msg}", file=sys.stderr)
                    return 1
            else:
                print("Desktop file not found")
                self.logger.warning("Desktop file not found")
            
            # Update desktop database
            try:
                desktop_dir = Path.home() / '.local' / 'share' / 'applications'
                subprocess.run(
                    ['update-desktop-database', str(desktop_dir)],
                    capture_output=True,
                    timeout=10,
                    check=False
                )
                self.logger.debug("Desktop database updated")
            except FileNotFoundError:
                self.logger.debug("update-desktop-database not found")
            except Exception as e:
                self.logger.warning(f"Could not update desktop database: {e}")
            
            print("Uninstalled successfully")
            print("Set a new default browser using your system settings")
            self.logger.info("Uninstallation complete")
            return 0
            
        except Exception as e:
            error_msg = f"Uninstallation failed: {type(e).__name__}: {e}"
            self.logger.exception(error_msg)
            print(f"Error: {e}", file=sys.stderr)
            return 1


def main():
    parser = argparse.ArgumentParser(
        description='Remote Default Browser - Opens URLs on remote host via SSH'
    )
    parser.add_argument('url', nargs='?', help='URL to open')
    parser.add_argument('--configure', action='store_true', 
                       help='Configure remote host settings')
    parser.add_argument('--install', action='store_true',
                       help='Install as default browser')
    parser.add_argument('--uninstall', action='store_true',
                       help='Uninstall and remove desktop file')
    parser.add_argument('--remote-host', help='Remote host (user@hostname)')
    parser.add_argument('--ssh-key', help='Path to SSH private key')
    parser.add_argument('--remote-browser', default='xdg-open',
                       help='Browser command on remote host (default: xdg-open)')
    
    # Logging arguments
    parser.add_argument('--enable-logging', action='store_true',
                       help='Enable logging')
    parser.add_argument('--disable-logging', action='store_true',
                       help='Disable logging')
    parser.add_argument('--log-level', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                       help='Set log level (default: INFO)')
    parser.add_argument('--log-file',
                       help='Path to log file (default: ~/.local/share/remote-default/remote-default.log)')
    parser.add_argument('--show-log', action='store_true',
                       help='Display the log file location and tail recent entries')
    
    args = parser.parse_args()
    
    browser = RemoteDefaultBrowser()
    
    # Show log
    if args.show_log:
        log_file = browser.config.get('log_file', '')
        if log_file:
            log_path = Path(log_file).expanduser()
        else:
            log_path = Path.home() / '.local' / 'share' / 'remote-default' / 'remote-default.log'
        
        print(f"Log file: {log_path}")
        print(f"Logging enabled: {browser.config.get('logging_enabled', False)}")
        print(f"Log level: {browser.config.get('log_level', 'INFO')}")
        print()
        
        if log_path.exists():
            print(f"Log file size: {log_path.stat().st_size} bytes")
            print("\nLast 20 lines:")
            print("-" * 80)
            try:
                with open(log_path, 'r') as f:
                    lines = f.readlines()
                    for line in lines[-20:]:
                        print(line.rstrip())
            except Exception as e:
                print(f"Error reading log file: {e}")
        else:
            print("Log file does not exist yet")
        
        return 0
    
    # Configure
    if args.configure or args.remote_host or args.enable_logging or args.disable_logging or args.log_level or args.log_file:
        # Get current config values as defaults
        remote_host = args.remote_host
        ssh_key = args.ssh_key
        remote_browser = args.remote_browser
        
        # Logging configuration
        if args.enable_logging:
            logging_enabled = True
        elif args.disable_logging:
            logging_enabled = False
        else:
            logging_enabled = browser.config.get('logging_enabled', False)
        
        log_level = args.log_level if args.log_level else browser.config.get('log_level', 'INFO')
        log_file = args.log_file if args.log_file else browser.config.get('log_file', '')
        
        # Interactive configuration if no remote_host provided
        if not remote_host and (args.configure):
            print("Enter remote host (user@hostname): ", end='')
            remote_host = input().strip()
        
        if not ssh_key and args.configure:
            print("Enter path to SSH key (optional, press Enter to skip): ", end='')
            ssh_key = input().strip()
            if not ssh_key:
                ssh_key = None
        
        # If still no remote host, keep the existing one
        if not remote_host:
            remote_host = browser.config.get('remote_host')
        
        if not ssh_key:
            ssh_key = browser.config.get('ssh_key')
        
        if remote_host:
            return browser.save_config(remote_host, ssh_key, remote_browser,
                                      logging_enabled, log_level, log_file)
        else:
            print("Error: Remote host is required", file=sys.stderr)
            return 1
    
    # Install
    if args.install:
        return browser.install()
    
    # Uninstall
    if args.uninstall:
        return browser.uninstall()
    
    # Open URL
    if args.url:
        return browser.open_url(args.url)
    
    # No arguments - show help
    parser.print_help()
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)

# Logging Guide

Remote Default Browser includes comprehensive logging capabilities to help diagnose issues and monitor operations.

## Quick Start

### Enable Logging

```bash
# Enable logging with default settings (INFO level)
remote-default --enable-logging

# Enable with specific log level
remote-default --enable-logging --log-level DEBUG
```

### View Logs

```bash
# Show log file location and recent entries
remote-default --show-log

# View full log file
tail -f ~/.local/share/remote-default/remote-default.log
```

### Disable Logging

```bash
remote-default --disable-logging
```

## Log Levels

Logging supports five levels, from most verbose to least:

### DEBUG
- **Use for**: Development, troubleshooting complex issues
- **Contains**: All messages including SSH commands, configuration details, step-by-step execution
- **Example**:
  ```
  2026-02-13 14:23:15 - DEBUG - Remote host: user@example.com
  2026-02-13 14:23:15 - DEBUG - Remote browser: firefox
  2026-02-13 14:23:15 - DEBUG - Using SSH key: /home/user/.ssh/id_rsa
  2026-02-13 14:23:15 - DEBUG - SSH command: ssh [options] user@example.com 'firefox <url>'
  ```

### INFO (Default)
- **Use for**: Normal operation monitoring
- **Contains**: High-level operations, successful actions
- **Example**:
  ```
  2026-02-13 14:23:15 - INFO - Attempting to open URL: https://example.com
  2026-02-13 14:23:15 - INFO - Connecting to user@example.com...
  2026-02-13 14:23:16 - INFO - Successfully opened URL on remote host
  ```

### WARNING
- **Use for**: Minimal logging, potential issues only
- **Contains**: Non-critical issues that don't prevent operation
- **Example**:
  ```
  2026-02-13 14:23:15 - WARNING - SSH key has insecure permissions: 644
  2026-02-13 14:23:15 - WARNING - update-desktop-database not found
  ```

### ERROR
- **Use for**: Error tracking only
- **Contains**: Failures that prevent operations
- **Example**:
  ```
  2026-02-13 14:23:15 - ERROR - SSH key not found: /home/user/.ssh/missing_key
  2026-02-13 14:23:15 - ERROR - SSH command failed with exit code 255
  2026-02-13 14:23:15 - ERROR - SSH connection failed - check host, network, and authentication
  ```

### CRITICAL
- **Use for**: Critical failures only (rare)
- **Contains**: System-level failures
- **Example**:
  ```
  2026-02-13 14:23:15 - CRITICAL - SSH command not found
  ```

## Configuration

### Via Command Line

```bash
# Enable logging with INFO level
remote-default --enable-logging --log-level INFO

# Enable logging with DEBUG level and custom log file
remote-default --enable-logging --log-level DEBUG --log-file ~/my-custom.log

# Change log level without reconfiguring host
remote-default --log-level WARNING

# Disable logging
remote-default --disable-logging
```

### Via Configuration File

Edit `~/.config/remote-default/config`:

```ini
# Enable logging
logging_enabled=true

# Set log level
log_level=DEBUG

# Set custom log file (optional)
log_file=/var/log/remote-default.log
```

### Default Settings

If not configured:
- **Logging enabled**: `false`
- **Log level**: `INFO`
- **Log file**: `~/.local/share/remote-default/remote-default.log`

## Log File Management

### Location

**Default location**:
```
~/.local/share/remote-default/remote-default.log
```

**Custom location** (must be writable):
```bash
remote-default --enable-logging --log-file /custom/path/my.log
```

### Viewing Logs

```bash
# Show recent entries
remote-default --show-log

# View full log
cat ~/.local/share/remote-default/remote-default.log

# Follow log in real-time
tail -f ~/.local/share/remote-default/remote-default.log

# View with timestamps highlighted
grep "ERROR\|WARNING" ~/.local/share/remote-default/remote-default.log

# View last 50 lines
tail -n 50 ~/.local/share/remote-default/remote-default.log
```

### Log Rotation

The log file is appended to continuously. To prevent it from growing too large:

#### Manual Rotation

```bash
# Archive old log
mv ~/.local/share/remote-default/remote-default.log \
   ~/.local/share/remote-default/remote-default.log.$(date +%Y%m%d)

# Compress archived logs
gzip ~/.local/share/remote-default/remote-default.log.*

# Remove old logs (older than 30 days)
find ~/.local/share/remote-default/ -name "remote-default.log.*" -mtime +30 -delete
```

#### Automatic Rotation with Logrotate

Create `/etc/logrotate.d/remote-default`:

```
/home/*/.local/share/remote-default/remote-default.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
    create 0644
}
```

Or for single user, add to `~/.logrotate.conf`:

```
~/.local/share/remote-default/remote-default.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
```

Then add to crontab:
```bash
0 0 * * * /usr/sbin/logrotate ~/.logrotate.conf
```

### Clearing Logs

```bash
# Clear log file
> ~/.local/share/remote-default/remote-default.log

# Or delete it
rm ~/.local/share/remote-default/remote-default.log
```

## Troubleshooting with Logs

### Common Issues and Log Analysis

#### SSH Connection Failures

**Enable DEBUG logging**:
```bash
remote-default --log-level DEBUG
remote-default https://example.com
remote-default --show-log
```

**Look for**:
```
ERROR - SSH command failed with exit code 255
ERROR - SSH connection failed - check host, network, and authentication
```

**Solution**: Check SSH key, host reachability, and authentication.

#### Remote Browser Not Found

**Log shows**:
```
ERROR - Remote browser command not found: firefox
ERROR - SSH command failed with exit code 127
```

**Solution**: Install browser on remote host or change `remote_browser` setting.

#### Permission Issues

**Log shows**:
```
WARNING - SSH key has insecure permissions: 644
```

**Solution**: 
```bash
chmod 600 ~/.ssh/id_rsa
```

#### Configuration Issues

**Log shows**:
```
ERROR - Remote host not configured
```

**Solution**:
```bash
remote-default --configure
```

### Debug Workflow

1. **Enable DEBUG logging**:
   ```bash
   remote-default --enable-logging --log-level DEBUG
   ```

2. **Reproduce the issue**:
   ```bash
   remote-default https://example.com
   ```

3. **Check logs**:
   ```bash
   remote-default --show-log
   ```

4. **Look for ERROR or WARNING entries**

5. **Check DEBUG details** for exact commands being executed

6. **Once resolved, reduce log level**:
   ```bash
   remote-default --log-level INFO
   ```

## Performance Considerations

### Log File Size

- **INFO level**: ~100-200 bytes per URL opening
- **DEBUG level**: ~500-1000 bytes per URL opening
- **With typical usage** (10-20 URLs/day): 
  - INFO: ~2-4 KB/day
  - DEBUG: ~10-20 KB/day

### Performance Impact

- **Minimal**: Logging is asynchronous and doesn't block operations
- **File I/O**: Single append operation per log entry
- **DEBUG mode**: Adds console output, slightly slower but negligible for normal use

### When to Use Each Level

| Level    | Use Case                           | Disk Usage | Performance |
|----------|------------------------------------| ---------- | ----------- |
| DEBUG    | Active troubleshooting             | High       | Minimal     |
| INFO     | Normal monitoring                  | Medium     | Minimal     |
| WARNING  | Production (issues only)           | Low        | Negligible  |
| ERROR    | Production (errors only)           | Very Low   | Negligible  |
| Disabled | No logging needed                  | None       | None        |

## Best Practices

### Development

```bash
remote-default --enable-logging --log-level DEBUG
```

### Production

```bash
remote-default --enable-logging --log-level WARNING
```

### Troubleshooting

```bash
# Temporarily enable DEBUG
remote-default --log-level DEBUG

# Reproduce issue
remote-default https://example.com

# Check logs
remote-default --show-log

# Revert to normal level
remote-default --log-level INFO
```

### Privacy Considerations

**Logged information includes**:
- URLs being opened (full URL)
- Remote host address
- SSH key paths
- Error messages
- Timestamps

**NOT logged**:
- SSH key contents
- Passwords
- Session data
- Remote host responses (beyond success/failure)

**For sensitive environments**:
- Use WARNING or ERROR level
- Secure log file permissions
- Regularly rotate/delete logs
- Consider disabling logging

### Log Security

```bash
# Restrict log file permissions
chmod 600 ~/.local/share/remote-default/remote-default.log

# Restrict log directory permissions
chmod 700 ~/.local/share/remote-default/
```

## Examples

### Basic Monitoring Setup

```bash
# Enable INFO logging
remote-default --enable-logging --log-level INFO

# Use normally
remote-default https://example.com

# Check logs periodically
remote-default --show-log
```

### Debugging SSH Issues

```bash
# Enable verbose logging
remote-default --enable-logging --log-level DEBUG

# Try to open URL
remote-default https://example.com

# View detailed logs
remote-default --show-log

# Or follow in real-time
tail -f ~/.local/share/remote-default/remote-default.log
```

### Production Setup with Rotation

```bash
# Enable WARNING level (errors and warnings only)
remote-default --enable-logging --log-level WARNING

# Set up log rotation (see Log Rotation section above)

# Monitor for issues
watch -n 300 'tail -n 20 ~/.local/share/remote-default/remote-default.log'
```

### Checking Historical Issues

```bash
# Search for all errors in the last week
grep "ERROR" ~/.local/share/remote-default/remote-default.log | grep "2026-02-"

# Count errors by type
grep "ERROR" ~/.local/share/remote-default/remote-default.log | cut -d'-' -f4- | sort | uniq -c

# Find all SSH connection failures
grep "SSH connection failed" ~/.local/share/remote-default/remote-default.log
```

## Integration with System Logging

### Systemd Journal (Optional)

For system-wide logging integration, consider redirecting to systemd journal:

```bash
# Run with output to journal
remote-default https://example.com 2>&1 | systemd-cat -t remote-default
```

Or create a wrapper script that logs to journal.

### Syslog Integration

For syslog integration, use logger:

```bash
# Create wrapper that logs to syslog
remote-default --log-level INFO
tail -f ~/.local/share/remote-default/remote-default.log | logger -t remote-default &
```

## Summary

- **Enable logging** for troubleshooting and monitoring
- **Use DEBUG** when actively debugging
- **Use INFO** for normal operation
- **Use WARNING** for production
- **Disable logging** when not needed
- **Rotate logs** to prevent disk space issues
- **Secure log files** if they contain sensitive information
- **Use `--show-log`** for quick log viewing

For more help, see [README.md](README.md) or [QUICKSTART.md](QUICKSTART.md).

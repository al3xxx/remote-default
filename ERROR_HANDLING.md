# Error Handling Guide

This guide covers common errors, their causes, and solutions when using Remote Default Browser.

## Error Categories

### Configuration Errors

#### Error: Remote host not configured
```
Error: Remote host not configured
Run: remote-default --configure
```

**Cause**: Configuration file missing or `remote_host` not set.

**Solution**:
```bash
remote-default --configure
# Or
remote-default --remote-host user@example.com
```

**Log entry**:
```
ERROR - Remote host not configured
```

---

#### Error: Invalid URL provided
```
Error: Invalid URL provided
```

**Cause**: URL argument is empty or malformed.

**Solution**: Provide a valid URL starting with `http://` or `https://`:
```bash
remote-default https://example.com
```

**Log entry**:
```
ERROR - Invalid URL provided: <url>
```

---

### SSH Connection Errors

#### Error: SSH key not found
```
Error: SSH key not found: /home/user/.ssh/id_rsa
```

**Cause**: Specified SSH key file doesn't exist.

**Solution**:
1. Verify SSH key path:
   ```bash
   ls -l ~/.ssh/id_rsa
   ```

2. Generate new key if needed:
   ```bash
   ssh-keygen -t ed25519
   ```

3. Update configuration:
   ```bash
   remote-default --ssh-key ~/.ssh/id_ed25519
   ```

**Log entry**:
```
ERROR - SSH key not found: /home/user/.ssh/id_rsa
```

---

#### Error: SSH connection failed (exit code 255)
```
Error opening URL on remote host:
ssh: connect to host example.com port 22: Connection refused

Hint: SSH connection failed. Check:
  - Remote host is reachable
  - SSH key is correct
  - SSH key permissions are 600
```

**Causes**:
1. Remote host is down or unreachable
2. SSH service not running on remote host
3. Network connectivity issues
4. SSH key authentication failed
5. Firewall blocking connection

**Solutions**:

1. **Check host reachability**:
   ```bash
   ping example.com
   ```

2. **Test SSH manually**:
   ```bash
   ssh user@example.com 'echo "Connection successful"'
   ```

3. **Check SSH key permissions**:
   ```bash
   chmod 600 ~/.ssh/id_rsa
   chmod 644 ~/.ssh/id_rsa.pub
   chmod 700 ~/.ssh
   ```

4. **Verify SSH key is authorized**:
   ```bash
   ssh-copy-id user@example.com
   ```

5. **Check SSH config**:
   ```bash
   ssh -v user@example.com
   ```

6. **Enable DEBUG logging** to see exact error:
   ```bash
   remote-default --log-level DEBUG
   remote-default https://example.com
   remote-default --show-log
   ```

**Log entries**:
```
ERROR - SSH command failed with exit code 255
ERROR - SSH connection failed - check host, network, and authentication
```

---

#### Warning: SSH key has insecure permissions
```
Warning: SSH key should have 600 permissions
```

**Cause**: SSH key file has permissions that are too open (e.g., 644, 777).

**Impact**: May work but is a security risk. SSH may refuse to use the key.

**Solution**:
```bash
chmod 600 ~/.ssh/id_rsa
```

**Log entry**:
```
WARNING - SSH key has insecure permissions: 644
```

---

#### Error: Remote browser command not found (exit code 127)
```
Error opening URL on remote host:
bash: firefox: command not found

Hint: Browser 'firefox' not found on remote host
```

**Cause**: Specified browser is not installed on remote host.

**Solution**:

1. **Install browser on remote host**:
   ```bash
   ssh user@example.com 'sudo apt install firefox'  # Ubuntu/Debian
   ssh user@example.com 'sudo dnf install firefox'  # Fedora
   ```

2. **Or change to installed browser**:
   ```bash
   # Try with default browser handler
   remote-default --remote-browser xdg-open
   
   # Or specify different browser
   remote-default --remote-browser chromium-browser
   ```

3. **Check what's available on remote host**:
   ```bash
   ssh user@example.com 'which firefox google-chrome chromium-browser xdg-open'
   ```

**Log entries**:
```
ERROR - Remote browser command not found: firefox
ERROR - SSH command failed with exit code 127
```

---

#### Error: SSH connection timed out
```
Error: SSH connection timed out after 30 seconds
Hint: Check if remote host is reachable and responsive
```

**Causes**:
1. Remote host is slow to respond
2. Network latency is very high
3. SSH service is overloaded
4. Firewall is partially blocking connection

**Solutions**:

1. **Check network latency**:
   ```bash
   ping -c 5 example.com
   ```

2. **Test SSH with verbose output**:
   ```bash
   ssh -v user@example.com
   ```

3. **Increase timeout** (modify script if needed)

4. **Check remote host load**:
   ```bash
   ssh user@example.com 'uptime'
   ```

**Log entry**:
```
ERROR - SSH connection timed out after 30 seconds
```

---

### Installation Errors

#### Error: Script is not executable
```
Error: Script is not executable: /usr/local/bin/remote-default
Run: chmod +x /usr/local/bin/remote-default
```

**Cause**: Script file doesn't have execute permissions.

**Solution**:
```bash
chmod +x /usr/local/bin/remote-default
# Or
chmod +x remote-default.py  # or remote-default.sh
```

**Log entry**:
```
ERROR - Script is not executable: /usr/local/bin/remote-default
```

---

#### Error: Failed to create desktop file
```
Error: Permission denied creating desktop file
```

**Cause**: No write permissions for `~/.local/share/applications/`

**Solution**:
```bash
# Create directory with proper permissions
mkdir -p ~/.local/share/applications
chmod 755 ~/.local/share/applications

# Try installation again
remote-default --install
```

**Log entry**:
```
ERROR - Permission denied creating desktop file: [errno]
```

---

#### Error: Failed to set as default browser
```
Error: Failed to set as default browser
You may need to set it manually in your system settings
```

**Causes**:
1. `xdg-settings` not available
2. Desktop environment not supported
3. Permissions issue

**Solutions**:

1. **Check if xdg-settings is available**:
   ```bash
   which xdg-settings
   ```

2. **Install xdg-utils** if missing:
   ```bash
   sudo apt install xdg-utils      # Ubuntu/Debian
   sudo dnf install xdg-utils      # Fedora
   sudo pacman -S xdg-utils        # Arch
   ```

3. **Set manually in desktop environment**:
   - **GNOME**: Settings → Default Applications → Web
   - **KDE**: System Settings → Applications → Default Applications
   - **XFCE**: Settings → Preferred Applications

4. **Or use command line**:
   ```bash
   xdg-settings set default-web-browser remote-default.desktop
   ```

**Log entries**:
```
ERROR - xdg-settings command not found
ERROR - Failed to set as default browser
```

---

### System Errors

#### Error: SSH command not found
```
Error: SSH command not found
Hint: Install openssh-client package
```

**Cause**: SSH client not installed on system.

**Solution**:
```bash
sudo apt install openssh-client     # Ubuntu/Debian
sudo dnf install openssh-clients    # Fedora
sudo pacman -S openssh              # Arch
```

**Log entry**:
```
CRITICAL - SSH command not found
```

---

#### Error: Permission denied
```
Error: Permission denied: [operation]
```

**Causes**: Insufficient permissions for file operations.

**Solutions**:

1. **For config directory**:
   ```bash
   mkdir -p ~/.config/remote-default
   chmod 755 ~/.config/remote-default
   ```

2. **For log directory**:
   ```bash
   mkdir -p ~/.local/share/remote-default
   chmod 755 ~/.local/share/remote-default
   ```

3. **For desktop applications**:
   ```bash
   mkdir -p ~/.local/share/applications
   chmod 755 ~/.local/share/applications
   ```

**Log entry**:
```
ERROR - Permission denied: [specific operation]
```

---

## Debugging Workflow

### Step 1: Enable DEBUG Logging

```bash
remote-default --enable-logging --log-level DEBUG
```

### Step 2: Reproduce the Issue

```bash
remote-default https://example.com
```

### Step 3: Check Logs

```bash
remote-default --show-log
```

### Step 4: Analyze Log Entries

Look for:
- ERROR entries (actual failures)
- WARNING entries (potential issues)
- DEBUG entries (detailed execution trace)

### Step 5: Test SSH Manually

```bash
# Test basic connection
ssh user@remote-host 'echo "Connection works"'

# Test browser command
ssh user@remote-host 'xdg-open https://example.com'

# Test with exact configuration
ssh -i ~/.ssh/id_rsa user@remote-host 'firefox https://example.com'
```

### Step 6: Fix and Verify

1. Apply the fix
2. Test again: `remote-default https://example.com`
3. Verify logs: `remote-default --show-log`
4. Reduce log level: `remote-default --log-level INFO`

---

## Error Code Reference

| Exit Code | Meaning | Common Causes |
|-----------|---------|---------------|
| 0 | Success | Operation completed successfully |
| 1 | General error | Configuration issue, file not found, operation failed |
| 127 | Command not found | Remote browser not installed, SSH not found |
| 130 | Interrupted by user | Ctrl+C pressed |
| 255 | SSH error | Connection failed, authentication failed, host unreachable |

---

## Common Scenarios

### Scenario 1: Works from terminal but not from applications

**Symptoms**: `remote-default https://example.com` works, but clicking links doesn't.

**Diagnosis**:
```bash
# Check if registered as default
xdg-settings get default-web-browser

# Check desktop file
cat ~/.local/share/applications/remote-default.desktop

# Check logs when clicking link
remote-default --enable-logging --log-level DEBUG
# Click a link in an application
remote-default --show-log
```

**Solution**:
```bash
# Reinstall
remote-default --uninstall
remote-default --install
```

---

### Scenario 2: Worked before, stopped working

**Possible causes**:
1. Remote host changed/unreachable
2. SSH key changed
3. Configuration file corrupted
4. Desktop environment updated

**Diagnosis**:
```bash
# Check configuration
cat ~/.config/remote-default/config

# Test SSH manually
ssh user@remote-host 'echo "test"'

# Check logs
remote-default --show-log

# Test with DEBUG
remote-default --log-level DEBUG
remote-default https://example.com
remote-default --show-log
```

**Solution**: Reconfigure if needed:
```bash
remote-default --configure
remote-default --install
```

---

### Scenario 3: Slow performance

**Symptoms**: Long delay before URL opens.

**Diagnosis**:
```bash
# Check SSH connection speed
time ssh user@remote-host 'echo "test"'

# Check network latency
ping remote-host

# Enable DEBUG to see timing
remote-default --log-level DEBUG
time remote-default https://example.com
remote-default --show-log
```

**Solutions**:
1. **Improve SSH connection**:
   - Use SSH connection multiplexing
   - Configure SSH keepalive
   
   Add to `~/.ssh/config`:
   ```
   Host remote-host
       ControlMaster auto
       ControlPath ~/.ssh/control-%r@%h:%p
       ControlPersist 10m
   ```

2. **Check remote host performance**:
   ```bash
   ssh user@remote-host 'uptime; free -h'
   ```

---

## Getting Help

### Information to Provide

When reporting issues, include:

1. **Version information**:
   ```bash
   remote-default --help  # Shows script path
   head -5 /usr/local/bin/remote-default  # Shows version comments
   ```

2. **Configuration** (sanitize sensitive info):
   ```bash
   cat ~/.config/remote-default/config
   ```

3. **Debug logs**:
   ```bash
   remote-default --log-level DEBUG
   remote-default https://example.com
   remote-default --show-log
   ```

4. **System information**:
   ```bash
   uname -a
   echo $DESKTOP_SESSION
   xdg-settings get default-web-browser
   ```

5. **Manual SSH test**:
   ```bash
   ssh -v user@remote-host 'xdg-open https://example.com' 2>&1
   ```

### Resources

- [README.md](README.md) - Main documentation
- [LOGGING.md](LOGGING.md) - Logging guide
- [QUICKSTART.md](QUICKSTART.md) - Quick setup guide

### Community Support

Check GitHub issues or create a new issue with:
- Description of the problem
- Steps to reproduce
- Debug logs
- System information

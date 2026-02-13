# Remote Default Browser

Remote Default Browser is a utility for headless Linux servers that forwards URL "open" requests to a remote host with a GUI via SSH. It allows CLI tools (like `gcloud auth`, `npm docs`, etc.) running on a server to automatically open their web-based flows or documentation on your local desktop browser.

## Key Features

- **Dual Implementation**: Choice of Python or Bash versions.
- **SSH Integration**: Uses secure SSH tunnels for communication.
- **Desktop Integration**: Registers as a system-wide default browser.
- **Flexible**: Compatible with any browser on the remote host.
- **Security Focused**: Supports SSH key restrictions and secure defaults.

## Security

### Restricting SSH Key Usage

For maximum security, it is highly recommended to restrict the SSH key used by Remote Default Browser on the **remote host**. This prevents the key from being used for general shell access.

If you are using `remlib` (the default and recommended helper), you can restrict the key in your `~/.ssh/authorized_keys` file on the remote host by adding a `command` prefix:

```text
command="/path/to/remlib "$SSH_ORIGINAL_COMMAND"",no-port-forwarding,no-x11-forwarding,no-agent-forwarding,no-pty ssh-rsa AAAAB3Nza... user@headless-server
```

**Note:**
- Replace `/path/to/remlib` with the actual absolute path to the `remlib` script on your desktop.
- `SSH_ORIGINAL_COMMAND` contains the browser command and URL sent by the headless server.
- The additional options (`no-port-forwarding`, etc.) further harden the connection.

## Installation

### Python Version (Recommended)
```bash
python3 remote-default.py --install
```

### Bash Version
```bash
./remote-default.sh --install
```

## Configuration

Configure the remote host and SSH key:
```bash
remote-default --configure
```

## How it Works

1. **Application** calls `xdg-open <URL>`.
2. **remote-default** handles the request.
3. **SSH** connects to the remote host.
4. **remlib** (or your chosen browser) opens the URL on the remote GUI.

## Documentation

- [LOGGING.md](LOGGING.md) - Detailed logging configuration.
- [ERROR_HANDLING.md](ERROR_HANDLING.md) - Troubleshooting guide.
- [SUMMARY.md](SUMMARY.md) - Project overview and architecture.

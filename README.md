# Remote Default Browser

Remote Default Browser is a utility for headless Linux servers that is trying to mimic **default browser** but instead forwards URL "open" requests to a remote host with a running **real GUI browser**  over SSH connection. It allows CLI tools (like `gcloud auth`, `npm docs`, etc.) running on a server to automatically open their web-based flows or documentation on your local desktop browser. Tested with Linux desktop with running X11 DE (YMMV)

## Key Features

- **Dual Implementation**: Choice of Python or Bash versions.
- **SSH Integration**: Uses secure SSH tunnels for communication.
- **Desktop Integration**: Registers as a system-wide default browser on headless server (at least npm checks for BROWSER env variable and uses it).
- **Flexible**: Compatible with the brosers that support '--new-tab <url>' command.
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

1. **Application** calls `xdg-open <URL>` or in case of some AI CLI terminal tools check for BROWSER env variable and if it exists execute 
```$BROWSER <url>```
2. **remote-default** handles the request.
3. **SSH** connects to the remote host and if <url> contains callback url that points to localhost:port same SSH session creates remote tunnel that connects remote localhost:port to the headless server localhost:port.
4. **remlib** (or your chosen browser) opens the URL on the remote GUI.

## Documentation

- [LOGGING.md](LOGGING.md) - Detailed logging configuration.
- [ERROR_HANDLING.md](ERROR_HANDLING.md) - Troubleshooting guide.
- [SUMMARY.md](SUMMARY.md) - Project overview and architecture.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Disclaimer**: The authors and contributors of this project are not responsible for any damages incurred by its use. Use it at your own risk.

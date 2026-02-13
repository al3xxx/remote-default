# Gemini Project Context: Remote Default Browser

## Project Overview
Remote Default Browser is a utility for headless Linux servers that forwards URL "open" requests to a remote host with a GUI via SSH. It allows CLI tools (like `gcloud auth`, `npm docs`, etc.) running on a server to automatically open their web-based flows or documentation on the user's local desktop browser.

### Main Technologies
- **Languages:** Python 3 (recommended) and Bash (minimal environments).
- **Communication:** SSH with key-based authentication.
- **Desktop Integration:** `xdg-utils` (`xdg-open`, `xdg-settings`), `.desktop` entry files.
- **Configuration:** INI-style configuration stored in `~/.config/remote-default/config`.

### Architecture
1. **Desktop Entry:** Registers `remote-default.desktop` in `~/.local/share/applications/`.
2. **Default Handler:** Sets itself as the system default for `http://`, `https://`, and `text/html`.
3. **Execution Flow:** `Application` → `xdg-open` → `remote-default` → `SSH` → `Remote Browser (e.g., xdg-open on remote)`.

## Building and Running

### Installation
The project provides a `Makefile` for easy installation.

- **Install Python version:**
  ```bash
  make install-python
  ```
- **Install Bash version:**
  ```bash
  make install-bash
  ```

### Configuration
After installation, configure the remote host:
```bash
remote-default --configure
```
Or via CLI:
```bash
remote-default --remote-host user@hostname --ssh-key ~/.ssh/id_rsa
```

### Registration
Register the tool as the system's default browser:
```bash
remote-default --install
```

### Running
Once installed and registered, any tool calling `xdg-open <URL>` will trigger the remote browser. You can also run it manually:
```bash
remote-default https://example.com
```

## Testing
A comprehensive test suite is available to verify installation, configuration, and connectivity.

```bash
./test.sh
```

## Project Structure and Key Files
- `remote-default.py`: Primary Python implementation (robust, recommended).
- `remote-default.sh`: Alternative Bash implementation (lightweight).
- `config.example`: Template for manual configuration.
- `SUMMARY.md`: High-level project summary and features.
- `LOGGING.md`: Detailed guide on configuration and usage of the logging system.
- `ERROR_HANDLING.md`: Comprehensive troubleshooting guide for common SSH and system issues.

## Development Conventions
- **Dual Implementation:** Maintain feature parity between the Python and Bash versions.
- **Logging:** All major operations should be logged. Use the `LOGGING_ENABLED` and `LOG_LEVEL` configuration flags.
- **Error Handling:** Provide user-friendly "Hints" for common failures (especially SSH-related).
- **Security:** Use SSH `BatchMode` and `ConnectTimeout` for non-interactive execution. Ensure SSH key permissions are validated.
- **Unix Philosophy:** The tool is designed to be small, composable, and leverage standard system utilities.

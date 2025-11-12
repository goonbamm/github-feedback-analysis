# Keyring Troubleshooting Guide

## Overview

The `github-feedback` tool uses the system keyring to securely store your GitHub Personal Access Token (PAT). On some systems, especially Linux, you may encounter keyring-related errors.

## Common Errors

### Linux: "object does not exist at path /org/freedesktop/secrets/collection/login"

This error occurs when the D-Bus secrets service (part of GNOME Keyring or KWallet) doesn't have a "login" collection or the collection is not accessible.

**Error message:**
```
object does not exist at path /org/freedesktop/secrets/collection/login
```

### Automatic Fix

The tool now automatically detects keyring failures and falls back to alternative storage methods. You should see a warning message if the system keyring is not accessible:

```
UserWarning: System keyring is not accessible.
Install 'keyrings.alt' for secure storage: pip install keyrings.alt
```

## Solutions

### Option 1: Install keyrings.alt (Recommended)

Install the `keyrings.alt` package for encrypted file-based credential storage:

```bash
pip install keyrings.alt
```

After installation, the tool will automatically use the encrypted file backend.

### Option 2: Set up GNOME Keyring (Linux)

If you want to use the system keyring:

1. Install GNOME Keyring:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install gnome-keyring

   # Fedora/RHEL
   sudo dnf install gnome-keyring

   # Arch Linux
   sudo pacman -S gnome-keyring
   ```

2. Start the keyring daemon:
   ```bash
   gnome-keyring-daemon --start --components=secrets
   ```

3. Create the login keyring:
   ```bash
   # Use seahorse (GNOME's keyring GUI)
   sudo apt-get install seahorse
   seahorse
   ```

### Option 3: Use a Different Collection

Set the `PYTHON_KEYRING_BACKEND` environment variable to use a different backend:

```bash
export PYTHON_KEYRING_BACKEND=keyring.backends.null.Keyring
```

**Note:** This disables secure storage entirely. Not recommended for production use.

## Verifying the Fix

After applying a solution, test the keyring functionality:

```bash
# Run the test script
python test_keyring_fix.py
```

Or initialize the configuration:

```bash
gfa init
```

## Technical Details

The tool uses the following fallback strategy:

1. **Primary:** System keyring (OS-specific)
   - Linux: SecretService (D-Bus)
   - macOS: Keychain
   - Windows: Credential Locker

2. **Fallback 1:** Encrypted file backend (requires `keyrings.alt`)

3. **Fallback 2:** Other available backends with priority > 0

4. **Last Resort:** Null backend (no secure storage)

## Security Considerations

- **Encrypted file backend:** Stores credentials in an encrypted file at `~/.local/share/python_keyring/`
- **System keyring:** Uses OS-provided secure storage
- **Null backend:** Does NOT store credentials securely (not recommended)

## Getting Help

If you continue to experience issues:

1. Check your system logs for D-Bus or keyring errors
2. Verify you have a working keyring daemon running
3. Try installing `keyrings.alt` for a file-based alternative
4. Report the issue at: https://github.com/goonbamm/github-feedback-analysis/issues

## Related Documentation

- [Python keyring documentation](https://pypi.org/project/keyring/)
- [keyrings.alt documentation](https://pypi.org/project/keyrings.alt/)
- [GNOME Keyring documentation](https://wiki.gnome.org/Projects/GnomeKeyring)

# Windows launcher

`windows.py` manages the on-demand Docker/KVM VM and FreeRDP desktop. Nix supplies
the Python interpreter and FreeRDP; `scripts/install-user.py` installs the package.
The linked `~/.local/bin/windows` forwards to this package in the user profile.
Rebuild and reinstall the package after changing the Python source.

See [Windows VM setup](../../docs/WINDOWS-VM.md) for storage, credentials,
installation, shutdown behavior and logs.

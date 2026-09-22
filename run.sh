#!/bin/sh
# Convenience launcher for macOS and Linux. Same as running the script yourself.
cd "$(dirname "$0")" || exit 1

if command -v python3 >/dev/null 2>&1; then
    exec python3 wdgwars_upload_check.py "$@"
elif command -v python >/dev/null 2>&1; then
    exec python wdgwars_upload_check.py "$@"
fi

echo "Python was not found. Install it from https://www.python.org/downloads/"
exit 1

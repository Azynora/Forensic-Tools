#!/usr/bin/env bash
# Forensics Suite - Cross-Platform Command Line Launcher (Linux/POSIX)
# Author: Truong Trieu Vy (trieuvy9198@gmail.com)

set -e

SOURCE="${BASH_SOURCE[0]}"
while [ -h "$SOURCE" ]; do
  DIR="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"
  SOURCE="$(readlink "$SOURCE")"
  [[ $SOURCE != /* ]] && SOURCE="$DIR/$SOURCE"
done
ROOT="$( cd -P "$( dirname "$SOURCE" )" >/dev/null 2>&1 && pwd )"

export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

# Check for Python executable (virtualenv or system)
if [ -f "$ROOT/.venv/bin/python" ]; then
    PYTHON_EXE="$ROOT/.venv/bin/python"
elif [ -f "$ROOT/venv/bin/python" ]; then
    PYTHON_EXE="$ROOT/venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_EXE="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_EXE="python"
else
    echo "[!] Error: python3 or python not found. Please install Python 3.10+." >&2
    exit 1
fi

if [ -d "$ROOT/backend/src" ]; then
    export PYTHONPATH="$ROOT/backend/src:${PYTHONPATH:-}"
fi

exec "$PYTHON_EXE" -m fdctl "$@"

#!/usr/bin/env bash

envname="${1:-${PWD##*/}}"

# use bash strict mode
set -euo pipefail

# create the venv
python3 -m venv "${envname}"

# activate it
source "${envname}/bin/activate"

# upgrade pip inside the venv and add support for the wheel package format
pip install -U pip wheel

# use "pipreqs /path/to/project" to generate requirements.txt
if [ -f requirements.txt ]; then
    pip install -r requirements.txt
fi

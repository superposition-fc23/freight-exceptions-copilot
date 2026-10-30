#!/bin/zsh
# Resets index.html and prototype.html to the blank templates. Run before every new case.
cd "$(dirname "$0")" && cp .blank-index.html index.html && cp .blank-prototype.html prototype.html && echo "index.html and prototype.html reset to blank templates"

#!/bin/zsh
set -eu
FIELD_SOURCE="${0:A:h}"
exec /bin/bash "$FIELD_SOURCE/deploy/bootstrap.sh" stop "$@"

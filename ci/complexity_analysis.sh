#!/bin/sh

set -eu

# TODO set limits, shouldn't expect 100%
lizard -Eduplicate Charon || true

exit 0

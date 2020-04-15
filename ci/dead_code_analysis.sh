#!/bin/sh

set -eu

vulture --min-confidence 100 "Charon"

exit 0

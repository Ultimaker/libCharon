#!/bin/sh

set -eu

# TODO set limits, shouldn't expect 100%
lizard -Eduplicate Charon -T cyclomatic_complexity=20 #This value shall not increase, target is <= 10

exit 0

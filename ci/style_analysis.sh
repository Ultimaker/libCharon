#!/bin/sh

set -eu

git diff origin/master/colorado | pycodestyle --config=pycodestyle.ini --diff

exit 0

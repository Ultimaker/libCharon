#!/bin/sh

set -eu

git diff origin/master/s-line | pycodestyle --config=pycodestyle.ini --diff

exit 0

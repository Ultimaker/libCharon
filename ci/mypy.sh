#!/bin/sh

set -eu

MYPY_FILES=$(git diff --name-only --diff-filter=d origin/master/colorado | grep -i .py$ | cat)

if [ -n "${MYPY_FILES}" ] ; then
    echo "Testing ${MYPY_FILES}"
    for file in ${MYPY_FILES} ; do
        echo "Mypying ${file}"
        mypy --config-file=mypy.ini --follow-imports=skip --cache-dir=/dev/null "${file}"
    done
fi

exit 0

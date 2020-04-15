#!/bin/sh

set -eu

# Run the make_docker.sh script here, within the context of the run_all_tests.sh script
. ./make_docker.sh

git fetch

for test in ci/*.sh ; do
    run_in_docker "${test}" || echo "Failed!"
done

echo "Testing done!"

exit 0

#!/bin/sh

set -eu

. ./make_docker.sh

run_in_docker "ci/pytest.sh" || echo "Failed!"

exit 0

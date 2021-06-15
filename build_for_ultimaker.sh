#!/bin/sh
#
# Copyright (C) 2019 Ultimaker B.V.
#
# SPDX-License-Identifier: LGPL-3.0+

set -eu

ARCH="armhf"

SRC_DIR="$(pwd)"
RELEASE_VERSION="${RELEASE_VERSION:-999.999.999}"
DOCKER_WORK_DIR="/build"
BUILD_DIR_TEMPLATE="_build_${ARCH}"
BUILD_DIR="${BUILD_DIR:-${SRC_DIR}/${BUILD_DIR_TEMPLATE}}"

run_env_check="yes"
run_linters="yes"
run_tests="yes"

# Run the make_docker.sh script here, within the context of the build_for_ultimaker.sh script
. ./make_docker.sh

env_check()
{
    run_in_docker "./docker_env/buildenv_check.sh"
}

run_build()
{
    run_in_docker "./build.sh" "${@}"
}

deliver_pkg()
{
    run_in_docker chown -R "$(id -u):$(id -g)" "${DOCKER_WORK_DIR}"

    cp "${BUILD_DIR}/"*".deb" "./"
}

run_tests()
{
    echo "Testing!"
    # These tests should never fail! See .gitlab-ci.yml
    ./run_style_analysis.sh || echo "Code Style Analaysis Failed!"
    ./run_mypy.sh || echo "MYPY Analysis Failed!"
    ./run_pytest.sh || echo "PyTest failed!"
}

run_linters()
{
    run_shellcheck
}

run_shellcheck()
{
    docker run \
        --rm \
        -v "$(pwd):${DOCKER_WORK_DIR}" \
        -w "${DOCKER_WORK_DIR}" \
        "registry.hub.docker.com/koalaman/shellcheck-alpine:stable" \
        "./run_shellcheck.sh"
}

usage()
{
    echo "Usage: ${0} [OPTIONS]"
    echo "  -c   Skip build environment checks"
    echo "  -h   Print usage"
    echo "  -l   Skip code linting"
    echo "  -t   Skip tests"
}

while getopts ":chlt" options; do
    case "${options}" in
    c)
        run_env_check="no"
        ;;
    h)
        usage
        exit 0
        ;;
    l)
        run_linters="no"
        ;;
    t)
        run_tests="no"
        ;;
    :)
        echo "Option -${OPTARG} requires an argument."
        exit 1
        ;;
    ?)
        echo "Invalid option: -${OPTARG}"
        exit 1
        ;;
    esac
done
shift "$((OPTIND - 1))"

if ! command -V docker; then
    echo "Docker not found, docker-less builds are not supported."
    exit 1
fi


if [ "${run_env_check}" = "yes" ]; then
    env_check
fi

if [ "${run_linters}" = "yes" ]; then
    run_linters
fi

run_build "${@}"

if [ "${run_tests}" = "yes" ]; then
    run_tests
fi

deliver_pkg

exit 0

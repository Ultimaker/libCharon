#!/bin/bash
# Copyright (C) 2019 Ultimaker B.V.
# Copyright (C) 2019 Raymond Siudak <raysiudak@gmail.com>
#
# SPDX-License-Identifier: LGPL-3.0+

set -eu
set -o pipefail

usage()
{
    echo "Usage: ${0} [OPTIONS] <release version> <release distribution>"
    echo "Triggers the release of this package to the CloudSmith package storage, given the"
    echo "release version passed as argument to the script, e.g. 6.0.1 or 6.0.1-dev."
    echo ""
    echo "An optional release distribution on CloudSmith can be passed in after the release version argument."
    echo "By default all packages will be released as Debian Buster compatible packages."
    echo "Packages can be released to cloudsmith as Debian Jessie compatible by passing in the argument \"jessie\","
    echo "e.g \"./release.sh 6.0.1 jessie\" will release a Debian Buster compatible package to the packages-official repository"
    echo ""
    echo "This script wil create a tag and push that to origin, this triggers the CI job to release"
    echo "to CloudSmith. The CI release job will differentiate between pushing to official release"
    echo "storage or development release storage, pushing to development release storage is "
    echo "triggerred by adding the '-dev' postfix to the release version e.g. 6.2.0-dev."
    echo ""
    echo "    -h   Print usage"
}

is_tag_existing_locally()
{
    if git rev-parse "${TAG}" > /dev/null 2>&1; then
        echo "WARNING: Local Git tag '${TAG}' already exists."
        return 0
    fi
    return 1
}


is_tag_on_github()
{
    if ! git ls-remote origin ":refs/tags/${TAG}"; then
        echo "WARNING: GitHub tag '${TAG}' already exists."
        return 0
    fi
    return 1
}

trigger_release()
{
    if is_tag_existing_locally; then
        if ! git tag -d "${TAG}"; then
            echo "Error: failed to clear local tag'${TAG}'."
            exit 1
        fi
    fi

    if ! git tag "${TAG}"; then
        echo "Error: failed to tag with '${TAG}'."
        exit 1
    fi

    if ! is_tag_on_github; then
        if ! git push origin "${TAG}"; then
            echo "Error: failed to push tag: '${TAG}'."
            exit 1
        fi
        return 0
    fi

    return 1
}

while getopts ":h" options; do
    case "${options}" in
    h)
        usage
        exit 0
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

#Check that the minimum amount of required arguments, at least the version number, has been provided
if [ "${#}" -lt 1 ]; then
    echo ""
    echo "Too little arguments, arguments should be at least one: <release_version>."
    echo ""
    usage
    exit 1
fi

RELEASE_VERSION="${1}"
RELEASE_DISTRO="${2:-buster}"

TAG="$(git rev-parse --abbrev-ref HEAD)-v${RELEASE_VERSION}-${RELEASE_DISTRO}"

#Check that a recognizable distribution has been provided
if [[ ! "${RELEASE_DISTRO}" =~ ^(jessie|buster)$ ]]; then
  echo ""
  echo "The provided release distribution: '${RELEASE_DISTRO}', is not known. Please provide a supported distribution: 'jessie' or 'buster'"
  echo ""
  exit 1
fi

if echo "${RELEASE_VERSION}" | grep -E '^[0-9]{1,3}+\.[0-9]{1,3}+\.[0-9]{1,3}+(-dev|-[0-9]+)?$'; then

    if is_tag_on_github; then
        echo "Error: Cannot continue, tag is already on GitHub."
        exit 1
    fi

    if trigger_release; then
        echo "Successfully triggered release '${RELEASE_VERSION}' to distribution '${RELEASE_DISTRO}' on Cloudsmith, follow the build at: http://34.90.73.76/dashboard."
        exit 0
    fi

    echo "Something went wrong triggering the release, please check the warnings and correct manually."
fi

echo "Invalid release version: '${RELEASE_VERSION}' given."
usage

exit 1

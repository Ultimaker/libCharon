#!/bin/bash

# Abort on errors, as well as unset variables. Makes the script less error prone.
set -o errexit

rm -rf dist || true
rm -rf build_env | true

#------------------------------------------------------
# Set up Python

virtualenv build_env
source build_env/bin/activate

pip3 install -r requirements.txt
pip3 install -r requirements-testing.txt

#------------------------------------------------------
# Python Package build

python3 setup.py bdist_wheel

#------------------------------------------------------
# Debian package build

BUILD_DIR=_build_armhf
VERSION=9999.99.99

rm -rf $BUILD_DIR || true
mkdir -p $BUILD_DIR

cd $BUILD_DIR
cmake .. -DCMAKE_INSTALL_PREFIX=/usr -DCPACK_PACKAGE_VERSION=${VERSION} -DEMBEDDED=ON
make package
cd ..

rm -rf build_env

echo ""
echo "Your fresh packages:"
echo ""
ls -alp dist/*.whl
ls -alp $BUILD_DIR/*.deb

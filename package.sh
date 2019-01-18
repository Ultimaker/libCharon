#!/bin/bash

# Abort on errors, as well as unset variables. Makes the script less error prone.
set -o errexit

rm -rf dist || true
rm -rf build_env | true

virtualenv build_env
source build_env/bin/activate

pip3 install -r requirements.txt
pip3 install -r requirements-testing.txt

python3 setup.py bdist_wheel

rm -rf build_env

echo ""
ls -alp dist

#! /bin/sh

set -x
set -e

# Try the builds first
python setup.py sdist
python setup.py bdist_wheel

# Upload the packages
python setup.py sdist upload
python setup.py bdist_wheel upload

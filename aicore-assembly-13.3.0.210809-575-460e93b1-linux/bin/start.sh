#!/bin/bash

# Root of the whole AI Core application
ROOT_DIR=$(readlink -f $0 | xargs dirname | xargs dirname)

SITE_PACKAGES=$ROOT_DIR/lib
MANAGE_PY=$SITE_PACKAGES/manage.py

PYTHON=$ROOT_DIR/bin/python/bin/python3

export PYTHONPATH=$PYTHONPATH:$SITE_PACKAGES

cd $ROOT_DIR
exec $PYTHON $MANAGE_PY run all

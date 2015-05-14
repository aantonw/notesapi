#!/usr/bin/env bash -e
#
if [ ! -d "env" ]; then
  echo "----------------------------"
  echo "creating virtual environment"
  echo "----------------------------"
  virtualenv --no-site-packages env
  echo "----------------------------"
  echo "activate virtual environment"
  source ./env/bin/activate
  echo "install required libraries"
  echo "----------------------------"
  pip install -r requirements.txt
else
  echo "activate virtual environment"
  source ./env/bin/activate
fi
echo "----------------------------"
echo "running test"
echo "----------------------------"
python notesapi_test.py -v
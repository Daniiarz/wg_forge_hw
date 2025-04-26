#!/bin/bash

if [[ -z "$1" ]]; then
  exit 1
fi

echo "Running your code ..."
python3 "$1" &

sleep 3

echo "Running your tests...."


timeout -s 9 30s pytest --no-showlocals --no-header --disable-warnings tests.py

exit_code=$?
exit $exit_code


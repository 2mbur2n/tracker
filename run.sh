#!/bin/bash

./date.sh
if [ "$?" -ne 0 ]; then
    echo 'data.dat not current'
    echo './add.sh <weight>'
    exit 1
fi 

python3 main.py "$@"


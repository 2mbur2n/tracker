#!/bin/bash

if [[ $# -ne 1 ]]; then
    echo './minutes.sh <amonut>'
    exit 1
fi

./date.sh
if [ "$?" -ne 0 ]; then
    echo 'data.dat not current'
    echo './add.sh <weight>'
    exit 1
fi 

python3 minutes.py "$@"
tail -1 data.dat 


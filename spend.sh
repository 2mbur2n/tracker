#!/bin/bash

if [[ $# -ne 1 ]]; then
    echo './spend.sh <amonut>'
    exit 1
fi

./date.sh
if [ "$?" -ne 0 ]; then
    echo 'data.dat not current'
    echo './add.sh <weight>'
    exit 1
fi 

echo "`head -n -1 data.dat`" > data.new
echo "`tail -1 data.dat`+$1" >> data.new
mv data.new data.dat
tail -1 data.dat


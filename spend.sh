#!/bin/bash

if [[ $# -ne 1 ]]; then
    echo './spend.sh <amonut>'
    exit 1
fi

echo "`head -n -1 data.dat`" > data.new
echo "`tail -1 data.dat`+$1" >> data.new
mv data.new data.dat
tail -1 data.dat


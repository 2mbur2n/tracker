#!/bin/bash

today="`date +%m/%d/%y`"
last="`tail -1 data.dat | cut -c 1-8`"

if [ "$today" = "$last" ]; then
    exit 0
else
    exit 1
fi


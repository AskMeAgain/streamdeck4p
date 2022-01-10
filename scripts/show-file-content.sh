#!/bin/sh

cat $1 |  yad --list --height=900 --width=1400 --no-headers --column "ABC" | xclip -sel clip

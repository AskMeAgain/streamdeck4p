#!/bin/sh

cat $1 |  yad --list --height=400 --width=400 --no-headers --column "ABC" | xclip -sel clip

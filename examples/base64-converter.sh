#!/bin/sh

text=$(yad --entry)

yad --button='to Base64':0 --button='from Base64':1 --button="Exit"
mode=$?

echo $text

if [[ mode -eq "0" ]]; then
  result=$(echo $text | base64)
else
  result=$(echo $text | base64 -d)
fi

yad --text $result --selectable-labels --height=400 --width=500 \
  --button="Copy":"bash -c 'echo $result | xclip -sel clip'" \
  --button="Exit"




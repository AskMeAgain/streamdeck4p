#!/bin/sh

text=$(yad --entry)

if [[ $? -eq "1" ]]; then
    echo "Exit because of cancel pressed"
exit
fi

result=$(yad --button='to Base64':1 --button='from Base64':2 --button='Exit':0)
mode=$?

if [[ mode -eq "0" ]]; then
  echo "Exit because of exit pressed"
  exit
fi

if [[ mode -eq "1" ]]; then
  result=$(echo $text | base64)
else
  result=$(echo $text | base64 -d)
fi

yad --text $result --selectable-labels --height=400 --width=500 \
  --button="Copy":"bash -c 'echo $result | xclip -sel clip'" \
  --button="Exit"




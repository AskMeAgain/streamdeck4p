#!/bin/sh

result=$(yad --entry --button=local:4 --button=int:5 --button=sandbox:6)

mode=$?

if [[ mode -eq "4" ]]; then
  echo "local"
  exit 0
fi

if [[ mode -eq "5" ]]; then
  echo "int"
  exit 1
fi

if [[ mode -eq "6" ]]; then
  echo "sandbox"
  exit 2
fi

echo $result
exit 3


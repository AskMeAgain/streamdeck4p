#!/bin/sh

result=$(yad --entry --button=local --button=int --button=sandbox)

mode=$?

if [[ mode -eq "0" ]]; then
  echo "local"
fi

if [[ mode -eq "1" ]]; then
  echo "int"
fi

if [[ mode -eq "2" ]]; then
  echo "sandbox"
  exit
fi

echo $result
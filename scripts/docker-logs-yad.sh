#!/bin/sh

docker logs $1 | awk '{print "#"$0}' | yad --width=700 --height=700 --progress --hide-text --text="Logs of $1" --percentage=10 --enable-log --log-expanded

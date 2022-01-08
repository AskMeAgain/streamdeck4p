#!/bin/python3

import subprocess

command = ["newman", "run", "postman_collection.json", "--reporter-cli-no-failures", "--reporter-cli-no-assertions",
           "--reporter-cli-no-summary", "--reporter-cli-no-banner"]

i = 0

expected = 3

yad_command = [
    "yad",
    "--progress",
    "--title=\"YAD Custom Dialog Buttons\"",
    "--button=Exit",
    "--enable-log='                                     '",
    "--log-expanded",
    "--height=300",
    "--width=300",
    "--log-height=250",
    "--posy=100",
    "--posx=1500"
]

with subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=1, universal_newlines=True) as newman_process:
    with subprocess.Popen(yad_command, stdin=subprocess.PIPE) as yad_process:
        for line in newman_process.stdout:
            if line != "\n":
                if line.startswith("→"):
                    i += 1
                fixedLine = line.strip("\n")[2:]
                percent = round((i / expected) * 100)
                if line.startswith("→") or "RESULT:" in fixedLine:
                    yad_process.stdin.write(f"{percent}\n#{i}/{expected} → {fixedLine}\n".encode())
                    yad_process.stdin.flush()

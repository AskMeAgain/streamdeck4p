# Streamdeck4p (Streamdeck for programmers)

This project is a python script to control your streamdeck.

It is loosely based on [timothycrosley's Streamdeck-ui](https://github.com/timothycrosley/streamdeck-ui)

The difference to all the other solutions is that you can do toggles and keep a persisted state on each button, which
can be referenced by other buttons.

## Example

Have one button to select a dev environment (local -> int -> sandbox -> prod), pressing the button will iterate over the
list and will show a different text + image based on the name of the environment. Other buttons now execute their script
based on the state of the environment toggle. All via an extremely simple mechanism. Also each toggle state can have a
different picture.

See the streamdeck4p.json file for an example.

## Features

* configuration is done via json file(s)
* unlimited pages
* toggles!
* write any text via key presses
* start any process
* show pictures/text and exchange picture/text based on a toggle

## Getting started

1. clone this repo somewhere
2. Install [poetry](https://python-poetry.org/)
3. execute `poetry update`
4. Plugin your streamdeck
5. find your streamdeck SerialId by running `python3 streamdeck4p.py --show-devices`
6. Create/update the streamdeck4p.json file in this folder
    1. Additionally any file with a name pattern like _streamdeck4p-*.json_ is getting merged into the streamdeck4p.json
       file on startup
7. Startup the main script via `python3 streamdeck4p.py`

## json format

the streamdeck4p.json file consist of a field for each streamdeck (via streamdeck serial id)
each streamdeck has a current_page field and any amount of pages.

Each page consists of a field for each possible keypress, named from 0 to X where X is the amount of keys on your
streamdeck minus 1.

A button can have the following fields:

| Field        | Description                                                                                   |
|--------------|-----------------------------------------------------------------------------------------------|
| text         | The text which is displayed on the streamdeck                                                 |
| keys         | the text which will be written via key presses. Check out [Key presses](#Keypresses)          |
| command      | the command which will be executed in a subshell                                              |
| image_mode   | if full, the text will not be placed at the bottom, but in the middle of the button           |
| image_url    | url to the button image                                                                       |
| toggle_index | internal array pointer of the toggle. This index will count up whenever the button is pressed |
| ANY LIST     | Please check out [State](#State)                                                              |

Example streamdeck4p.json:

    {
      "STREAMDECK_SERIAL_ID": {
        "current_page": "PAGE_NAME",
        "PAGE_NAME": {
          "0": {
            "command": "echo $_text_state_0_$",
            "image_mode": "full",
            "text": "$_text_state_0_$",
            "toggle_index": 3,
            "state": [
              "local",
              "int",
              "sandbox",
              "prod"
            ],
            "text_state": [
              "different",
              "different2",
              "1231123",
              "123222222"
            ],
            "image_url": "icons/$_state_0_$.png"
          }
        }
      }
    }

## State

any substring with the pattern `$_STATESTORENAME_KEYNAME_$` (examples: $_text_state_0_$, or $_abc_123_$)
is getting interpolated **before** it gets processed by the specific routing:

* Before a text is written
* Before a command is getting executed
* Before a text is displayed on the StreamDeck
* Before an image is rendered on the StreamDeck

A lookup happens based on the State store name and key number:

if button 10 defines an array called abc_def[a,b,c,d,e], any button on the same page can do a lookup in this statestore
by using a string like: $_abc_def_10_$. Now the toggle_index of button 10 is used to determine the correct value: if the
toggle_index is 3, then $_abc_def_0_$ is getting replaced with d.

In the example above, button 0 tries to displays the text **_$_text_state_0_$_** on the lcd, which is getting
interpolated from "
text_state". Currently _toggle_index_ is 3, that means "1231123" is getting displayed. The image_url is differently
calculated, as it uses the "state" array to do its lookup (-> sandbox).

**if you have atleast one state array, then there needs to exist a state arrray called "state", or else the application
will not work**

## Keypresses

Pynput is used under the hood.

each keypress will be separated by comma (","), key combinations can be done via plus ("+")

    "e,c,h,o,<space>,t,e,s,t,<enter>"
    "<ctrl>+<f1>,a,b,c,d"
    "<ctrl>+<shift>+a

## External Changes

You can change the json files externally and trigger an usr1 signal on the running script to reload the page.

    kill -USR1 PID_OF_THE_PYTHON_SCRIPT

You can also just run the python script again with the --reload-config flag to reload the configs.

    python3 streamdeck4p.py --reload-config STREAMDECK_SERIAL_ID

There is also a switch_page switch to change the current page

    python3 streamdeck4p.py --switch-page STREAMDECK_SERIAL_ID PAGE_NAME

To shutdown the script, press CTRL + C, kill it via SIGINT or via the script itself

    python3 streamdeck4p.py --exit

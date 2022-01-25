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
3. execute `poetry install`
4. Add [pygobject](https://pygobject.readthedocs.io/en/latest/getting_started.html) (choose **Installing from PyPI with
   pip**, but replace pip with poetry add)
5. Plugin your streamdeck
6. find your streamdeck SerialId by running `poetry run streamdeck4p --show-devices`
7. Create/update the streamdeck4p.json file in this folder
    1. Additionally any file with a name pattern like _streamdeck4p-*.json_ is getting merged into the streamdeck4p.json
       file on startup
8. Startup the main script via `poetry run streamdeck4p`

## json format

the streamdeck4p.json file consist of a field for each streamdeck (via streamdeck serial id)
each streamdeck has a current_page field and any amount of pages.

Each page consists of a field for each possible keypress, named from 0 to X where X is the amount of keys on your
streamdeck minus 1.

A button can have the following fields:

| Field         | Description                                                                                                                                                                                                                                                                                                       |
|---------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| text          | The text which is displayed on the streamdeck. FontAwesome compatible (see [here](#FontAwesome))                                                                                                                                                                                                                  |
| keys          | the text which will be written via key presses. Check out [Key presses](#Keypresses)                                                                                                                                                                                                                              |
| command       | the command which will be executed in a subshell                                                                                                                                                                                                                                                                  |
| image_mode    | if full, the text will not be placed at the bottom, but in the middle of the button                                                                                                                                                                                                                               |
| image_url     | url to the button image. Can parse straight rgb colors (see [here](Image Url))                                                                                                                                                                                                                                    |
| toggle_index  | internal array pointer of the toggle. This index will count up whenever the button is pressed                                                                                                                                                                                                                     |
| notification  | if you set this to true, then a system inotify call will be made when you start and stop a command                                                                                                                                                                                                                |
| text_color    | Color of the text (white, blue, black etc)                                                                                                                                                                                                                                                                        |                                                                                     |
| text_size     | Size of the text                                                                                                                                                                                                                                                                                                  |                                                                                     |
| ask_for_input | A popup will open, which asks the user for input. The result is stored in a state called "input" and can be reference like a normal state (aka $_input_0_$ for example). If prefixed with sh-> the script will be called instead and the stdout value will be used instead.                                       |                                                                                     |
| yad-additions | Whenever an option uses yad, these parameters will be additionally supplied (--height=400 or stuff like that)                                                                                                                                                                                                     |
| toggle_mode   | default is "simple", which makes the button just a simple toggle. If you chose "button_selection", then yad will open and present you all the possible toggle options to chose from. It uses the state array for displaying. If toggle mode "script" then the return value of the script in ask_for_input is used |
| ANY LIST      | Please check out [State](#State)                                                                                                                                                                                                                                                                                  |
| top_margin    | Margin for the picture. Positive value moves up, negative moves the text downwards                                                                                                                                                                                                                                |
| line_break_on | this sign will be replaced with \n in a displayed text                                                                                                                                                                                                                                                            |
| defaultbutton | A button with the name "default" will be the default template which other buttons (aka button 0-14) inherite                                                                                                                                                                                                      |

Example streamdeck4p.json:

    {
      "STREAMDECK_SERIAL_ID": {
        "current_page": "PAGE_NAME",
        "PAGE_NAME": {
          "0": {
            "command": "echo $_text_state_0_$",
            "image_mode": "full",
            "text": "$_text_state_0_$",
            "notification": True,
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
            "ask_for_input": "Please enter a value!",
            "image_url": "icons/$_state_0_$.png"
          }
        }
      }
    }

## State

any substring with the pattern `$_STATESTORENAME_KEYNAME_$` (examples: `$_text_state_0_$`, or `$_abc_123_$`)
is getting interpolated **before** it gets processed by the specific routing:

* Before a text is written
* Before a command is getting executed
* Before a text is displayed on the StreamDeck
* Before an image is rendered on the StreamDeck

A lookup happens based on the State store name and key number:

if button 10 defines an array called abc_def[a,b,c,d,e], any button on the same page can do a lookup in this statestore
by using a string like: `$_abc_def_10_$`. Now the toggle_index of button 10 is used to determine the correct value: if
the toggle_index is 3, then `$_abc_def_0_$` is getting replaced with d.

In the example above, button 10 tries to displays the text `$_text_state_0_$` on the lcd, which is getting interpolated
from "text_state". Currently _toggle_index_ is 3, that means "1231123" is getting displayed. The image_url is
differently calculated, as it uses the "state" array to do its lookup (-> sandbox).

**if you have atleast one state array, then there needs to exist a state arrray called "state", or else the application
will not work**

### Input state

If you add the "ask_for_input" flag, then a popup will ask the user for input. The result is stored in a state called **
input** and can be referenced like normal.

    $_input_0_$ #is the reference to the input state of button 0

## Keypresses

Pynput is used under the hood.

each keypress will be separated by comma (","), key combinations can be done via plus ("+").

If you want to write a bigger word, then you can add the prefix "sep->" to **sep**arate the complete word by comma.

If you want to wait for some time you can add delay, to wait for 0.25 seconds

    "e,c,h,o,<space>,t,e,s,t,<enter>"
    "e,c,h,o,delay,<space>" //waits 0.25 seconds until pressing enter
    "<ctrl>+<f1>,a,b,c,d"
    "<ctrl>+<shift>+a"
    "sep->HELLOWORLD" //this will be handled as H,E,L,L,O,W,O,R,L,D

## External Changes

You can change the json files externally and trigger an usr1 signal on the running script to reload the page.

    kill -USR1 PID_OF_THE_PYTHON_SCRIPT

You can also just run the python script again with the --reload-config flag to reload the configs.

    python3 streamdeck4p.py --reload-config STREAMDECK_SERIAL_ID

There is also a switch_page switch to change the current page

    python3 streamdeck4p.py --switch-page STREAMDECK_SERIAL_ID PAGE_NAME

To shutdown the script, press CTRL + C, kill it via SIGINT or via the script itself

    python3 streamdeck4p.py --exit

To press a button via cli:

    python3 streamdeck4p.py --press-button DECK_ID PAGE_NAME BTN_ID

## FontAwesome

[FontAwesome](https://github.com/FortAwesome/Font-Awesome) is also integrated into this script. If you want to display
font awesome icons instead of pictures just display a text only, and prefix the **unicode** font awesome icon with "
fa->". Also the F needs to be in uppercase:

    "text": "fa->\uF2b9"

## Image Url

You can pass a normal url to an image for display via url->, but you can also parse straight values if you prefix with bg->

    "image_url": "url->http//.google.de/iconwhatever.png" #this downloads the image
    "image_url": "bg->black" #this renders a black background
    "image_url": "bg->#123,123,123" #this renders an rgb value as background color
    

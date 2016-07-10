#!/usr/bin/env bash

CURDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
NUKEPATH="/Applications/Nuke9.0v8/Nuke9.0v8.app/Contents/MacOS/Nuke9.0v8"

export PYTHONPATH=$CURDIR
export PYTHONPATH=${PYTHONPATH}:/Users/kif/Documents/AnimationMentor/panda/Assets/tools/lib/working/nuke/python
export PYTHONPATH=${PYTHONPATH}:/Users/kif/Documents/AnimationMentor/panda/Assets/tools/lib/working/nuke/startup

COMMAND="$1"

if [ "$COMMAND" = "run" ]
then
    python ./logger.py

elif [ "$COMMAND" = "test" ]
then
    python ./tests/simple_test.py

elif [ "$COMMAND" = "nuke" ]
then
    $NUKEPATH -t ./tests/simple_test.py

elif [ "$COMMAND" = "build_ui" ]
then
    pyside-uic resources/publish_dialog.ui -o ui/publish_dialog.py

else
    echo "Command is unknown"
fi

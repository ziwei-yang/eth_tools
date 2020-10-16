#!/bin/bash --login
SOURCE="${BASH_SOURCE[0]}"
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"

cd $DIR

# Must have python3 in PATH
which python3
[[ $? != 0 ]] && echo "No python3" && exit 1

# Init $DIR/venv and enable it.
[ ! -d $DIR/venv ] && python3 -m venv $DIR/venv
[ -f $DIR/venv/bin/activate ] && echo "activate venv now" && source $DIR/venv/bin/activate

# Check pip and install libs.
pip_path=$( which pip )
[[ $pip_path != $DIR/venv/bin/pip ]] && echo "Unexpected pip: $pip_path" && exit 1
$pip_path install -r $DIR/requirements.txt || exit 1

echo "$pip_path install $DIR/eth_tool"
pip install -e $DIR/

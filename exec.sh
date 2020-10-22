#!/bin/bash --login
SOURCE="${BASH_SOURCE[0]}"
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"

VENV=$DIR/venv
if [ -d $VENV ]; then
        echo "Enable venv " && source $VENV/bin/activate
else
        echo "No venv, run init_venv.sh first"
        exit 1
fi

[ -f $DIR/conf/env.sh ] && source $DIR/conf/env.sh || echo "No $DIR/conf/env.sh"

export ETH_TOOLS_DIR=$DIR

mkdir -p $DIR/cache
mkdir -p $DIR/data
mkdir -p $DIR/output

cd $DIR

file=$1
if [ -z $1 ]; then
        echo "No target file, start python CLI"
        python
elif [ -f $file ]; then
        python $@
else
        echo "File $file not exist, start as shell command"
        which $1
        eval "$@"
fi

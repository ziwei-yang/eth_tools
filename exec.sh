#!/bin/bash --login
SOURCE="${BASH_SOURCE[0]}"
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"

file=$1
[ ! -f $file ] && echo "No target $1" && exit 1

VENV=$DIR/../venv
[ -d $VENV ] && echo "Enable venv " && source $VENV/bin/activate

[ -f $DIR/conf/env.sh ] && source $DIR/conf/env.sh || echo "No $DIR/conf/env.sh"

export ETH_TOOLS_DIR=$DIR

mkdir -p $DIR/cache
mkdir -p $DIR/data

python $@

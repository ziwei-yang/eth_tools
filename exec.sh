#!/bin/bash --login
SOURCE="${BASH_SOURCE[0]}"
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"

file=$1
[ -f $file ] || exit 1

source $DIR/bin/activate
[ -f $DIR/conf/env.sh ] && source $DIR/conf/env.sh || echo "No $DIR/conf/env.sh"

python $@

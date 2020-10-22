#!/bin/bash --login
SOURCE="${BASH_SOURCE[0]}"
DIR="$( cd -P "$( dirname "$SOURCE" )" && pwd )"

remote=zwyang.site
addr=$1
[ -z $addr ] && echo "No args" && exit 1

log=$DIR/output/holder.$addr.log
html=$DIR/output/holder.$addr.html
[ ! -f $log ] && echo "No file $log" && exit 1

ansi2html=$HOME/Proj/linux-setup/util/ansi2html.sh
[ ! -f $ansi2html ] && echo "No ansi2html $ansi2html" && exit 1

echo "Converting $log"
cat $log | $ansi2html --palette=solarized-xterm --bg=dark > $html
[[ $? != 0 ]] && echo "Failed in converting $log" && exit 1

echo "Uploading $html"
scp $html $remote:/var/nginx/www/
[[ $? != 0 ]] && echo "Failed in uploading $log" && exit 1

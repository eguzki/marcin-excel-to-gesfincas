#!/bin/bash

# stop if any statement returns non-true value
set -e

get_abs_path()
{
    if [ -d $1 ] ; then
        # It's a dir
        local PARENT_DIR="$1"
        echo "`cd $PARENT_DIR; pwd`"
    else 
        # It's a file
        local PARENT_DIR=$(dirname "$1")
        echo "`cd $PARENT_DIR; pwd`/$(basename $1)"
    fi
}

usage() 
{
    cat << EOF
Usage: `basename $0` [-v] [-e encoding] comunidad.csv numcom"

This script parses csv data filename and converts to Gesfincas format

OPTIONS
 -h Show this message
 -v verbose mode
 -e encoding. Ex. latin1, utf8
EOF
    exit $E_BADARGS
} 

CURR_DIR=$(get_abs_path `pwd`)
LOG_LEVEL="info"
ENCODING="latin1"

while getopts "vf:e:h" opt; do
    case $opt in
        v)
            LOG_LEVEL="debug"
            ;;
        e)
            ENCODING=$OPTARG
            ;;
        h)
            usage
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            usage
            ;;
    esac
done

# Change index to read script operands
shift $((OPTIND-1)); OPTIND=1

if [ "X$1" =  "X" ]
then
    echo "libraplus data filename missing" >&2
    usage
fi

if [ "X$2" =  "X" ]
then
    echo "numcom missing" >&2
    usage
fi

DATA_FILE=$(get_abs_path $1)

NUMCOMU=$2

# Create log directory

WORKSPACE=$(get_abs_path `dirname "$0"`)

OUTPUT_DIR="${CURR_DIR}/OUTPUT_`date +%Y.%m.%d-%H.%M.%S`"

echo "log_level: $LOG_LEVEL"
echo "encoding: $ENCODING"
echo "data_file: $DATA_FILE"
echo "output_file: $OUTPUT_DIR"

cd $WORKSPACE
python workspace/converter.py -l $LOG_LEVEL -e $ENCODING -o $OUTPUT_DIR $DATA_FILE $NUMCOMU


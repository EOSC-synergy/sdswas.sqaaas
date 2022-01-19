#!/bin/bash

if [ "$1" == "" ]; then
    mod="eventlet"
else
    mod=$1
fi

if [ "$2" == "" ]; then
    workers=17
else
    workers=$2
fi

TODAY=$(date "+%Y%m%d")
PYTHON_EXEC=${HOME}/dust-dashboard/bin/
DASH_HOME=${HOME}/interactive-forecast-viewer
LOGDIR=${DASH_HOME}/log/gunicorn/
CONNECTIONS=120

echo -n "Shutting down current service ... "
kill `ps auxww | grep 9000 | grep gunicorn | awk '{ printf $2" "}'`
wait
echo "done."

echo -n "Starting new service with class $mod and workers $workers ... "
cd $DASH_HOME
${PYTHON_EXEC}/gunicorn \
    --error-logfile ${LOGDIR}/${TODAY}.error.log \
    --access-logfile ${LOGDIR}/${TODAY}.access.log \
    --capture-output --log-level debug \
    -w $workers --preload \
        --threads `expr $workers - 1` \
    --worker-class=$mod \
    --worker-connections=100 \
    -b bscesdust03.bsc.es:9000 \
    dash_server:server -D
wait
echo "done".
#    --max-requests 100 \
#    --max-requests-jitter 10 \

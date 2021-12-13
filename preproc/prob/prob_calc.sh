#!/bin/bash

if [ "$1" == "" ]; then
    curdate=$(date +%Y%m%d -d '-1day')
else
    curdate=$1
fi

PYTHON=$HOME/dust-dashboard/bin/python

$PYTHON interpolateNetcdf.py $curdate
wait
$PYTHON probabilityMaps.py $curdate
wait

for var in /data/daily_dashboard/prob/{sconc_dust,od550_dust}
do
    for thresh in $var/*
	do
	    rm $thresh/geojson/$curdate/*geojson
            $PYTHON $HOME/interactive-forecast-viewer/preproc/nc2geojson.py PROB $thresh/geojson/ $thresh/netcdf/$curdate/$curdate*nc
	done
done

wait
rm /data/daily_dashboard/prob/tmp/interpolated/${curdate}*nc

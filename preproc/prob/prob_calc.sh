#!/bin/bash

if [ "$1" == "" ]; then
    curdate=$(date +%Y%m%d -d '-1day')
else
    curdate=$1
fi

python interpolateNetcdf.py $curdate
wait
python probabilityMaps.py $curdate
wait

for var in /data/daily_dashboard/prob/{sconc_dust,od550_dust}
do
    for thresh in $var/*
	do
	    rm $thresh/geojson/$curdate/*geojson
	    $HOME/dust-dashboard/bin/python $HOME/interactive-forecast-viewer/preproc/nc2geojson.py PROB $thresh/geojson/ $thresh/netcdf/$curdate/$curdate*nc
	done
done

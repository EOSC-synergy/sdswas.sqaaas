#!/usr/bin/env bash

# generate daily maps for each model and for the whole ensamble
# usage: script.sh [MODEL] [ENSEMBLE] [ANIM]

if [ "$1" != "" ]; then
    model="$1"
else
    model="all"
fi

if [ "$2" != "" ]; then
    ensemble="$2"
else
    ensemble="false"
fi

if [ "$3" != "" ]; then
    anim="$3"
else
    anim="true"
fi

if [ "$4" != "" ]; then
    curvar="$4"
else
    curvar="all"
fi

curdate=`date '+%Y%m%d' -d '-1day'`
curyear=`date '+%Y' -d '-1day'`
curmon=`date '+%m' -d '-1day'`
repodir='/data/daily_dashboard/comparison/'

for var in od550_dust sconc_dust dust_depd dust_depw dust_load dust_ext_sfc
do
	variable=$var
	echo "************ $model $ensemble $anim $curvar $variable ****************"
	if [ "$curvar" != "$variable" ] && [ "$curvar" != "all" ]; then
		continue
	fi
	tmpdir=${HOME}/tmp/${var}
	mkdir -p $tmpdir
	rm -Rf $tmpdir/*
	if [ "$variable" != "od550_dust" ] && [ "$variable" != "sconc_dust" ]; then
	    model="monarch"
	    node js/create_model_loop.js $anim $model $curdate ${variable^^}
	    wait
	    sleep 1
	    convert -loop 0 -delay 25 ${tmpdir}/${curdate}_${model}_??.png ${tmpdir}/${curdate}_${model}_loop.gif
	    currepo=${repodir}/${model}/${variable}/${curyear}/${curmon}/
	    mkdir -p $currepo
	    wait
	    mv ${tmpdir}/${curdate}_${model}_* $currepo

	elif [ "$model" == "all" ]; then
	    for mod in `cat interactive-forecast-viewer/conf/models.json | grep '": {' | sed 's/^.*"\(.*\)".*$/\1/g'`
		do
		    node js/create_model_loop.js $anim $mod $curdate ${variable^^}
		    wait
	    	    sleep 1
		    convert -loop 0 -delay 25 ${tmpdir}/${curdate}_${mod}_??.png ${tmpdir}/${curdate}_${mod}_loop.gif
		    currepo=${repodir}/${mod}/${variable}/${curyear}/${curmon}/
		    mkdir -p $currepo
		    wait
		    mv ${tmpdir}/${curdate}_${mod}_* $currepo
		done
	else
	    node js/create_model_loop.js $anim $model $curdate ${variable^^}
	    wait
	    sleep 1
	    convert -loop 0 -delay 25 ${tmpdir}/${curdate}_${model}_??.png ${tmpdir}/${curdate}_${model}_loop.gif
	    currepo=${repodir}/${model}/${variable}/${curyear}/${curmon}/
	    mkdir -p $currepo
	    wait
	    mv ${tmpdir}/${curdate}_${model}_* $currepo
	fi

	if [ "$ensemble" == "true" ]; then
	    model="all"
	    node js/create_model_loop.js $anim $model $curdate ${variable^^}
	    wait
	    sleep 1
	    convert -loop 0 -delay 25 ${tmpdir}/${curdate}_${model}_??.png ${tmpdir}/${curdate}_${model}_loop.gif
	    currepo=${repodir}/${model}/${variable}/${curyear}/${curmon}/
	    mkdir -p $currepo
	    wait
	    mv ${tmpdir}/${curdate}_${model}_* $currepo
	fi
	wait
	sleep 1
done

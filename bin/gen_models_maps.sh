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
    ensemble="true"
fi

if [ "$3" != "" ]; then
    anim="$3"
else
    anim="true"
fi

if [ "$4" != "" ]; then
    var="$4"
else
    var="all"
fi

curdate=`date '+%Y%m%d' -d '-1day'`
curyear=`date '+%Y' -d '-1day'`
curmon=`date '+%m' -d '-1day'`
repodir='/data/daily_dashboard/comparison/'

if [ "$var" == "all" ]; then
    for var in od550_dust sconc_dust dust_depd dust_depw dust_load dust_ext_sfc
    do
	tmpdir=${HOME}/tmp/${var}
	mkdir -p $tmpdir
        variable=$var
        if [ "$variable" != "od550_dust" ] && [ "$variable" != "sconc_dust" ]; then
            model="monarch"
            node js/create_model_loop.js $anim $model $curdate ${variable^^}
            wait
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
                    convert -loop 0 -delay 25 ${tmpdir}/${curdate}_${mod}_??.png ${tmpdir}/${curdate}_${mod}_loop.gif
                    currepo=${repodir}/${mod}/${variable}/${curyear}/${curmon}/
                    mkdir -p $currepo
                    wait
                    mv ${tmpdir}/${curdate}_${mod}_* $currepo
                done
        else
            node js/create_model_loop.js $anim $model $curdate ${variable^^}
            wait
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
            convert -loop 0 -delay 25 ${tmpdir}/${curdate}_${model}_??.png ${tmpdir}/${curdate}_${model}_loop.gif
            currepo=${repodir}/${model}/${variable}/${curyear}/${curmon}/
            mkdir -p $currepo
            wait
            mv ${tmpdir}/${curdate}_${model}_* $currepo
        fi
    done
fi

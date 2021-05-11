#!/bin/sh

DATE1=$(date +"%Y%m%d")
YYYY1=$(date +"%Y")
MM1=$(date +"%m")
DD1=$(date +"%d")

DATE=$(date +"%Y%m%d" -d "-1 day")
YYYY=$(date +"%Y" -d "-1 day")
MM=$(date +"%m" -d "-1 day")
DD=$(date +"%d" -d "-1 day")

echo $DATE1
echo $DATE
rm -rvf ncModelFiles/*.nc
#DATE="20180726"
#YYYY="2018"
#MM="07"
#DD="26"

WG=' -q --user ewernerh@aemet.es --password Aemet304 --auth-no-challenge --no-check-certificate sds-was.aemet.es/forecast-products/dust-forecasts/files-download/'
WG=' -P ./ncModelFiles/ -q --user ewernerh@aemet.es --password Aemet304 --auth-no-challenge --no-check-certificate sds-was.aemet.es/forecast-products/dust-forecasts/files-download/'

listOfModels="
nmmb-bsc/$YYYY/$MM/${DATE}12_3H_NMMB-BSC.nc
noa-wrf-chem/$YYYY/$MM/${DATE}12_NOA-WRF-CHEM.nc
bsc-dream8b-v2/$YYYY/$MM/${DATE}_BSC_DREAM8b_V2.nc
macc-ecmwf/$YYYY/$MM/${DATE}00_3H_MACC-ECMWF.nc
nasa-geos-5/$YYYY/$MM/${DATE}_NASA-GEOS.nc
dream-nmme-macc/$YYYY/$MM/${DATE}00_3H_DREAM8-MACC.nc
silam/$YYYY/$MM/${DATE}00_SILAM.nc
ema-regcm4/$YYYY/$MM/${DATE}_EMA-RegCM4.nc
lotos-euros/$YYYY/$MM/${DATE}00_3H_LOTOSEUROS.nc
uk-met-office-um/$YYYY/$MM/${DATE}00_3H_UKMET.nc
ncep-ngac/$YYYY/$MM/${DATE}_NCEP-NGAC.nc
icon-art/$YYYY/$MM/${DATE}00_ICON-ART.nc
"
#ncep-ngac/$YYYY/$MM/${DATE}_NCEP-NGAC.nc Not being downloaded due to poor performance
echo $string |cut -d';' -f1 | read str1
echo "download RUNNING..."
for modelName in $listOfModels
do
  #mod=$(echo $modelName |cut -d '/' -f 1)
  echo wget $WG$modelName
  wget $WG$modelName
  echo $modelName
done

#Change the _FillValue for NOA model to prevent error
ncatted  -a _FillValue,,m,f,-1.0e36 ncModelFiles/${DATE}12_NOA-WRF-CHEM.nc
#rename od550_dust in NMMB-BSC model
ncrename -v od550_dust,OD550_DUST ncModelFiles/${DATE}12_3H_NMMB-BSC.nc
ncrename -v sconc_dust,SCONC_DUST ncModelFiles/${DATE}12_3H_NMMB-BSC.nc
#Choose the steps runtime 12
cdo -seltimestep,1/21 ncModelFiles/${DATE}12_3H_NMMB-BSC.nc ncModelFiles/NMMB-BSC.nc
cdo -seltimestep,1/21 ncModelFiles/${DATE}12_NOA-WRF-CHEM.nc ncModelFiles/NOA-WRF-CHEM.nc
cdo -seltimestep,1/21 ncModelFiles/${DATE}_BSC_DREAM8b_V2.nc ncModelFiles/BSC_DREAM8b_V2.nc
#Choose the steps runtime 00
cdo -seltimestep,5/25 ncModelFiles/${DATE}00_3H_MACC-ECMWF.nc ncModelFiles/MACC-ECMWF.nc
cdo -seltimestep,5/25 ncModelFiles/${DATE}_NASA-GEOS.nc ncModelFiles/NASA-GEOS.nc
cdo -seltimestep,5/25 ncModelFiles/${DATE}_NCEP-NGAC.nc ncModelFiles/NCEP-NGAC.nc
cdo -seltimestep,5/25 ncModelFiles/${DATE}00_3H_DREAM8-MACC.nc ncModelFiles/DREAM8-MACC.nc
cdo -seltimestep,5/25 ncModelFiles/${DATE}00_SILAM.nc ncModelFiles/SILAM.nc
cdo -seltimestep,5/25 ncModelFiles/${DATE}_EMA-RegCM4.nc ncModelFiles/EMA-RegCM4.nc
cdo -seltimestep,5/25 ncModelFiles/${DATE}00_3H_LOTOSEUROS.nc ncModelFiles/LOTOSEUROS.nc
cdo -seltimestep,5/25 ncModelFiles/${DATE}00_3H_UKMET.nc ncModelFiles/UKMET.nc
cdo -seltimestep,5/25 ncModelFiles/${DATE}00_ICON-ART.nc ncModelFiles/ICON-ART.nc
#Change longitudes in NCEP-NGAC.nc (0 360 into 0 180 0 -180)
cdo -O sellonlatbox,-180,180,-90,90 ncModelFiles/NCEP-NGAC.nc ncModelFiles/NCEP-NGACok.nc
rm -rvf ncModelFiles/NCEP-NGAC.nc
#remove nc files
rm -rvf ncModelFiles/${YYYY}*.nc



echo "download DONE!"


#wget  -q --user ggarciacastrillor@aemet.es --password Canalejas55 --auth-no-challenge sds-was.aemet.es/forecast-products/dust-forecasts/files-download/nmmb-bsc-dust-public/2018/07/2018070212_3H_NMMB-BSC.nc/view

#https://sds-was.aemet.es/forecast-products/dust-forecasts/files-download/nmmb-bsc/2018/07/2018070512_3H_NMMB-BSC.nc/view
#https://sds-was.aemet.es/forecast-products/dust-forecasts/files-download/bsc-dream8b-v2/2018/07/20180704_BSC_DREAM8b_V2.nc/view
#https://sds-was.aemet.es/forecast-products/dust-forecasts/files-download/macc-ecmwf/2018/07/2018070300_3H_MACC-ECMWF.nc/view
#https://sds-was.aemet.es/forecast-products/dust-forecasts/files-download/nasa-geos-5/2018/07/20180704_NASA-GEOS.nc/view
#https://sds-was.aemet.es/forecast-products/dust-forecasts/files-download/ncep-ngac/2018/07/20180704_NCEP-NGAC.nc/view
#https://sds-was.aemet.es/forecast-products/dust-forecasts/files-download/noa-wrf-chem/2018/07/2018070412_NOA-WRF-CHEM.nc/view
#https://sds-was.aemet.es/forecast-products/dust-forecasts/files-download/dream-nmme-macc/2018/07/2018070400_3H_DREAM8-MACC.nc/view
#https://sds-was.aemet.es/forecast-products/dust-forecasts/files-download/silam/2018/07/2018070400_SILAM.nc/view
#https://sds-was.aemet.es/forecast-products/dust-forecasts/files-download/icon-art/2021/01/2021013100_ICON-ART.nc/view
# NOT INCLUDED (not working since 06/2018)
#https://sds-was.aemet.es/forecast-products/dust-forecasts/files-download/dreamabol/2018/06/20180629_DREAMABOL.nc/view
#dreamabol/$YYYY/$MM/${DATE}_DREAMABOL.nc

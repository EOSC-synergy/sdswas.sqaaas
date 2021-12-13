#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import subprocess
from glob import glob

class InterpolateNetcdf(object):

    def __init__(self, curdate, ncModelsDir, main_output_path, lonlat):

        dates = curdate
        inputFileDir = os.listdir(ncModelsDir)
        scriptClean =   "rm -rvf "+main_output_path+"/*.nc"
        subprocess.call(scriptClean, shell=True)
        for ifileDir in inputFileDir:
            if ifileDir == 'NMMB-BSC':
                tpl = '*OPER.nc'
            elif ifileDir == 'median':
                tpl = '*MEDIAN.nc'
            else:
                tpl = '*.nc'
            print (ifileDir)
            for ifile in glob('{}/archive/{}{}'.format('/data/products/'+ifileDir, dates, tpl)):
                if os.path.exists(main_output_path+"interpolated/"+os.path.basename(ifile)):
                    print(main_output_path+"interpolated/"+os.path.basename(ifile), 'exists. Exit.')
                    continue
                script =  "cdo -L -s -sellonlatbox,"+lonlat+" -remapbil,global_0.5  "+ifile+" "+main_output_path+"interpolated/"+os.path.basename(ifile)
                print (script)
                subprocess.call(script, shell=True)

if __name__=="__main__":
    import sys
    #ncModelsDir = "/home/administrador/webpolvo/DustEpsgrams/ncModelFiles/"
    ncModelsDir = "/data/thredds/models-repos/"
    #LonW, LonE, LatN, LatS
    lonlatRegional = "-25,60,5,65"
    main_output_path = '/data/daily_dashboard/prob/tmp/'
    curdate = sys.argv[1]
    InterpolateNetcdf(curdate, ncModelsDir, main_output_path, lonlatRegional)

#     lonlatCanarias = "-21,-5,22,32"
#     main_output_path = 'InterpolatedNcModelFiles/Canarias/'
#     InterpolateNetcdf(ncModelsDir, main_output_path, lonlatCanarias)
# 
#     lonlatEuropa = "-25,42,30,65"
#     main_output_path = 'InterpolatedNcModelFiles/Europa/'
#     InterpolateNetcdf(ncModelsDir, main_output_path, lonlatEuropa)
# 
#     lonlatSahel = "-20,20,5,28"
#     main_output_path = 'InterpolatedNcModelFiles/Sahel/'
#     InterpolateNetcdf(ncModelsDir, main_output_path, lonlatSahel)
# 
#     lonlatSahara = "-13,-5,21,29"
#     main_output_path = 'InterpolatedNcModelFiles/Sahara/'
#     InterpolateNetcdf(ncModelsDir, main_output_path, lonlatSahara)
    #12º49´30.61    12.82527778
    #5º57´08.84     5.95250000

    #28º11´00.23N   28.18333333
    #21º13´06.62N   21.21861111

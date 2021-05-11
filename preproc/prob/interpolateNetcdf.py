#!/usr/bin/python
# -*- coding: utf-8 -*-

import os

class InterpolateNetcdf(object):

    def __init__(self, ncModelsDir, main_output_path, lonlat):

        inputFileList = os.listdir(ncModelsDir)
        scriptClean =   "rm -rvf "+main_output_path+"/*.nc"
        subprocess.call(scriptClean, shell=True)
        print (inputFileList)
        for ifile in inputFileList:
            script =  "cdo -s -sellonlatbox,"+lonlat+" -remapbil,global_0.5  "+ncModelsDir+ifile+" "+main_output_path+"interpolated"+ifile
            print (script)
            subprocess.call(script, shell=True)

if __name__=="__main__":

    #ncModelsDir = "/home/administrador/webpolvo/DustEpsgrams/ncModelFiles/"
    ncModelsDir = "../DustEpsgrams/ncModelFiles/"
    #LonW, LonE, LatN, LatS
    lonlatRegional = "-25,60,0,65"
    main_output_path = 'InterpolatedNcModelFiles/Regional/'
    InterpolateNetcdf(ncModelsDir, main_output_path, lonlatRegional)

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

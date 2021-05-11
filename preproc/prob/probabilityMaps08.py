#!/usr/bin/python
# -*- coding: utf-8 -*-
#import pdb; pdb.set_trace()

import netCDF4
from scipy.interpolate import interp2d
import pickle
import numpy as np
import pandas as pd
import os
import sys
import shutil
import datetime as dt

# ProbabilityMaps class plots probability maps for D+1 and D+2 daily
# maximum of a given parameter (AOD and "SCONC_DUST") from a interpolated
# netcdf file and needs: inputDir, outputDir, parameterName, threshold
# (The Domain is defined previously in the netcdf file)
# doIt method needs: conversionFactor, units, parameterNameTitle (title figure)

class ProbabilityMaps(object):

    def __init__(self, mWDict, inputDir, outputDir, parameterName, threshold):
        self._mWDict = mWDict
        self._inputDir = inputDir
        self._outputDir = outputDir
        self._parameterName = parameterName
        self._threshold = threshold
    @property
    def mWDict (self):
        return self._mWDict
    @property
    def inputDir (self):
        return self._inputDir
    @property
    def outputDir (self):
        return self._outputDir
    @property
    def parameterName (self):
        return self._parameterName
    @property
    def threshold (self):
        return self._threshold

    def doIt(self, conversionFactor, units, parameterNameTitle):
        # Getting parameter from nc files
        parameterMax24ProbList = []
        parameterMax48ProbList = []
        parameterMean24ProbList = []
        parameterMean48ProbList = []
        inputFileList = os.listdir(self.inputDir)
        print ("inputFileList...", inputFileList)
        weightSum= 0.
        for f in inputFileList:
            key = '_'.join(f.split('_')[-2:])
            if key not in self.mWDict:
                continue
            print(f, "Weight", self.mWDict[key])
            weight = self.mWDict[key]
            weightSum += weight
            f = self.inputDir+f
            #ff = netCDF4.MFDataset(f)
            ff = netCDF4.Dataset(os.path.join(inputDir, f))  # , format="NETCDF3")
            #print (ff.variables.keys())
            if self.parameterName not in ff.variables:
                parameterValues = ff.variables[self.parameterName.lower()][:]
            else:
                parameterValues = ff.variables[self.parameterName][:]
            lon = ff.variables["lon"][:]
            lat = ff.variables["lat"][:]
            steps = ff.variables["time"][:]
            runTime =  ff.variables['time'].units.split()[2:]
            #print (runTime)
            #print (steps)
            # Calculates parameter daily maximum for D1, from 24 to 48
            # Calculates parameter daily mean for D1, from 24 to 48
            # (steps are 12 15 18 21...24 27 30 33 36 39 42 45...)
            # Slicing an array:  a[start:end+1]
            # parameterArray has [step,lat,lon]
            parameterMax24 = parameterValues[4,:,:] #first step 24 hours
            parameterMean24 = parameterValues[4,:,:] #first step 24 hours
            for m in parameterValues[5:12,:,:]:
                parameterMax24 = np.maximum(parameterMax24, m)
                parameterMean24 = parameterMean24+m
            parameterMean24 = parameterMean24/len(parameterValues[4:12,:,:])
            # Change matrix values to true/false when exceding the given threshold
            # and when *1 to 1/0 this way matrixs can be added.
            parameterMax24Prob = (parameterMax24 >self.threshold*conversionFactor)*1*weight
            parameterMax24ProbList.append(np.array(parameterMax24Prob))
            parameterMean24Prob = (parameterMean24 > self.threshold*conversionFactor)*1*weight
            parameterMean24ProbList.append(np.array(parameterMean24Prob))
            #print (parameterMean24ProbList)
            # Calculates parameter daily maximum for D2, from 48 to 69
            # (steps are 48 51 54 57 60 63 66 69...72)
            parameterMax48 = parameterValues[12,:,:]
            parameterMean48 = parameterValues[12,:,:]
            for m in parameterValues[13:20,:,:]:
                parameterMax48 = np.maximum(parameterMax48, m)
                parameterMean48 = parameterMean48+m
            parameterMean48 = parameterMean48/len(parameterValues[12:20,:,:])
            # Change matrix values to true/false when exceding the given threshold
            # and when *1 to 1/0 this way matrixs can be added.
            parameterMax48Prob = (parameterMax48 >self.threshold*conversionFactor)*1*weight
            parameterMax48ProbList.append(np.array(parameterMax48Prob))
            parameterMean48Prob = (parameterMean48 >self.threshold*conversionFactor)*1*weight
            parameterMean48ProbList.append(np.array(parameterMean48Prob))
        ff.close()
        print ("Done reading nc files")
        # We add all the matrix for each model
        # and divide by the number of models to get probability
        print ("weightSum", weightSum)
        print ("runTime0", runTime[0])
        # and then plotting the maps
        ######parameterMaxProbListList = [parameterMax24ProbList, parameterMax48ProbList]
        parameterMaxProbListList = [parameterMean24ProbList, parameterMean48ProbList]
        D  = dt.datetime.strptime(runTime[0],"%Y-%m-%d")
        D1 = dt.datetime.strptime(runTime[0],"%Y-%m-%d") + dt.timedelta(days=1)
        D2 = dt.datetime.strptime(runTime[0],"%Y-%m-%d") + dt.timedelta(days=2)
        D1s = str(D1.day).zfill(2) +"/"+ str(D1.month).zfill(2) + "/" +str(D1.year)
        D2s = str(D2.day).zfill(2) +"/"+ str(D2.month).zfill(2) + "/" +str(D2.year)
        Ds  = str(D.day).zfill(2) +"/"+ str(D.month).zfill(2) + "/" +str(D.year)
        dayForecastList = ["D+1", "D+2"] #this is for the image file name
        DDMMYYYYList = [D1s, D2s]

        for parameterMaxProbList, dayForecast, DDMMYYYY in zip(parameterMaxProbListList, dayForecastList, DDMMYYYYList):
            result1=np.array(parameterMaxProbList[0])
            dataListLen = np.array(parameterMaxProbList).shape[0]
            for m in range(1, dataListLen):
                result1=result1+parameterMaxProbList[m]
            #data1=100*result1/float(dataListLen)
            data1=100*result1/weightSum

            # dataframe to NETCDF #############################################
            print (len(data1), len(data1[0]))
            print ("lon:", len(lon))
            print ("lat:", len(lat))
            # lat, lon, prob must have same lenght
            # np.tile(a, n) repeats an array "a" "n" times: [[a],[a],...]
            # Ex: a = [1,2,3]
            # flatten reduce to 1 dimension by rows: [1,2,3,1,2,3,...]
            # flatten('F') reduce to 1 dimension by columns:  [1,1,1,2,2,2,...]
            # default format is NETCDF4
            # format {"NETCDF4", "NETCDF4_CLASSIC", "NETCDF3_64BIT", "NETCDF3_CLASSIC"}
            print (self.parameterName)
            ##we can ad after 'lon': 'time': ["23/03/2021"]*(len(lat)*len(lon)),
            ##https://stackoverflow.com/questions/57006443/how-do-i-add-the-time-to-the-netcdf-file
            df_multiindex = pd.DataFrame({'time':[D1]*(len(lat)*len(lon)),
                                           'lat': np.tile(lat,(len(lon),1)).flatten('F'),
                                           'lon': np.tile(lon,len(lat)),
                                            self.parameterName+"_P"+str(threshold): np.array(data1).flatten() })
            df_multiindex = df_multiindex.set_index(['time','lat','lon'])
            xr = df_multiindex.to_xarray()
            print (df_multiindex)
            print(xr)
            xr.to_netcdf("{}{}{}_{}_Prob{}.nc".format(str(D.year),
                str(D.month).zfill(2), str(D.day).zfill(2), self.parameterName,
                str(threshold)))
                # +'_'+self.parameterName+'_Prob'+str(threshold)+'_Canarias.nc')

            #sys.exit(0) ########

#     	    # Plotting the maps
#             print ("Start plotting!")
# 
#             fig = plt.figure( figsize=(16, 13) )
#             m = Basemap(projection='cyl',lat_ts=10,llcrnrlon=lon.min(),
#             urcrnrlon=lon.max(),llcrnrlat=lat.min(),urcrnrlat=lat.max(),
#             resolution='i')
# 
#     		# color palette AEMET Prova3
#             colourList = (  (1,1,1),                                            \
#                             (225/255.0,225/255.0,225/255.0),                    \
#                             (205/255.0,205/255.0,205/255.0),                    \
#                             (190/255.0,255/255.0, 51/255.0),                    \
#                             (162/255.0,220/255.0, 51/255.0),                    \
#                             (255/255.0,255/255.0,155/255.0),                    \
#                             (255/255.0,255/255.0, 75/255.0),                    \
#                             (255/255.0,210/255.0, 64/255.0),                    \
#                             (255/255.0,139/255.0, 90/255.0),                    \
#                             (255/255.0,102/255.0, 51/255.0)  )
# 
#             bounds=[0,10,20,30,40,50,60,70,80,90,100]
#             ticks =[0,10,20,30,40,50,60,70,80,90,100]
# 
#             cmap = LinearSegmentedColormap.from_list('my_colour',colourList)
#             cmap = cmap.from_list('Custom_cmap', colourList, N=cmap.N)
#             norm = BoundaryNorm(bounds, cmap.N)
#             m.imshow(data1,vmin=0, vmax=100,interpolation="bilinear",cmap=cmap, norm=norm)
#             # m_pkl = pickle.dumps(m) # Question for Francesco!!
#             cb = m.colorbar(ticks=ticks[1:], location='right', boundaries=bounds[1:])
#             cb.ax.set_yticklabels(ticks[1:], fontsize=17)
#             cb.ax.set_ylabel('Probability', fontsize = 24)
#             m.drawcountries()
#             m.drawcoastlines()
#             #m.drawmapboundary()
#             # Add a colorbar and title, and then show the plot.
#             # Nor the data nor the domain are in the image file name
#             # image names are like this: D+?_probability_PARAMETER_THRESHOLD.png
#             # ex: D+1_probability_SCONC_DUST_100.png -> 100 is the THRESHOLD!
#             # Domain and data are direcories
#             # path to images is: ./images/Canarias/20190621 -> images/DOMAIN/DATA
#             '''
#             plt.title("Daily Maximum of "+r"$\bf{"+parameterNameTitle+"}$"+
#             "\nProbability of exceeding "+r"$\bf{"+str(threshold)+"}$"+" "+units+
#             "\nENS members: "+r"$\bf{"+str(dataListLen)+"}$"+" Run: "+D+" Valid for: "+r"$\bf{"+DDMMYYYY+"}$"+"\n", fontsize=24)
#             plt.savefig(self.outputDir+dayForecast+"_probability_"+parameterName+"_"+str(threshold)+".png",bbox_inches="tight")
#             print ("Saving plot...", self.outputDir+dayForecast+"_probability_"+parameterName+"_"+str(threshold)+".png")
#             plt.close()
#             '''
#             plt.title("Daily Mean of "+r"$\bf{"+parameterNameTitle+"}$"+
#             "\nProbability of exceeding "+r"$\bf{"+str(threshold)+"}$"+" "+units+
#             "\nENS members: "+r"$\bf{"+str(dataListLen)+"}$"+" Run: "+D+" Valid for: "+r"$\bf{"+DDMMYYYY+"}$"+"\n", fontsize=24)
#             plt.savefig(self.outputDir+dayForecast+"_probability_"+parameterName+"_"+str(threshold)+".png",bbox_inches="tight")
#             print ("Saving plot...", self.outputDir+dayForecast+"_probability_"+parameterName+"_"+str(threshold)+".png")
#             plt.close()


if __name__ == "__main__":
    # makes daily directories where the maps will be stored #before 20200715: Sahel_prova...
    today = dt.datetime.today().strftime('%Y%m%d')
    print (today)
    # clean OLD Directories
#     try:
#         y = dt.datetime.today()- dt.timedelta(days=30)
#         yesterday = y.strftime('%Y%m%d')
#         outputDirToRemoveList = [ "./images/SahelMean/"+yesterday+"/",
#                                   "./images/EuropaMean/"+yesterday+"/",
#                                   "./images/RegionalMean/"+yesterday+"/",
#                                   "./images/CanariasMean/"+yesterday+"/",
#                                   "./images/SaharaMean/"+yesterday+"/" ]
#         for dirToRemove in outputDirToRemoveList:
#              shutil.rmtree(dirToRemove)
#              print ("Dir removed:", dirToRemove)
#     except:
#         e = sys.exc_info()[0]
#         print ("Dir to remove not found", e)
# 
#     outputDirList = [ "./images/SahelMean/"+today+"/",
#                       "./images/EuropaMean/"+today+"/",
#                       "./images/RegionalMean/"+today+"/",
#                       "./images/CanariasMean/"+today+"/",
#                       "./images/SaharaMean/"+today+"/" ]
# 
#     for outputDir in outputDirList:
#         if not os.path.exists( outputDir ):
#             os.mkdir( outputDir )

    allModelNameList = ['BSC_DREAM8b_V2', 'DREAM8-MACC', 'EMA-RegCM4',
                        'LOTOSEUROS',     'MACC-ECMWF',  'NASA-GEOS',
                        'NCEP-NGAC',    'NMMB-BSC',    'NOA-WRF-CHEM',
                        'SILAM',          'UKMET',       'ICON-ART' ]

    allModelNameListInterpolated = ["{}_interp.nc".format(mod) for mod in allModelNameList]
    #[0.3, 0.3,    0.1, 1,    0.3, 1,    0.3, 1, 1,      0.3, 1 ]
    weightListDustSfcConc = [1, 1, 0.1,
                             1, 1, 1,
                             1, 1, 1,
                             1, 1, 1]

    weightListAod =         [1., 1., 0.1,
                             1., 1., 1.,
                             1., 1., 1.,
                             1., 1., 1. ]

    modelWeightAodDict = dict(zip(allModelNameListInterpolated, weightListAod))
    modelWeightDustSfcConcDict = dict(zip(allModelNameListInterpolated, weightListDustSfcConc))

    #print (modelWeightAodDict)
    #print (modelWeightDustSfcConcDict)

#     # Probability Maps for Canarias SCONC_SFC
#     # Input threshold Canarias
#     thresholdList = [20,35,50,75,100,150,250,350,450,500,600,800,1000]
#     conversionFactor = 10**-9
#     units = u"\u03bcg/m3"
#     # Input parameter-netcdf-name
#     parameterName = "SCONC_DUST"
#     # Title uses spaces in mathematical mode
#     # (https://es.overleaf.com/learn/latex/Spacing_in_math_mode -> \:)
#     parameterNameTitle = "Dust\: SFC\: Concentration"
#     # Input nc files
#     inputDir = "./InterpolatedNcModelFiles/Canarias/"
#     modelWeightDict = modelWeightDustSfcConcDict
#     for threshold in thresholdList:
#         ProbabilityMaps(modelWeightDict, inputDir, outputDirList[3], parameterName, threshold).doIt(conversionFactor, units, parameterNameTitle)
# 
#     # Probability Maps for Canarias AOD
#     # Input threshold Canarias
#     thresholdList = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
#     conversionFactor = 1
#     units = ""
#     # Input parameter-netcdf-name
#     parameterName = "OD550_DUST"
#     parameterNameTitle = "Dust\: AOD"
#     # Input nc files
#     inputDir = "./InterpolatedNcModelFiles/Canarias/"
#     modelWeightDict = modelWeightAodDict
#     for threshold in thresholdList:
#         ProbabilityMaps(modelWeightDict, inputDir, outputDirList[3], parameterName, threshold).doIt(conversionFactor, units, parameterNameTitle)
    # Probability Maps for Regional SCONC_SFC
    # Input threshold Regional
    thresholdList = [20, 35, 50, 75, 100, 150, 200, 250, 350, 400, 450, 500, 600, 800, 1000]
    conversionFactor = 10**-9
    units = u"\u03bcg/m3"
    # Input parameter-netcdf-name
    parameterName = "SCONC_DUST"
    parameterNameTitle = "Dust\: SFC\: Concentration"
    # Input nc files
    inputDir = "/data/interactive_test/prob/tmp_current/"
    for threshold in thresholdList:
        ProbabilityMaps(modelWeightDustSfcConcDict, inputDir, "", parameterName, threshold).doIt(conversionFactor, units, parameterNameTitle)
    # Probability Maps for Regional AOD
    # Input threshold Regional
    thresholdList = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
    conversionFactor = 1
    units = ""
    # Input parameter-netcdf-name
    parameterName = "OD550_DUST"
    parameterNameTitle = "Dust\: AOD"
    # Input nc files
    inputDir = "/data/interactive_test/prob/tmp_current/"
    for threshold in thresholdList:
        ProbabilityMaps(modelWeightAodDict, inputDir, "", parameterName, threshold).doIt(conversionFactor, units, parameterNameTitle)
#     # Probability Maps for Europa SCONC_SFC
#     # Input threshold Europa
#     thresholdList = [20,35,50,75,100,150,250,350,450,500,600,800,1000]
#     conversionFactor = 10**-9
#     units = u"\u03bcg/m3"
#     # Input parameter-netcdf-name
#     parameterName = "SCONC_DUST"
#     parameterNameTitle = "Dust\: SFC\: Concentration"
#     # Input nc files
#     inputDir = "./InterpolatedNcModelFiles/Europa/"  #Title uses spaces in mathematical mode
#     for threshold in thresholdList:
#         ProbabilityMaps(modelWeightDustSfcConcDict, inputDir, outputDirList[1], parameterName, threshold).doIt(conversionFactor, units, parameterNameTitle)
# 
#     # Probability Maps for Sahel SCONC_SFC
#     # Input threshold Sahel
#     thresholdList = [20,35,50,75,100,150,250,350,450,500,600,800,1000]
#     conversionFactor = 10**-9
#     units = u"\u03bcg/m3"
#     # Input parameter-netcdf-name
#     parameterName = "SCONC_DUST"
#     parameterNameTitle = "Dust\: SFC\: Concentration"
#     # Input nc files
#     inputDir = "./InterpolatedNcModelFiles/Sahel/"  #Title uses spaces in mathematical mode
#     for threshold in thresholdList:
#         ProbabilityMaps(modelWeightDustSfcConcDict, inputDir, outputDirList[0], parameterName, threshold).doIt(conversionFactor, units, parameterNameTitle)
# 
#     # Probability Maps for Sahara SCONC_SFC
#     # Input threshold Sahara
#     thresholdList = [20,35,50,75,100,150,250,350,450,500,600,800,1000]
#     conversionFactor = 10**-9
#     units = u"\u03bcg/m3"
#     # Input parameter-netcdf-name
#     parameterName = "SCONC_DUST"
#     parameterNameTitle = "Dust\: SFC\: Concentration"
#     # Input nc files
#     inputDir = "./InterpolatedNcModelFiles/Sahara/"  #Title uses spaces in mathematical mode
#     for threshold in thresholdList:
#         ProbabilityMaps(modelWeightDustSfcConcDict, inputDir, outputDirList[4], parameterName, threshold).doIt(conversionFactor, units, parameterNameTitle)

    ################################################ Cleaning
#     try:
#         y = dt.datetime.today()- dt.timedelta(days=1)
#         print ("removing old dir")
#         yesterday = y.strftime('%Y%m%d')
#         shutil.rmtree(dirToRemove)
#         outputDirToRemove ="/home/admin/webpolvo/ProbabilityMaps/images/"
#         outputDirToRemoveList = [ outputDirToRemove+"SahelMean/"+yesterday+"/",
#                                   outputDirToRemove+"EuropaMean/"+yesterday+"/",
#                                   outputDirToRemove+"RegionalMean/"+yesterday+"/",
#                                   outputDirToRemove+"SaharaMean/"+yesterday+"/",
#                                   outputDirToRemove+"CanariasMean/"+yesterday+"/" ]
#         for dirToRemove in outputDirToRemoveList:
#              shutil.rmtree(dirToRemove)
#              print ("dir removed: ", dirToRemove)
#     except:
#         e = sys.exc_info()[0]
#         print (e)

# -*- coding: utf-8 -*-
# Copyright 2016 Earth Sciences Department, BSC-CNS
#

"""nc2geojson module.

This module provide conversion from netCDF to geojson format.

"""

import netCDF4 as nc
import numpy as np
import json
import jsonator
import os
import os.path
import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta

np.set_printoptions(precision=2)

CURRENT_PATH = os.path.abspath(os.path.dirname(__file__))

# DATATYPE = ''


def nc2geojson(datatype='', outdir='.', filelist=[], outfile_tpl=''):
    """ NetCDF(s) to geojson converter """

    VARS = json.load(open(os.path.join(CURRENT_PATH, '../conf/vars.json')))

    print("Converting netCDF(s) with DATATYPE ...", datatype)
    if datatype == 'MODIS':
        # MODIS
        bounds = VARS['OD550_DUST']['bounds'] 
        mul = 1
        VARS = ['od550aero',]
    elif datatype == 'PROB':
        # PROBABILITY MAPS
        bounds = range(10, 110, 10)
        mul = 1  #None
    else:
        bounds = None
        mul = None

    outfiles = []

    print('xxx MUL', mul)
    print('xxx bounds', bounds)

    if isinstance(filelist, str):
        # file is global
        filelist = [filelist]

    # loop over files
    for filename in filelist:
        print("current file %s", filename)
        fp = nc.Dataset(filename)
        tim = fp.variables['time']
        timevals = tim[:].copy()
        try:
            what, _, date, _ = tim.units.split()[:4]
        except:
            print("File", filename, "time units exception. Skipping.")
            continue
        if what.lower() == 'hours':
            date = datetime.strptime(date, "%Y-%m-%d") + relativedelta(hours=int(timevals[0]))
        elif what.lower() == 'days':
            date = datetime.strptime(date, "%Y-%m-%d") + relativedelta(days=int(timevals[0]))
        else:
            date = datetime.strptime(date, "%Y-%m-%d")

        newdate = date.strftime("%Y%m%d")
        if 'lat' in fp.variables:
            lats = np.round(fp.variables['lat'][:], decimals=2)
            lons = np.round(fp.variables['lon'][:], decimals=2)
        else:
            lats = np.round(fp.variables['latitude'][:], decimals=2)
            lons = np.round(fp.variables['longitude'][:], decimals=2)

        for variable in VARS:

            print('VARIABLE', variable)

#            if datatype not in ('MODIS', 'PROB') and VARS[variable]['models'] != 'all':
#                print('continue-1')
#                continue

            if variable not in fp.variables and variable.lower() not in fp.variables:
                print('continue-2')
                continue

            print('MUL', mul)
            if mul is None:
                mult = VARS[variable]['mul']
            else:
                mult = mul

            if bounds is None:
                levels = VARS[variable]['bounds']
            else:
                levels = bounds

            print('MULT', mult)
            print('BOUNDS', levels)

            # loop over timesteps
            for t, m in enumerate(timevals):

                outfile = '{:02d}_{}_{}.geojson'.format(t, newdate.lower(),
                                                        variable)
                newdir = os.path.join(outdir, newdate)
                newfile = os.path.join(newdir, outfile)
                if os.path.exists(newfile) and os.path.getsize(newfile) > 42:
                    print("File", newfile, "already exists. Skipping.")
                    continue

                features = []

                try:
                    current_var = fp.variables[variable]
                except:
                    current_var = fp.variables[variable.lower()]

                values = current_var[t]*mult

                # metadata = {
                #    'value': values,
                #    # 'fill' : fill,
                # }

                geojson = jsonator.contourf(lons, lats, values,
                                            levels=levels,
                                            cmap=None)

                if geojson:
                    features.append(geojson)

                if features:
                    merged = json.loads(features[0]).copy()
                    for feat in features[1:]:
                        merged['features'] += json.loads(feat)['features']

                    outfiles.append(outfile)
                    try:
                        os.makedirs(newdir)
                    except:
                        pass
                    with open(os.path.join(newdir, outfile), 'w') as out:
                        out.write(json.dumps(merged, separators=(',', ':')))

        fp.close()


if __name__ == "__main__":
    datatype = sys.argv[1]
    outdir = sys.argv[2]
    filenames = sys.argv[3:]
    print('outdir', outdir)
    print('fnames', filenames)
    nc2geojson(datatype, outdir, filenames)

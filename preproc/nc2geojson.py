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

np.set_printoptions(precision=2)

CURRENT_PATH = os.path.abspath(os.path.dirname(__file__))

VARS = json.load(open('../conf/vars.json'))
VARS = ['SCONC_DUST',]
BOUNDS = range(10, 110, 10)

def nc2geojson(outdir='.', filelist=[], outfile_tpl=''):
    """ NetCDF(s) to geojson converter """

    print("Converting netCDF(s) ...")
    outfiles = []

    if isinstance(filelist, str):
        # file is global
        filelist = [filelist]

    # loop over files
    for filename in filelist:
        print("current file %s", filename)
        fp = nc.Dataset(filename)
        tim = fp.variables['time']
        timevals = tim[:].copy()
        _, _, date, _ = tim.units.split()[:4]
        newdate = datetime.strptime(date, "%Y-%m-%d").strftime("%Y%m%d")
        if 'lat' in fp.variables:
            lats = np.round(fp.variables['lat'][:], decimals=2)
            lons = np.round(fp.variables['lon'][:], decimals=2)
        else:
            lats = np.round(fp.variables['latitude'][:], decimals=2)
            lons = np.round(fp.variables['longitude'][:], decimals=2)

        for variable in VARS:

            mul = 1  # VARS[variable]['mul']
            levels = BOUNDS  # VARS[variable]['bounds']

            # loop over timesteps
            for t, m in enumerate(timevals):

                features = []

                current_var = fp.variables[variable]

                values = current_var[t]*mul

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

                    outfile = '{:02d}_{}_{}.geojson'.format(t, newdate.lower(),
                                                            variable)
                    outfiles.append(outfile)
                    newdir = os.path.join(outdir, newdate)
                    try:
                        os.makedirs(newdir)
                    except:
                        pass
                    with open(os.path.join(newdir, outfile), 'w') as out:
                        out.write(json.dumps(merged, separators=(',', ':')))

        fp.close()


if __name__ == "__main__":
    outdir = sys.argv[1]
    filenames = sys.argv[2:]
    print('outdir', outdir)
    print('fnames', filenames)
    nc2geojson(outdir, filenames)

#!/usr/bin/env python
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

np.set_printoptions(precision=2)

CURRENT_PATH = os.path.abspath(os.path.dirname(__file__))

BOUNDS = [.1, .2, .4, .8, 1.2, 1.6, 3.2, 6.4, 10]

VARIABLES = ['od550_dust']

COLORS = None   # ['#a1ede3', '#5ce3ba', '#fcd775', '#da7230',
                # '#9e6226', '#714921', '#392511', '#1d1309']


def nc2geojson(filelist, outdir='.', outfile_tpl=''):
    """ NetCDF(s) to geojson converter """

    print("Converting netCDF(s) ...")
    outfiles = []

    levels = np.array(BOUNDS)  # arange(25, 115, 15)

    if isinstance(filelist, str):
        # file is global
        filelist = [filelist]

    # check time, lat and lon details from the first file
    with nc.Dataset(filelist[0]) as f0:
        tim = f0.variables['time']
        timevals = tim[:].copy()
        _, _, date, _ = tim.units.split()[:4]

    # loop over timesteps
    for t, m in enumerate(timevals):

        # loop over files
        for filename in filelist:
            print("current file %s", filename)
            fp = nc.Dataset(filename)
            lats = np.round(fp.variables['lat'][:], decimals=2)
            lons = np.round(fp.variables['lon'][:], decimals=2)

            for variable in VARIABLES:

                features = []

                current_var = fp.variables[variable]

                values = current_var[t]

                # metadata = {
                #    'value': values,
                #    # 'fill' : fill,
                # }

                geojson = jsonator.contourf(lons, lats, values,
                                            levels=levels,
                                            cmap=COLORS)

                if geojson:
                    features.append(geojson)

                if features:
                    merged = json.loads(features[0]).copy()
                    for feat in features[1:]:
                        merged['features'] += json.loads(feat)['features']

                    outfile = '{:02d}_{}_{}.geojson'.format(t, date.lower(),
                                                            variable)
                    outfiles.append(outfile)
                    with open(os.path.join(outdir, outfile), 'w') as out:
                        out.write(json.dumps(merged, separators=(',', ':')))

            fp.close()


if __name__ == "__main__":
    filenames = sys.argv[1]
    nc2geojson(filenames.split(','))

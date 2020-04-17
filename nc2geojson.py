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

VARS = json.load(open('conf/vars.json'))


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
        lats = np.round(fp.variables['lat'][:], decimals=2)
        lons = np.round(fp.variables['lon'][:], decimals=2)

        for variable in VARS:

            mul = VARS[variable]['mul']
            levels = VARS[variable]['bounds']

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

                    outfile = '{:02d}_{}_{}.geojson'.format(t, date.lower(),
                                                            variable)
                    outfiles.append(outfile)
                    with open(os.path.join(outdir, outfile), 'w') as out:
                        out.write(json.dumps(merged, separators=(',', ':')))

        fp.close()


if __name__ == "__main__":
    outdir = sys.argv[1]
    filenames = sys.argv[2:]
    print('outdir', outdir)
    print('fnames', filenames)
    nc2geojson(outdir, filenames)

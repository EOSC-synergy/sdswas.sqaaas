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

COLORS = ['#a1ede3', '#5ce3ba', '#fcd775', '#da7230',
          '#9e6226', '#714921', '#392511', '#1d1309']

BOUNDS = [.1, .2, .4, .8, 1.2, 1.6, 3.2, 6.4]

VARIABLES = ['od550_dust']


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

#         start_date = datetime.strptime("{} {}".format(date, hour), self.date_format_orig)
#         current_date = start_date + relativedelta(months=int(m))
#         year, month = current_date.strftime("%Y %b").split()
#         self.log.info("CURRENT DATE %s %s", year, month)
#         if t == len(timevals)-1:
#             mdiff = int(m - timevals[t-1])
#         else:
#             mdiff = int(timevals[t+1] - m)
#         sdate = current_date.strftime(self.date_format)
#         edate = (current_date + relativedelta(months=mdiff) -
#                  relativedelta(days=1)).strftime(self.date_format)
# 
#         files_start.append(datetime.strptime(sdate, self.date_format)
#                            .strftime(self.date_format_new))
#         files_end.append(datetime.strptime(edate, self.date_format)
#                          .strftime(self.date_format_new))

        # loop over files
        for filename in filelist:
            print("current file %s", filename)
            fp   = nc.Dataset(filename)
            lats = np.round(fp.variables['lat'][:], decimals=2)
            lons = np.round(fp.variables['lon'][:], decimals=2)

#             properties = {
#                 'title': title,
#                 'description': description,
#             }

            for variable in VARIABLES:

                features = []

                current_var = fp.variables[variable]

                values = current_var[t]

                metadata = {
                    'value': values,
                    # 'fill' : fill,
                }

                geojson = jsonator.contourf(lons, lats, values,
                                              levels=levels,
                                              # gridded_metadata=metadata,
                                              # properties={},
                                              )
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

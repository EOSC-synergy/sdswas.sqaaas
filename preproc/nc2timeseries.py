#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2021 Earth Sciences Department, BSC-CNS

""" Save time series """

import xarray as xr
import numpy as np
import json
import os
import sys
from datetime import datetime
from glob import glob


CURRENT_PATH = os.path.abspath(os.path.dirname(__file__))

VARS = json.load(open(os.path.join(CURRENT_PATH, '../conf/vars.json')))
MODELS = json.load(open(os.path.join(CURRENT_PATH, '../conf/models.json')))
OBS = json.load(open(os.path.join(CURRENT_PATH, '../conf/obs.json')))


def preprocess(ds, n=8):
    """keep only the first N timestep for each file"""
    return ds.isel(time=range(n))


def convert2timeseries(model, fmt='feather', months=None):
    """ Convert data from daily netCDF to time series """

    path = os.path.join(MODELS[model]['path'], 'netcdf', '{}.nc'.format(MODELS[model]['template']))
    dest = './tmp/{}-{}'.format(model, fmt)
    # dest = os.path.join(MODELS[model]['path'], fmt)

    if not os.path.exists(dest):
        os.makedirs(dest)

    if not months:
        curr_year = str(datetime.now().year)
        months = np.arange(int("{}01".format(curr_year)),
                int("{}12".format(curr_year)))

    paths = ["{}/{}*{}".format(os.path.dirname(path), month, os.path.basename(path)) for month in months]

    for cpath, month in zip(paths, months):
        fnames = glob(cpath)
        if not fnames:
            print('No files correspondence to path', cpath)
            continue

        try:
            ds = xr.open_mfdataset(cpath,
                                   concat_dim='time',
                                   combine='nested',
                                   preprocess=preprocess)
        except Exception as err:
            print('Error', str(err))
            continue

        for variable in VARS:
            print('variable', variable)
            fname = "{}-{}-{}".format(month, model, variable)
            if variable in ds.variables:
                print('converting to df with name {} ...'.format(fname))
                variable_df = ds[variable].to_dataframe()
                if fmt == 'parquet':
                    print('saving to parquet ...')
                    variable_df.to_parquet(
                        '{}/{}.parquet.gzip'.format(dest, fname),
                        compression='gzip')
                elif fmt == 'feather':
                    print('reset index ...')
                    var_df = variable_df.astype('float32').reset_index()
                    print('saving to feather ...')
                    var_df.to_feather(
                        '{}/{}.ft'.format(dest, fname),
                        )

        ds.close()


if __name__ == "__main__":
    if len(sys.argv) > 4:
        print("Error. Usage: {} [MONTHS] [MODEL] [FORMAT]".format(sys.argv[0]))
        sys.exit(1)
    if len(sys.argv) == 1:
        for model in MODELS:
            convert2timeseries(model)
    elif len(sys.argv) == 2:
        months = sys.argv[1].split(",")
        for model in MODELS:
            convert2timeseries(model, months=months)
    elif len(sys.argv) == 3:
        months = sys.argv[1].split(",")
        model = sys.argv[2]
        convert2timeseries(model, months=months)
    else:
        months = sys.argv[1].split(",")
        model = sys.argv[2]
        fmt = sys.argv[3]
        convert2timeseries(model, fmt, months)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2016 Earth Sciences Department, BSC-CNS

""" Save time series """

import xarray as xr
import json
import os
import sys


VARS = json.load(open('conf/vars.json'))
MODELS = json.load(open('conf/models.json'))


def preprocess(ds, n=8):
    """keep only the first N timestep for each file"""
    return ds.isel(time=range(n))


def convert2timeseries(model, fmt='feather'):
    """ Convert data from daily netCDF to time series """

    path = os.path.join(MODELS[model]['path'], 'netcdf', '*{}*.nc4'.format(MODELS[model]['template']))
    dest = os.path.join(MODELS[model]['path'], fmt)

    if not os.path.exists(dest):
        os.makedirs(dest)

    ds = xr.open_mfdataset(path,
                           concat_dim='time',
                           preprocess=preprocess,
                           parallel=True)

    for variable in VARS:
        print('variable', variable)
        if variable in ds.variables:
            print('converting to df ...')
            variable_df = ds[variable].to_dataframe()
            if fmt == 'parquet':
                print('saving to parquet ...')
                variable_df.to_parquet(
                    '{}/{}.parquet.gzip'.format(dest, variable),
                    compression='gzip')
            elif fmt == 'feather':
                print('saving to feather ...')
                variable_df.reset_index(inplace=True)
                variable_df.to_feather(
                    '{}/{}.ft'.format(dest, variable),
                    )


if __name__ == "__main__":
    if len(sys.argv) > 3:
        print("Error. Usage: {} [MODEL] [FORMAT]".format(sys.argv[0]))
        sys.exit(1)
    if len(sys.argv) == 1:
        for model in MODELS:
            convert2timeseries(model)
    elif len(sys.argv) == 2:
        model = sys.argv[1]
        convert2timeseries(model)
    else:
        fmt = sys.argv[2]
        convert2timeseries(model, fmt)

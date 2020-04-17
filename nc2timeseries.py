#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2016 Earth Sciences Department, BSC-CNS

""" Save time series """

import xarray as xr
import json
import sys


VARS = json.load(open('conf/vars.json'))


def preprocess(ds, n=8):
    """keep only the first N timestep for each file"""
    return ds.isel(time=range(n))


def convert2timeseries(path, fmt='feather'):
    """ Convert data from daily netCDF to time series """
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
                    'data/{}/{}.parquet.gzip'.format(fmt, variable),
                    compression='gzip')
            elif fmt == 'feather':
                print('saving to feather ...')
                variable_df.reset_index(inplace=True)
                variable_df.to_feather(
                    'data/{}/{}.ft'.format(fmt, variable),
                    )


if __name__ == "__main__":
    if len(sys.argv) > 3:
        print("Error. Usage: {} <PATH> [FORMAT]".format(sys.argv[0]))
        sys.exit(1)
    path = sys.argv[1]
    if len(sys.argv) == 2:
        convert2timeseries(path)
    else:
        fmt = sys.argv[2]
        convert2timeseries(path, fmt)

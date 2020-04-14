#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Save time series """

import xarray as xr
import json
import sys


VARS = json.load(open('conf/vars.json'))


def preprocess(ds, n=8):
    """keep only the first N timestep for each file"""
    return ds.isel(time=range(n))


def convert2timeseries(path, fmt='parquet'):
    """ Convert data from daily netCDF to time series """
    ds = xr.open_mfdataset(path,
                           concat_dim='time',
                           preprocess=preprocess,
                           parallel=True)

    for variable in VARS:
        if variable in ds.variables:
            od550_dust_df = ds[variable].to_dataframe()
            od550_dust_df.to_parquet(
                'data/{}/{}.parquet.gzip'.format(fmt, variable),
                compression='gzip')


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Error. Usage: {} <PATH>".format(sys.argv[0]))
        sys.exit(1)
    path = sys.argv[1]
    convert2timeseries(path)

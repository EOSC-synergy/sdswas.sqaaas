#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2016 Earth Sciences Department, BSC-CNS

""" Save time series """

import xarray as xr
import numpy as np
import json
import os
import sys
from datetime import datetime
from glob import glob


VARS = json.load(open('../conf/vars.json'))
MODELS = json.load(open('../conf/models.json'))
OBS = json.load(open('../conf/obs.json'))


def preprocess(ds, n=8):
    """keep only the first N timestep for each file"""
    return ds.isel(time=range(n))


def convert2timeseries(model, obs, fmt='feather', months=None):
    """ Convert data from daily netCDF to time series """

    mod_path = os.path.join(MODELS[model]['path'], 'netcdf', '{}.nc'.format(MODELS[model]['template']))
    obs_path = os.path.join(OBS[obs]['path'], 'netcdf', '{}.nc'.format(OBS[obs]['template']))
    mod_dest = './tmp/{}-{}_interp'.format(model, fmt)
    obs_dest = './tmp/{}-{}_interp'.format(obs, fmt)
    # dest = os.path.join(MODELS[model]['path'], fmt)

    if not os.path.exists(mod_dest):
        os.makedirs(mod_dest)

    if not os.path.exists(obs_dest):
        os.makedirs(obs_dest)

    if not months:
        curr_year = str(datetime.now().year)
        months = np.arange(int("{}01".format(curr_year)),
                int("{}12".format(curr_year)))

    mod_paths = ["{}/{}*{}".format(os.path.dirname(mod_path), month, os.path.basename(mod_path)) for month in months]
    obs_paths = ["{}".format(obs_path).format(month) for month in months]

    for mpath, opath, month in zip(mod_paths, obs_paths, months):
        fnames = glob(mpath)
        if not fnames:
            print('No files correspondence to path', cpath)
            continue

        try:
            mod_ds = xr.open_mfdataset(mpath,
                                   concat_dim='time',
                                   combine='nested',
                                   preprocess=preprocess)
        except Exception as err:
            print('Error', str(err))
            continue

        try:
            obs_ds = xr.open_dataset(opath)
        except Exception as err:
            print('Error', str(err))
            continue

        for variable in VARS:
            print('v', variable)
            print('o', OBS[obs]['mod_var'])
            if OBS[obs]['mod_var'] != variable:
                continue
            print('observation', OBS[obs]['obs_var'])
            fname = "{}-{}-{}_interp".format(month, obs, variable)
            variable_df = obs_ds[OBS[obs]['obs_var']].to_dataframe()
            if fmt == 'parquet':
                print('saving to parquet ...')
                variable_df.to_parquet(
                    '{}/{}.parquet.gzip'.format(obs_dest, fname),
                    compression='gzip')
            elif fmt == 'feather':
                print('reset index ...')
                var_df = variable_df.astype('float32').reset_index()
                print('saving to feather ...')
                var_df.to_feather(
                    '{}/{}.ft'.format(obs_dest, fname),
                    )
            print('variable', variable)
            fname = "{}-{}-{}_interp".format(month, model, variable)
            if variable in mod_ds.variables:
                print('interpolating to observations ...')
                try:
                    mod_interp = mod_ds[variable].interp(longitude=obs_ds['longitude'], latitude=obs_ds['latitude'])
                except:
                    mod_interp = mod_ds[variable].interp(lon=obs_ds['longitude'], lat=obs_ds['latitude'])
                print('converting to df with name {} ...'.format(fname))
                variable_df = mod_interp.to_dataframe()
                if fmt == 'parquet':
                    print('saving to parquet ...')
                    variable_df.to_parquet(
                        '{}/{}.parquet.gzip'.format(mod_dest, fname),
                        compression='gzip')
                elif fmt == 'feather':
                    print('reset index ...')
                    var_df = variable_df.astype('float32').reset_index()
                    print('saving to feather ...')
                    var_df.to_feather(
                        '{}/{}.ft'.format(mod_dest, fname),
                        )

        mod_ds.close()
        obs_ds.close()


if __name__ == "__main__":
    if len(sys.argv) > 4:
        print("Error. Usage: {} [MONTHS] [MODEL] [OBS] [FORMAT]".format(sys.argv[0]))
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
    elif len(sys.argv) == 4:
        months = sys.argv[1].split(",")
        model = sys.argv[2]
        obs = sys.argv[3]
        convert2timeseries(model, obs, months=months)
    else:
        months = sys.argv[1].split(",")
        model = sys.argv[2]
        obs = sys.argv[3]
        fmt = sys.argv[4]
        convert2timeseries(model, obs, fmt, months)

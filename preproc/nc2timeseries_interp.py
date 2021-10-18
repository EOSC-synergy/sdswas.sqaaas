#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2021 Earth Sciences Department, BSC-CNS

""" Save time series """

import xarray as xr
import numpy as np
import pandas as pd
import json
import os
import sys
from datetime import datetime
from glob import glob


CURRENT_PATH = os.path.abspath(os.path.dirname(__file__))

VARS = json.load(open(os.path.join(CURRENT_PATH, '../conf/vars.json')))
MODELS = json.load(open(os.path.join(CURRENT_PATH, '../conf/models.json')))
OBS = json.load(open(os.path.join(CURRENT_PATH, '../conf/obs.json')))

DTYPE = 'float32'


def save_to_timeseries(df, fname, dest, fmt='feather'):
    df = df.to_dataframe()
    print(df)
    dest = os.path.join(dest, fname)
    if fmt == 'parquet':
        print('saving to parquet ...')
        df.to_parquet(
            '{}.parquet.gzip'.format(dest),
            compression='gzip')
    elif fmt == 'feather':
        print('reset index ...')
        var_df = df.astype(DTYPE).reset_index()
        print('saving to feather ...')
        var_df.to_feather(
            '{}.ft'.format(dest),
            )


def preprocess(ds, n=8):
    """keep only the first N timestep for each file"""
    return ds.isel(time=range(n))


def convert2timeseries(model, obs=None, fmt='feather', months=None):
    """ Convert data from daily netCDF to time series or interpolated observations timeseries """

    mod_path = os.path.join(MODELS[model]['path'], 'netcdf', '{}.nc'.format(MODELS[model]['template']))
    # dest = os.path.join(MODELS[model]['path'], fmt)
#    mod_dest = './tmp/{}-{}_interp'.format(model, fmt)
#    if not os.path.exists(mod_dest):
#        os.makedirs(mod_dest)

    if obs:
        obs_path = os.path.join(OBS[obs]['path'], 'netcdf', '{}.nc'.format(OBS[obs]['template']))
        obs_dest = os.path.join(OBS[obs]['path'], fmt)  # , '{}-{}_interp'.format(obs, fmt)
        mod_dest = obs_dest
        if not os.path.exists(obs_dest):
            os.makedirs(obs_dest)

    if not months:
        curr_year = str(datetime.now().year)
        months = np.arange(int("{}01".format(curr_year)),
                int("{}12".format(curr_year)))

    mod_paths = ["{}/{}*{}".format(os.path.dirname(mod_path), month, os.path.basename(mod_path)) for month in months]

    print(obs_path, months, obs)
    obs_paths = [obs_path.format(OBS[obs]['obs_var'], month)
            if obs else ''
            for month in months]

    for mpath, opath, month in zip(mod_paths, obs_paths, months):
        fnames = glob(mpath)
        if not fnames:
            print('No files correspondence to path', mpath)
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
            obs_ds = None
            if opath:
                obs_ds = xr.open_dataset(opath)
                if obs_ds:
                    if 'longitude' in obs_ds.variables:
                        obs_lon = 'longitude'
                        obs_lat = 'latitude'
                    else:
                        obs_lon = 'lon'
                        obs_lat = 'lat'
                if obs == 'aeronet':
                    sites = pd.read_table(os.path.join('../conf/',
                        OBS[obs]['sites']), delimiter=r"\s+", engine='python')

                    print(obs_ds['station_name'])
                    idxs, station_names = np.array([[idx, st_name.data.tobytes().decode('utf-8').rstrip(' \t\r\n\0')]
                                          for idx, st_name in
                                          enumerate(obs_ds['station_name'])
                                          if st_name.data.tobytes().decode('utf-8').rstrip(' \t\r\n\0').upper() in map(str.upper, sites['SITE'])]
                                          ).T
                    idxs = idxs.astype(int)
                else:
                    idxs = [(obs_ds[obs_lat]>-10) & (obs_ds[obs_lat]<65), (obs_ds[obs_lon]>-30) & (obs_ds[obs_lon]<70)]
                    print('******')
                    #print(idxs)
                    print('******')
        except Exception as err:
            print('Error', str(err))
            continue

        for variable in VARS:
            print('v', variable)
            # if observation perform interpolation
            if opath:
                print('o', OBS[obs]['mod_var'])
                if OBS[obs]['mod_var'] != variable:
                    continue
                print('observation', OBS[obs]['obs_var'])
                fname = "{}-{}-{}_interp".format(month, obs, variable)
                fpath = os.path.join(obs_dest, fname)
                if not os.path.exists(fpath):
                    if obs == 'aeronet':
                        save_to_timeseries(obs_ds[OBS[obs]['obs_var']][:, idxs], fname, obs_dest, fmt)
                    else:
                        save_to_timeseries(obs_ds[OBS[obs]['obs_var']][:, idxs[0], :][:, :, idxs[1]], fname, obs_dest, fmt)
            print('variable', variable)
            for var in mod_ds.variables:
                if var.upper() != variable:
                    continue
                fname = "{}-{}-{}_interp".format(month, model, variable)
                fpath = os.path.join(obs_dest, fname) + '.ft'
                print('-----', fpath)
                if obs_ds:
                    print('interpolating to observations ...')
                    mod_da = mod_ds[var].dropna('time', 'all')
                    if obs == 'aeronet':
                        if 'longitude' in mod_ds.variables:
                            mod_interp = mod_da.interp(longitude=obs_ds[obs_lon][idxs], latitude=obs_ds[obs_lat][idxs])
                        else:
                            mod_interp = mod_da.interp(lon=obs_ds[obs_lon][idxs], lat=obs_ds[obs_lat][idxs])
                    else:
                        if 'longitude' in mod_ds.variables:
                            mod_interp = mod_da.interp(longitude=obs_ds[obs_lon][idxs[1]], latitude=obs_ds[obs_lat][idxs[0]])
                        else:
                            mod_interp = mod_da.interp(lon=obs_ds[obs_lon][idxs[1]], lat=obs_ds[obs_lat][idxs[0]])
                    print('converting to df with name {} ...'.format(fname))
                else:
                    mod_interp = mod_ds[var]
                    print('converting dataset to df ...')
                print(mod_interp.shape)
                mod_interp = mod_interp.dropna('time', 'all')
                print(mod_interp.shape)
                save_to_timeseries(mod_interp, fname, obs_dest, fmt)

        if obs_ds:
            obs_ds.close()
        mod_ds.close()


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
        print(months, model, obs)
        convert2timeseries(model, obs, months=months)
    else:
        months = sys.argv[1].split(",")
        model = sys.argv[2]
        obs = sys.argv[3]
        fmt = sys.argv[4]
        convert2timeseries(model, obs, fmt, months)

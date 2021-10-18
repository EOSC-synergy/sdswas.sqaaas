#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2021 Earth Sciences Department, BSC-CNS

""" Save time series """

import xarray as xr
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error
import json
import os
import sys
from datetime import datetime
from glob import glob
from collections import OrderedDict


CURRENT_PATH = os.path.abspath(os.path.dirname(__file__))

VARS = json.load(open(os.path.join(CURRENT_PATH, '../conf/vars.json')))
MODELS = json.load(open(os.path.join(CURRENT_PATH, '../conf/models.json')))
OBS = json.load(open(os.path.join(CURRENT_PATH, '../conf/obs.json')))

DTYPE = 'float32'

STATS = OrderedDict({ 'bias': 'BIAS', 'corr': 'CORR', 'rmse': 'RMSE', 'frge': 'FRGE', 'totn': 'CASES' })


def save_to_timeseries(df, fname, dest, fmt='feather'):
    df = df.to_dataframe()
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
    if (ds.time[4]-ds.time[0])/1e9/3600 == np.array(24, dtype='timedelta64[ns]'):
        n = 4
    return ds.isel(time=range(n))


def ret_scores(mod_da, obs_da):
    decs = 2
    try:
        bias = np.nanmean(mod_da - obs_da).round(decimals=decs).astype(str)
    except:
        bias = '-'
    try:
        corr = np.ma.corrcoef(np.ma.masked_invalid(mod_da).flatten(), np.ma.masked_invalid(obs_da).flatten()).data[0,1].round(decimals=decs).astype(str)
    except:
        corr = '-'
    try:
        obs_da_m = np.ma.masked_invalid(obs_da)
        mod_da_m = np.ma.masked_invalid(mod_da)
        rmse = mean_squared_error(obs_da_m[~(obs_da_m.mask+mod_da_m.mask)].flatten(), mod_da_m[~(obs_da_m.mask+mod_da_m.mask)].flatten(), squared=True).round(decimals=decs).astype(str)
    except:
        rmse = '-'
    try:
        frge_arr = np.abs(2*((mod_da_m[~(mod_da_m.mask+obs_da_m.mask)] - obs_da_m[~(mod_da_m.mask+obs_da_m.mask)])))
        if frge_arr.size == 0:
            frge = '-'
        else:
            frge = np.nanmean(frge_arr).round(decimals=decs).astype(str)
    except:
        frge = '-'
    try:
        print(";;;", obs_da_m[~(mod_da_m.mask+obs_da_m.mask)].size)
        totn = str(obs_da_m[~(mod_da_m.mask+obs_da_m.mask)].size)
    except:
        totn = '0'
    return {'bias':  bias, 'corr': corr, 'rmse': rmse, 'frge': frge, 'totn': totn}


def convert2timeseries(model, obs=None, months=None):
    """ Convert data from daily netCDF to time series or interpolated observations timeseries """

    if isinstance(model, str):
        model = [model]

    # paths of all models
    mods_path = [os.path.join(MODELS[mod]['path'], 'netcdf', '{}.nc'.format(MODELS[mod]['template'])) for mod in model]

    if obs:
        obs_path = os.path.join(OBS[obs]['path'], 'netcdf', '{}.nc'.format(OBS[obs]['template']))

    if not months:
        curr_year = str(datetime.now().year)
        months = np.arange(int("{}01".format(curr_year)),
                int("{}12".format(curr_year)))

    # paths of all models per all months
    mod_paths = [["{}/{}*{}".format(os.path.dirname(mod_path), month, os.path.basename(mod_path)) for month in months] for mod_path in mods_path]

    obs_paths = [obs_path.format(OBS[obs]['obs_var'], month)
            if obs else ''
            for month in months]

    print("MOD", mod_paths)
    print("OBS", obs_paths)

    columns = ['model'] + list(STATS.keys())
    print(columns)
    total_df = pd.DataFrame(columns=columns)

    models_ds = []
    for mpath in mod_paths:
        fnames = [x for mp in mpath for x in sorted(glob(mp))]
        try:
            #print(fnames)
            mod_ds = xr.open_mfdataset(fnames,
                                   concat_dim='time',
                                   combine='nested',
                                   preprocess=preprocess)
            models_ds.append(mod_ds)
        except Exception as err:
            print('Error', str(err))
            continue

    try:
        # read observations and transform to a dataframe with only needed stations
        obs_ds = xr.open_mfdataset(obs_paths,
                               concat_dim='time',
                               combine='nested',
                               )

        # retrieve lat and lon only with 'station' dimension to perform the interpolation
        obs_lat = obs_ds['lat']
        obs_lon = obs_ds['lon']

    except Exception as err:
        print('Error', str(err))

    variable = OBS[obs]['mod_var']
    print('v', variable)
    # if observation perform interpolation
    print('mod var', OBS[obs]['mod_var'])
    print('obs var', OBS[obs]['obs_var'])

    print(models_ds)
    print(model)
    for mod_idx, (mod_ds, mod) in enumerate(zip(models_ds, model)):
        print('MOD', mod, 'IDX', mod_idx)
        if variable in mod_ds.variables:
            if obs_ds:
                print('interpolating to observations ...')
                try:
                    mod_interp = mod_ds[variable].interp(longitude=obs_lon, latitude=obs_lat)
                except:
                    mod_interp = mod_ds[variable].interp(lon=obs_lon, lat=obs_lat)
                print('converting to df  ...')
            else:
                mod_interp = mod_ds[variable]
                print('converting dataset to df ...')

            obs_timesteps = np.unique(obs_ds[OBS[obs]['obs_var']][obs_ds[OBS[obs]['obs_var']].time.isin(mod_interp.time)].time)
            print("timesteps", obs_timesteps, type(obs_timesteps))
            obs_da = obs_ds[OBS[obs]['obs_var']].sel(time=obs_timesteps)
            print(obs_da)
            mod_da = mod_interp.sel(time=obs_timesteps)
            print(mod_da)

            scores = ret_scores(mod_da, obs_da)
            scores.update({ 'model': mod })
            total_df.loc[mod_idx] = scores

            print(mod, scores)

    if obs_ds:
        obs_ds.close()
    mod_ds.close()

    if len(months) == 1:
        fname = "{}".format(months[0])
    else:
        fname = "{}-{}".format(months[0], months[-1])

    print("Writing h5 ...")
    total_df_out = os.path.join(OBS[obs]['path'], "h5", "{}_scores.h5")
    print("BIAS", total_df_out.format(fname))
    total_df.to_hdf(total_df_out.format(fname), "total_{}".format(fname), format='table')


if __name__ == "__main__":
    if len(sys.argv) > 4:
        print("Error. Usage: {} [MODEL] [OBS] [MONTHS]".format(sys.argv[0]))
        sys.exit(1)
    if len(sys.argv) == 1:
        # for model in MODELS:
        convert2timeseries(MODELS.keys(), obs='aeronet')
    elif len(sys.argv) == 2:
        model = sys.argv[1].split(',')
        if model[0] == 'all':
            model = MODELS.keys()
        convert2timeseries(model=model, obs='aeronet')
    elif len(sys.argv) == 3:
        model = sys.argv[1].split(',')
        if model[0] == 'all':
            model = MODELS.keys()
        obs = sys.argv[2]
        convert2timeseries(model, obs=obs)
    else:
        model = sys.argv[1].split(',')
        if model[0] == 'all':
            model = MODELS.keys()
        obs = sys.argv[2]
        months = sys.argv[3].split(",")
        convert2timeseries(model, obs=obs, months=months)

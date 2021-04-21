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


CURRENT_PATH = os.path.abspath(os.path.dirname(__file__))

VARS = json.load(open(os.path.join(CURRENT_PATH, '../conf/vars.json')))
MODELS = json.load(open(os.path.join(CURRENT_PATH, '../conf/models.json')))
OBS = json.load(open(os.path.join(CURRENT_PATH, '../conf/obs.json')))

DTYPE = 'float32'


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
    return ds.isel(time=range(n))


def ret_scores(mod, obs, flt, st):
    flt_stat = flt.get_group(st).set_index('time')
    try:
        obs_stat = obs.get_group(st).set_index('time')[flt_stat[OBS['aeronet']['flt_var']]>0.6]
    except:
        return flt_stat['station_name'][0], {'BIAS':  np.nan, 'CORR': np.nan, 'RMSE': np.nan, 'FRGE': np.nan}
    if obs_stat.size == 0:
        return flt_stat['station_name'][0], {'BIAS':  np.nan, 'CORR': np.nan, 'RMSE': np.nan, 'FRGE': np.nan}
    mod_stat = mod.get_group(st).set_index('time')
    tot = obs_stat.merge(mod_stat, on='time')
    mvar, ovar = OBS['aeronet']['mod_var'], OBS['aeronet']['obs_var']
    try:
        bias = (tot[mvar] - tot[ovar]).mean()
    except:
        bias = np.nan
    try:
        corr = tot[[ovar, mvar]].corr()
    except:
        corr = np.nan
    try:
        rmse = mean_squared_error(tot[ovar], tot[mvar], squared=False)
    except:
        rmse = np.nan
    try:
        frge = 2*((tot[mvar] - tot[ovar])/(tot[mvar] + tot[ovar])).abs().mean()
    except:
        frge = np.nan
    return obs_stat['station_name'][0], {'BIAS':  bias, 'CORR': corr.values[0][1], 'RMSE': rmse, 'FRGE': frge}


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

    flt_paths = [obs_path.format(OBS[obs]['flt_var'], month)
            if obs else ''
            for month in months]

    print("MOD", mod_paths)
    print("OBS", obs_paths)
    print("FLT", flt_paths)

    columns = ['station'] + list(MODELS.keys())
    print(columns)
    bias_df = pd.DataFrame(columns=columns)
    rmse_df = pd.DataFrame(columns=columns)
    corr_df = pd.DataFrame(columns=columns)
    frge_df = pd.DataFrame(columns=columns)

    sites = pd.read_table('/home/fbeninca/devel/interactive-forecast-viewer/conf/aeronet_sites.txt', delimiter=r"\s+", engine='python')

    # for mpath, opath, fpath, month in zip(*mod_paths, obs_paths, flt_paths, months):
    # for outputs in zip(*mod_paths, obs_paths, flt_paths, months):
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
        obs_ds = xr.open_mfdataset(obs_paths,
                               concat_dim='time',
                               combine='nested',
                               )
        obs_ds = obs_ds.where(obs_ds['station_name'].isin(sites['SITE'].values.astype(np.bytes_)))
        obs_df = obs_ds.to_dataframe().reset_index().dropna(subset=['station_name'])
        obs_df = obs_df[['time', 'station', 'ndata', 'station_name', OBS[obs]['obs_var']]]
        old_stations = obs_df['station'].unique()
        new_stations = np.arange(old_stations.size)
        for old_st, new_st in zip(old_stations, new_stations):
            obs_df.loc[obs_df['station'] == old_st, 'station'] = new_st
        obs_lat = obs_ds['latitude'].dropna('station')[0].drop_vars('time')
        obs_lon = obs_ds['longitude'].dropna('station')[0].drop_vars('time')
        obs_grps = obs_df.groupby('station')
        flt_ds = xr.open_mfdataset(flt_paths,
                               concat_dim='time',
                               combine='nested',
                               )
        flt_ds = flt_ds.where(flt_ds['station_name'].isin(sites['SITE'].values.astype(np.bytes_)))
        flt_df = flt_ds.to_dataframe().reset_index().dropna(subset=['station_name'])
        flt_df = flt_df[['time', 'station', 'ndata', 'station_name', OBS[obs]['flt_var']]]
        for old_st, new_st in zip(old_stations, new_stations):
            flt_df.loc[flt_df['station'] == old_st, 'station'] = new_st
        flt_grps = flt_df.groupby('station')
    except Exception as err:
        print('Error', str(err))

    variable = OBS[obs]['mod_var']
    print('v', variable)
    # if observation perform interpolation
    print('mod var', OBS[obs]['mod_var'])
    print('obs var', OBS[obs]['obs_var'])

    print(models_ds)
    for mod_idx, mod_ds in enumerate(models_ds):
        stations = []
        bias = []
        rmse = []
        corr = []
        frge = []
        print('IDX', mod_idx)
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

            mod_df = mod_interp.to_dataframe().reset_index()
            mod_grps = mod_df.groupby('station')

            for grp in mod_grps:
                station, scores = ret_scores(mod_grps, obs_grps, flt_grps, grp[0])
                stations.append(station)
                bias.append(scores['BIAS'])
                rmse.append(scores['RMSE'])
                corr.append(scores['CORR'])
                frge.append(scores['FRGE'])

        print(stations)
        print(columns[mod_idx+1])
        print('BIAS', bias)
        print('RMSE', rmse)
        print('CORR', corr)
        print('FRGE', frge)
        bias_df['station'] = stations
        bias_df[columns[mod_idx+1]] = bias
        rmse_df['station'] = stations
        rmse_df[columns[mod_idx+1]] = rmse
        corr_df['station'] = stations
        corr_df[columns[mod_idx+1]] = corr
        frge_df['station'] = stations
        frge_df[columns[mod_idx+1]] = frge

    if obs_ds:
        obs_ds.close()
    if flt_ds:
        flt_ds.close()
    mod_ds.close()

    print('BIAS', bias_df)


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

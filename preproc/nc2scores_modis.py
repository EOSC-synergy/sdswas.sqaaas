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


def ret_scores(mod_da, obs_da, axis=None):
    decs = 2
    obs_da_m = np.ma.masked_invalid(obs_da)
    mod_da_m = np.ma.masked_invalid(mod_da)
    try:
        bias = np.nanmean(mod_da - obs_da, axis=axis).round(decimals=decs).flatten().astype(str)
        if type(bias) in (list, np.ndarray) and len(bias) == 1:
            bias = bias[0]
    except Exception as err:
        print('BIAS ERROR', str(err))
        bias = '-'
    try:
        if axis is None:
            corr = np.ma.corrcoef(mod_da_m.flatten(), obs_da_m.flatten()).data[0,1].round(decimals=decs).astype(str)
        else:
            corr = xr.corr(mod_da, obs_da, dim='time').values.flatten().astype(str)
        if type(corr) in (list, np.ndarray) and len(corr) == 1:
            corr = corr[0]
    except Exception as err:
        print('CORR ERROR', str(err))
        corr = '-'
    try:
        if axis is None:
            rmse = mean_squared_error(obs_da_m[~(obs_da_m.mask+mod_da_m.mask)].flatten(), mod_da_m[~(obs_da_m.mask+mod_da_m.mask)].flatten(), squared=False).round(decimals=decs).astype(str)
        else:
            rmse = np.sqrt(np.square((obs_da - mod_da).mean(axis=axis))).values.flatten().astype(str)
        if type(rmse) in (list, np.ndarray) and len(rmse) == 1:
            rmse = rmse[0]
    except Exception as err:
        print('RMSE ERROR', str(err))
        rmse = '-'
    try:
        # frge_arr = np.abs(2*((mod_da_m[~(mod_da_m.mask+obs_da_m.mask)] - obs_da_m[~(mod_da_m.mask+obs_da_m.mask)])))
        frge_arr = np.abs(2*(obs_da - mod_da))
        if frge_arr.size == 0:
            frge = '-'
        else:
            frge = np.nanmean(frge_arr, axis=axis).round(decimals=decs).flatten().astype(str)
        if type(frge) in (list, np.ndarray) and len(frge) == 1:
            frge = frge[0]
    except Exception as err:
        print('FRGE ERROR', str(err))
        frge = '-'
    try:
        print(";;;", obs_da_m[~(mod_da_m.mask+obs_da_m.mask)].size)
        totn = str(obs_da_m[~(mod_da_m.mask+obs_da_m.mask)].size)
        if type(totn) in (list, np.ndarray) and len(totn) == 1:
            totn = totn[0]
    except:
        totn = '0'
    #if axis is None:
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

    total_columns = ['model'] + list(STATS.keys())
    print(total_columns)
    total_df = pd.DataFrame(columns=total_columns)

    stat_columns = ['lon', 'lat'] + list(MODELS.keys())
    print(stat_columns)
    bias_df = pd.DataFrame(columns=stat_columns)
    rmse_df = pd.DataFrame(columns=stat_columns)
    corr_df = pd.DataFrame(columns=stat_columns)
    frge_df = pd.DataFrame(columns=stat_columns)
    # totn_df = pd.DataFrame(columns=stat_columns)

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
            print('Error', str(fnames), str(err))
            continue

    try:
        # read observations and transform to a dataframe with only needed points 
        obs_ds = xr.open_mfdataset([obs_file for obs_file in obs_paths if os.path.exists(obs_file)],
                               concat_dim='time',
                               combine='nested',
                               )

        # retrieve lat and lon to perform the interpolation
        obs_lat = obs_ds['lat']
        obs_lon = obs_ds['lon']

    except Exception as err:
        print('Error', str(obs_paths), str(err))
        obs_ds = False
    
    variable = OBS[obs]['mod_var']
    obs_var = OBS[obs]['obs_var']
    print('v', variable)
    # if observation perform interpolation
    print('mod var', OBS[obs]['mod_var'])
    print('obs var', OBS[obs]['obs_var'])

    print(models_ds)
    print(model)
    for mod_idx, (mod_ds, mod) in enumerate(zip(models_ds, model)):
        print('MOD', mod, 'IDX', mod_idx)
        print('VARIABLE', variable, mod_ds.variables.keys())
        if variable in mod_ds.variables or variable.lower() in mod_ds.variables:
            if variable.lower() in mod_ds.variables:
                curr_var = variable.lower()
            else:
                curr_var = variable
            if obs_ds:
                print('interpolating to observations ...')
                try:
                    mod_interp = mod_ds[curr_var].interp(longitude=obs_lon, latitude=obs_lat)
                except:
                    mod_interp = mod_ds[curr_var].interp(lon=obs_lon, lat=obs_lat)
                print('converting to df  ...')
            else:
                mod_interp = mod_ds[curr_var]
                print('converting dataset to df ...')

            obs_timesteps = np.unique(obs_ds[obs_var][obs_ds[obs_var].time.isin(mod_interp.time)].time)
            print("timesteps", obs_timesteps, type(obs_timesteps))
            obs_da = obs_ds[obs_var].sel(time=obs_timesteps)
            #print(obs_da)
            mod_da = mod_interp.sel(time=obs_timesteps)
            #print(mod_da)

            # TOTAL SCORES
            scores = ret_scores(mod_da, obs_da)
            scores.update({ 'model': mod })
            total_df.loc[mod_idx] = scores
            print(mod)
            print(total_df)

            # SCORES per point
            print('SCORES per point!')
            scores = ret_scores(mod_da, obs_da, axis=0)
            print(scores)
            #print('lon', obs_lon.shape, 'lat', obs_lat.shape, 'BIAS', scores['bias'].shape)
            xlon, ylat = np.meshgrid(obs_lon, obs_lat)
            bias_df['lon'] = xlon.flatten().astype(str)
            bias_df['lat'] = ylat.flatten().astype(str)
            corr_df['lon'] = xlon.flatten().astype(str)
            corr_df['lat'] = ylat.flatten().astype(str)
            rmse_df['lon'] = xlon.flatten().astype(str)
            rmse_df['lat'] = ylat.flatten().astype(str)
            frge_df['lon'] = xlon.flatten().astype(str)
            frge_df['lat'] = ylat.flatten().astype(str)
            bias_df[stat_columns[mod_idx+2]] = scores['bias']
            corr_df[stat_columns[mod_idx+2]] = scores['corr']
            rmse_df[stat_columns[mod_idx+2]] = scores['rmse']
            frge_df[stat_columns[mod_idx+2]] = scores['frge']

    if obs_ds:
        obs_ds.close()
    mod_ds.close()

    if len(months) == 1:
        fname = "{}".format(months[0])
    else:
        fname = "{}-{}".format(months[0], months[-1])

    print("Writing h5 tables for maps ...")
    bias_df_out = os.path.join(OBS[obs]['path'], "h5", "{}_bias.h5")
    corr_df_out = os.path.join(OBS[obs]['path'], "h5", "{}_corr.h5")
    rmse_df_out = os.path.join(OBS[obs]['path'], "h5", "{}_rmse.h5")
    frge_df_out = os.path.join(OBS[obs]['path'], "h5", "{}_frge.h5")
    print("Writing h5 tables for scores ...")
    total_df_out = os.path.join(OBS[obs]['path'], "h5", "{}_scores.h5")

    print("BIAS", bias_df_out.format(fname), bias_df.size)
    bias_df = bias_df[((bias_df[bias_df.columns[2:]]!='nan') & (bias_df[bias_df.columns[2:]].notnull())).any(axis=1)]
    print("AFTER", bias_df.size)
    bias_df.to_hdf(bias_df_out.format(fname), "bias_{}".format(fname), format='table')
    
    print("CORR", corr_df_out.format(fname), corr_df.size)
    corr_df = corr_df[((corr_df[corr_df.columns[2:]]!='nan') & (corr_df[corr_df.columns[2:]].notnull())).any(axis=1)]
    print("AFTER", corr_df.size)
    corr_df.to_hdf(corr_df_out.format(fname), "corr_{}".format(fname), format='table')
    
    print("RMSE", rmse_df_out.format(fname), rmse_df.size)
    rmse_df = rmse_df[((rmse_df[rmse_df.columns[2:]]!='nan') & (rmse_df[rmse_df.columns[2:]].notnull())).any(axis=1)]
    print("AFTER", rmse_df.size)
    rmse_df.to_hdf(rmse_df_out.format(fname), "rmse_{}".format(fname), format='table')
    
    print("FRGE", frge_df_out.format(fname), frge_df.size)
    frge_df = frge_df[((frge_df[frge_df.columns[2:]]!='nan') & (frge_df[frge_df.columns[2:]].notnull())).any(axis=1)]
    print("AFTER", frge_df.size)
    frge_df.to_hdf(frge_df_out.format(fname), "frge_{}".format(fname), format='table')
    
    print("TOTAL", total_df_out.format(fname))
    print(mod, total_df)
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

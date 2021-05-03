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


def ret_scores(mod_df, obs_df, grp=None, grpname=None, obs='aeronet'):
    decs = 2
    if grp is None:
        obs_stat = obs_df.set_index('time')
    else:
        obs_stat = obs_df.get_group(grp).set_index('time')
    if obs_stat.size == 0 and grpname is None:
        return 'Total', {'BIAS':  np.nan, 'CORR': np.nan, 'RMSE': np.nan, 'FRGE': np.nan, 'TOTN': np.nan}
    elif obs_stat.size == 0:
        return obs_stat[grpname][0], {'BIAS':  np.nan, 'CORR': np.nan, 'RMSE': np.nan, 'FRGE': np.nan, 'TOTN': np.nan}
    if grp is None:
        mod_stat = mod_df.set_index('time')
    else:
        mod_stat = mod_df.get_group(grp).set_index('time')
    tot = obs_stat.merge(mod_stat, on='time')
    mvar, ovar = OBS[obs]['mod_var'], OBS[obs]['obs_var']
    try:
        bias = (tot[mvar] - tot[ovar]).mean().round(decimals=decs).astype(str)
    except:
        bias = '-'
    try:
        corr = tot[[ovar, mvar]].corr().values[0][1].round(decimals=decs)
        corr = not np.isnan(corr) and corr.astype(str) or '-'
    except:
        corr = '-'
    try:
        rmse = mean_squared_error(tot[ovar][~tot[ovar].isna()], tot[mvar][~tot[ovar].isna()], squared=False).round(decimals=decs).astype(str)
    except:
        rmse = '-'
    try:
        frge = (2*((tot[mvar] - tot[ovar])/(tot[mvar] + tot[ovar]))).abs().mean().round(decimals=decs).astype(str)
    except:
        frge = '-'
    try:
        totn = tot[ovar].notnull().sum().round(decimals=decs).astype(str)
    except:
        totn = '-'
    if grpname is None:
        ret_name = 'Total'
    else:
        ret_name = obs_stat[grpname][0]
        if isinstance(ret_name, bytes):
            ret_name = ret_name.decode('utf-8')
    return ret_name, {'BIAS':  bias, 'CORR': corr, 'RMSE': rmse, 'FRGE': frge, 'TOTN': totn}


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
    totn_df = pd.DataFrame(columns=columns)

    # read sites for a text file
    sites = pd.read_table(os.path.join(CURRENT_PATH, '../conf/',
        OBS[obs]['sites']), delimiter=r"\s+",
        engine='python').sort_values(by='AREA')

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
        # read filter variable
        flt_ds = xr.open_mfdataset(flt_paths,
                               concat_dim='time',
                               combine='nested',
                               )

        # select stations and remove others
        flt_ds = flt_ds.where(flt_ds['station_name'].isin(sites['SITE'].values.astype(np.bytes_)))
        flt_df = flt_ds.to_dataframe().reset_index().dropna(subset=['station_name'])
        flt_df = flt_df[['time', 'station', 'ndata', 'station_name', OBS[obs]['flt_var']]]

        # re-numbering stations
        old_stations = flt_df['station'].unique()
        new_stations = np.arange(old_stations.size)
        for old_st, new_st in zip(old_stations, new_stations):
            flt_df.loc[flt_df['station'] == old_st, 'station'] = new_st

        # read observations and transform to a dataframe with only needed stations
        obs_ds = xr.open_mfdataset(obs_paths,
                               concat_dim='time',
                               combine='nested',
                               )
        # select only stations in a given text file and remove others
        obs_ds = obs_ds.where(obs_ds['station_name'].isin(sites['SITE'].values.astype(np.bytes_)))
        obs_df = obs_ds.to_dataframe().reset_index().dropna(subset=['station_name'])
        obs_df = obs_df[['time', 'station', 'ndata', 'station_name', OBS[obs]['obs_var']]]

        # re-numbering stations
        for old_st, new_st in zip(old_stations, new_stations):
            obs_df.loc[obs_df['station'] == old_st, 'station'] = new_st

        # adding area to each station
        for site in sites['SITE']:
            obs_df.loc[obs_df['station_name'] == site.encode('utf-8'), 'area'] = sites.loc[sites['SITE'] == site, 'AREA'].values

        # apply filtering on the whole dataframe
        obs_df.loc[flt_df[OBS[obs]['flt_var']]>0.6, OBS[obs]['obs_var']] = np.nan

        # retrieve lat and lon only with 'station' dimension to perform the interpolation
        obs_lat = obs_ds['latitude'].dropna('station')[0].drop_vars('time')
        obs_lon = obs_ds['longitude'].dropna('station')[0].drop_vars('time')

        # group by area
        obs_grps_area = obs_df.groupby('area')

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
        totn = []
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

            # adding area to each station
            for st in mod_df['station']:
                mod_df.loc[mod_df['station'] == st, 'area'] = obs_df.loc[obs_df['station'] == st, 'area'].values[0]

            # print(mod_df)
            mod_grps_area = mod_df.groupby('area')

            for obs_area in obs_grps_area:
                area, scores = ret_scores(mod_grps_area, obs_grps_area, obs_area[0], grpname='area')
                stations.append(area)
                bias.append(scores['BIAS'])
                rmse.append(scores['RMSE'])
                corr.append(scores['CORR'])
                frge.append(scores['FRGE'])
                totn.append(scores['TOTN'])
                mod_grps_stat = mod_grps_area.get_group(obs_area[0]).groupby('station')
                obs_grps_stat = obs_grps_area.get_group(obs_area[0]).groupby('station')
                for stat in obs_grps_stat:
                    station, scores = ret_scores(mod_grps_stat, obs_grps_stat, stat[0], grpname='station_name')
                    stations.append(station)
                    bias.append(scores['BIAS'])
                    rmse.append(scores['RMSE'])
                    corr.append(scores['CORR'])
                    frge.append(scores['FRGE'])
                    totn.append(scores['TOTN'])

            total, scores = ret_scores(mod_df, obs_df)
            stations.append(total)
            bias.append(scores['BIAS'])
            rmse.append(scores['RMSE'])
            corr.append(scores['CORR'])
            frge.append(scores['FRGE'])
            totn.append(scores['TOTN'])
            print(stations)
            print(columns[mod_idx+1])
            print('BIAS', bias)
            print('RMSE', rmse)
            print('CORR', corr)
            print('FRGE', frge)
            print('TOTN', totn)

        # break
        print(stations)
        print(columns[mod_idx+1])
        print('BIAS', bias)
        print('RMSE', rmse)
        print('CORR', corr)
        print('FRGE', frge)
        print('TOTN', totn)
        bias_df['station'] = stations
        bias_df[columns[mod_idx+1]] = bias
        rmse_df['station'] = stations
        rmse_df[columns[mod_idx+1]] = rmse
        corr_df['station'] = stations
        corr_df[columns[mod_idx+1]] = corr
        frge_df['station'] = stations
        frge_df[columns[mod_idx+1]] = frge
        totn_df['station'] = stations
        totn_df[columns[mod_idx+1]] = totn

    if obs_ds:
        obs_ds.close()
    if flt_ds:
        flt_ds.close()
    mod_ds.close()

    if len(months) == 1:
        fname = "{}".format(months[0])
    else:
        fname = "{}-{}".format(months[0], months[-1])

    print("Writing h5 ...")
    bias_df_out = os.path.join(OBS[obs]['path'], "h5", "{}_bias.h5")
    corr_df_out = os.path.join(OBS[obs]['path'], "h5", "{}_corr.h5")
    rmse_df_out = os.path.join(OBS[obs]['path'], "h5", "{}_rmse.h5")
    frge_df_out = os.path.join(OBS[obs]['path'], "h5", "{}_frge.h5")
    totn_df_out = os.path.join(OBS[obs]['path'], "h5", "{}_totn.h5")
    print("BIAS", bias_df_out.format(fname))
    bias_df.to_hdf(bias_df_out.format(fname), "bias_{}".format(fname), format='table')
    print("CORR", corr_df_out.format(fname))
    corr_df.to_hdf(corr_df_out.format(fname), "corr_{}".format(fname), format='table')
    print("RMSE", rmse_df_out.format(fname))
    rmse_df.to_hdf(rmse_df_out.format(fname), "rmse_{}".format(fname), format='table')
    print("FRGE", frge_df_out.format(fname))
    frge_df.to_hdf(frge_df_out.format(fname), "frge_{}".format(fname), format='table')
    print("TOTN", totn_df_out.format(fname))
    totn_df.to_hdf(totn_df_out.format(fname), "totn_{}".format(fname), format='table')


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

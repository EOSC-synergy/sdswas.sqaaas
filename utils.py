#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Utils module with utility functions """

import matplotlib as mpl
from matplotlib import cm
import xarray as xr
import numpy as np
import pandas as pd
import math
import feather
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html


TIMES = {
    'animation': 900,
    'transition': 500,
    'slider_transition': 500
}


def concat_dataframes(fname_tpl, months, variable, rename_from=None, notnans=None):
    """ Concatenate monthly dataframes """

    # build feather files paths
    opaths = [fname_tpl.format(month, variable)
        for month in months]

    # read monthly dataframes and concatenate into one
    if rename_from:
        mon_dfs = pd.concat([feather.read_dataframe(opath)
            .rename(columns={rename_from: variable})
            for opath in opaths])
    # in case of models we don't rename the variable column
    else:
        mon_dfs = pd.concat([feather.read_dataframe(opath)
            for opath in opaths])

    if notnans is None:
        notnans = [st for st in mon_dfs['station'].unique()
            if not mon_dfs[mon_dfs['station']==st][variable].isnull().all()]

    return notnans, mon_dfs[mon_dfs['station'].isin(notnans)]


def retrieve_timeseries(fname, lat, lon, variable, method='netcdf'):
    """ """
    if method == 'feather':
        df = feather.read_dataframe(fname)
        if 'lat' in df.columns:
            lat_col = 'lat'
            lon_col = 'lon'
        else:
            lat_col = 'latitude'
            lon_col = 'longitude'

        #print("LAT LON", lat, lon)
        n_lon = find_nearest(df[lon_col].values, lon)
        n_lat = find_nearest(df[lat_col].values, lat)
        #print("NLAT", df[lat_col] == n_lat)
        #print("NLON", df[lon_col] == n_lon)
        ts = df.loc[(df[lat_col] == n_lat) &
                    (df[lon_col] == n_lon), 
                    ('time', variable)].set_index('time')
        return n_lat, n_lon, ts.index, ts[variable]

    def preprocess(ds, n=8):
        return ds.isel(time=range(n))

    ds = xr.open_mfdataset(fname, concat_dim='time', combine='nested', preprocess=preprocess)
    if 'lat' in ds.variables:
        da = ds[variable].sel(lon=lon, lat=lat, method='nearest')
        return da['lat'].values, da['lon'].values, da.indexes['time'], da
    else:
        da = ds[variable].sel(longitude=lon, latitude=lat, method='nearest')
        return da['latitude'].values, da['longitude'].values, da.indexes['time'], da


def find_nearest(array, value):
    """ Find the nearest value of a couple of coordinates """
    return array[np.abs(array-value).argmin()]


def find_nearest2(array, value):
    """ Find the nearest value of a couple of coordinates """
    idx = np.searchsorted(array, value, side="left")
    if idx > 0 and (idx == len(array) or math.fabs(value - array[idx-1]) <
                    math.fabs(value - array[idx])):
        return array[idx-1]
    else:
        return array[idx]


def calc_matrix(n):
    """ Calculate the mosaic optimum matrix shape """
    sqrt_n = math.sqrt(n)
    ncols = sqrt_n == int(sqrt_n) and int(sqrt_n) or int(sqrt_n) + 1
    nrows = n%ncols > 0 and int(n/ncols)+1 or int(n/ncols)
    return ncols, nrows


def magnitude(num):
    """ Calculate magnitude """
    return int(math.floor(math.log10(num)))


def normalize_vals(vals, valsmin, valsmax, rnd=2):
    """ Normalize values to 0-1 scale """
    vals = np.array(vals)
    if rnd < 2:
        rnd = 2
    return np.around((vals-valsmin)/(valsmax-valsmin), rnd)


def get_colorscale(bounds, colormap, discrete=True):
    """ Create colorscale """
    bounds = np.array(bounds).astype('float32')
    magn = magnitude(bounds[-1])
    n_bounds = normalize_vals(bounds, bounds[0], bounds[-1], magn)
    norm = mpl.colors.BoundaryNorm(bounds, len(bounds)-1, clip=True)
    s_map = cm.ScalarMappable(norm=norm, cmap=colormap)

    colorscale = [[idx,
                   'rgba' + str(s_map.to_rgba(val,
                                              alpha=True,
                                              bytes=True,
                                              norm=True))]
                  for idx, val in zip(n_bounds, bounds)]

    if discrete:
        for item in colorscale.copy():
            if colorscale.index(item) < len(colorscale)-2:
                colorscale.insert(colorscale.index(item)+1,
                                  [colorscale[colorscale.index(item)+1][0],
                                   colorscale[colorscale.index(item)][1]])

    return colorscale


def get_animation_buttons():
    """ Returns play and stop buttons """
    return dict(
        type="buttons",
        direction="left",
        buttons=[
            dict(label="&#9654;",
                 method="animate",
                 args=[
                     None,
                     dict(
                         frame=dict(duration=TIMES['animation'],
                                    redraw=True),
                         transition=dict(duration=TIMES['transition'],
                                         easing="quadratic-in-out"),
                         fromcurrent=True,
                         mode='immediate'
                     )
                 ]),
            dict(label="&#9724;",
                 method="animate",
                 args=[
                     [None],
                     dict(
                         frame=dict(duration=0,
                                    redraw=True),
                         transition=dict(duration=0),
                         mode='immediate'
                         )
                 ])
            ],
        pad={"r": 0, "t": 0},
        x=0.50,
        y=1.07,
        xanchor="right",
        yanchor="top"
    )


def get_graph(index=None, figure={}, gid=None, style={ 'height': '93vh !important' }):
    """ Renders map graph """
    from data_handler import MODEBAR_CONFIG
    from data_handler import MODEBAR_LAYOUT

    if gid is None:
        gid = {
                'type': 'graph-with-slider',
                'index': index,
            }

    figure.update_layout(MODEBAR_LAYOUT)

    return dcc.Graph(
            id=gid,
            className="graph-with-slider",
            style=style,
            figure=figure,
            config=MODEBAR_CONFIG
        )

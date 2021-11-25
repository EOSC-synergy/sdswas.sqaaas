# -*- coding: utf-8 -*-
""" Data Handler """

import plotly.graph_objs as go
from dash import html
import dash_leaflet as dl
import dash_leaflet.express as dlx
from dash_extensions.javascript import arrow_function
from dash_extensions.javascript import Namespace
from matplotlib.colors import ListedColormap
import numpy as np
from netCDF4 import Dataset as nc_file
import pandas as pd
import geopandas as gpd
from shapely import geometry
import json
import orjson
from datetime import datetime
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
from PIL import Image
import requests
import calendar
import time
import os

from utils import concat_dataframes
from utils import retrieve_timeseries
from utils import retrieve_single_point
from utils import get_colorscale


DIR_PATH = os.path.dirname(os.path.realpath(__file__))

DEBUG = True

COLORS = ['#ffffff', '#a1ede3', '#5ce3ba', '#fcd775', '#da7230',
          '#9e6226', '#714921', '#392511', '#1d1309']

COLORS_NEW = ['rgba(255,255,255,0.3)', '#a1ede3', '#5ce3ba', '#fcd775', '#da7230',
          '#9e6226', '#714921', '#392511', '#1d1309']

COLORS_PROB = [  #(1,1,1),                                            \
                (225/255.0,225/255.0,225/255.0),                    \
                (205/255.0,205/255.0,205/255.0),                    \
                (190/255.0,255/255.0, 51/255.0),                    \
                (162/255.0,220/255.0, 51/255.0),                    \
                (255/255.0,255/255.0,155/255.0),                    \
                (255/255.0,255/255.0, 75/255.0),                    \
                (255/255.0,210/255.0, 64/255.0),                    \
                (255/255.0,139/255.0, 90/255.0),                    \
                (255/255.0,102/255.0, 51/255.0)  ]

COLORMAP = ListedColormap(COLORS)
COLORMAP_PROB = ListedColormap(COLORS_PROB)

VARS = json.load(open(os.path.join(DIR_PATH, 'conf/vars.json')))
MODELS = json.load(open(os.path.join(DIR_PATH, 'conf/models.json')))
OBS = json.load(open(os.path.join(DIR_PATH, 'conf/obs.json')))
WAS = json.load(open(os.path.join(DIR_PATH, 'conf/was.json')))
PROB = json.load(open(os.path.join(DIR_PATH, 'conf/prob.json')))
DATES = json.load(open(os.path.join(DIR_PATH, 'conf/dates.json')))

STATS = OrderedDict({ 'bias': 'BIAS', 'corr': 'CORR', 'rmse': 'RMSE', 'frge': 'FGE', 'totn': 'TOTAL CASES' })
STATS_CONF = OrderedDict(
        { 
            'bias': {
                'max': 0.10,
                'min': -0.10,
                'mid': 0,
                'cmap': 'RdBu_r',
                'bounds': np.array([-0.10,-0.08,-0.06,-0.04,-0.02,0,0.02,0.04,0.06,0.08,0.10]),  # np.arange(-0.1, 0.12, 0.02)
                },
            'corr': {
                'max': 1,
                'min': -1,
                'mid': 0,
                'cmap': 'RdBu_r',
                'bounds': np.array([-1,-0.80,-0.60,-0.40,-0.20,0,0.20,0.40,0.60,0.80,1]),  # np.arange(-1, 1.2, 0.2)
                },
            'rmse': {
                'max': 0.30,
                'min': 0,
                'mid': None,
                'cmap': 'viridis',
                'bounds': np.array([0,0.02,0.04,0.06,0.08,0.10,0.12,0.15,0.20,0.25,0.30])
                },
            'frge': {
                'max': 2,
                'min': 0,
                'mid': None,
                'cmap': 'viridis',
                'bounds': np.array([0,0.20,0.40,0.60,0.80,1.00,1.20,1.40,1.60,1.80,2])  # np.arange(0, 2.2, 0.2)
                }
            })

GRAPH_HEIGHT = 92.8

# Frequency = 3 Hourly
FREQ = 3

DEFAULT_VAR = 'OD550_DUST'
DEFAULT_MODEL = 'median'

STYLES = {
    "carto-positron": {
        'name': "Light",
        'url': 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
	'attribution': '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
    },
    "open-street-map": {
        'name': "Open street map",
        'url': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
	'attribution': '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    },
    "stamen-terrain": {
        'name': "Terrain",
        'url': 'https://stamen-tiles-{s}.a.ssl.fastly.net/terrain/{z}/{x}/{y}{r}.png',
        'attribution': 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a> &mdash; Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    },
    "esri-world": {
        'name': "ESRI",
        'url': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
       	'attribution': 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
    }
}


MODEBAR_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": ["toImage",
                               "pan2d",
                               "select2d",
                               "lasso2d",
                               ],
}

MODEBAR_CONFIG_TS = {
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": ["zoom2d",
                               "pan2d",
                               "select2d",
                               "lasso2d",
                               "autoScale2d"
                               ],
}

MODEBAR_LAYOUT = {
    'modebar': {
        'orientation': 'v',
        'color': '#40535C',
        'bgcolor': 'rgba(0,0,0,0)',
        'activecolor': '#A2B0B6',
    }
}

MODEBAR_LAYOUT_TS = {
    'modebar': {
        'orientation': 'h',
        'color': '#40535C',
        'bgcolor': 'rgba(0,0,0,0)',
        'activecolor': '#A2B0B6',
    }
}

DISCLAIMER_MODELS = [html.Span(html.P("""FORECAST ISSUED"""), id='forecast-issued'), html.Span(html.P("""DISCLAIMER: Dust data ©2021 WMO Barcelona Dust Regional Center."""), id='forecast-disclaimer')]

DISCLAIMER_OBS = html.P("""DISCLAIMER: Aerosol data ©2021 WMO Barcelona Dust Regional Center, NASA.""")

GEOJSON_TEMPLATE = "{}/geojson/{}/{:02d}_{}_{}.geojson"
NETCDF_TEMPLATE = "{}/netcdf/{}{}.nc"


class Observations1dHandler(object):
    """ Class which handles 1D obs data """

    def __init__(self, sdate, edate, obs):
        fday = sdate[:-2] + '01'
        lday = edate[:-2] + str(calendar.monthrange(int(edate[:4]), int(edate[4:6]))[1])
        date_range = pd.date_range(fday, lday, freq='M')
        months = [d.strftime("%Y%m") for d in date_range.to_pydatetime()]
        filepath = "{}.nc".format(os.path.join(OBS[obs]['path'], 'netcdf', OBS[obs]['template'].format(OBS[obs]['obs_var'], months[0])))
        self.input_file = nc_file(filepath)
        self.lon = self.input_file.variables['longitude'][:]
        self.lat = self.input_file.variables['latitude'][:]
        time_obj = self.input_file.variables['time']
        self.tim = time_obj[:]
        self.what, _, rdate, rtime = time_obj.units.split()[:4]
        self.rdatetime = datetime.strptime("{} {}".format(rdate, rtime[:5]),
                                           "%Y-%m-%d %H:%M")
        self.varlist = [var for var in self.input_file.variables if var == OBS[obs]['obs_var']]
        if DEBUG: print('VARLIST', self.varlist)

        sites = pd.read_table(os.path.join('./conf/',
            OBS[obs]['sites']), delimiter=r"\s+", engine='python')

        idxs, self.station_names = np.array([[idx, st_name[~st_name.mask].tostring().decode('utf-8')]
                              for idx, st_name in
                              enumerate(self.input_file.variables['station_name'][:])
                              if st_name[~st_name.mask].tostring().decode('utf-8').upper() in map(str.upper, sites['SITE'])]
                              ).T
#        idxs, self.station_names = np.array([[idx, st_name]
#                              for idx, st_name in
#                              enumerate(sites['SITE'][:])
#                              if st_name[~st_name.mask].tostring().decode('utf-8').upper() in map(str.upper, sites['SITE'])]
#                              ).T

        if DEBUG: print('IDXS', idxs)
        if DEBUG: print('ST_NAMES', self.station_names)

        self.clon = self.lon[idxs.astype(int)]
        self.clat = self.lat[idxs.astype(int)]

        self.values = {
            varname: self.input_file.variables[varname][:, idxs.astype(int)]
            for varname in self.varlist
        }

        self.bounds = {
            varname: np.array(VARS[OBS[obs]['mod_var']]['bounds']).astype('float32')
            for varname in self.varlist
        }

        self.colormaps = {
            varname: get_colorscale(self.bounds[varname], COLORMAP)
            for varname in self.varlist
        }

#         self.selected_date_plain = selected_date
# 
#         self.selected_date = datetime.strptime(
#             selected_date, "%Y%m%d").strftime("%Y-%m-%d")

#     def retrieve_time_index(self, tstep=0):
#         """ Generate index of current date time """
#         seldate = datetime.strptime(self.selected_date, "%Y-%m-%d")
#         if self.what == 'days':
#             cdatetime = self.seldaterdatetime + relativedelta(days=self.tim[tstep])
#         elif self.what == 'hours':
#             cdatetime = self.rdatetime + relativedelta(hours=self.tim[tstep])
#         elif self.what == 'minutes':
#             cdatetime = self.rdatetime + relativedelta(minutes=self.tim[tstep])
#         elif self.what == 'seconds':
#             cdatetime = self.rdatetime + relativedelta(seconds=self.tim[tstep])

    def generate_obs1d_tstep_trace(self, var):
        """ Generate trace to be added to data, per variable and timestep """
        varname = self.varlist[0]
        #val = self.values[varname][0]
        notnan = (np.array([i for i in range(self.values[varname].shape[1]) if not self.values[varname][:,i].mask.all()]),)
        clon = self.clon[notnan]
        clat = self.clat[notnan]
        cstations = self.station_names[notnan]
        if DEBUG: print(len(clon), len(clat), len(cstations))
        name = 'Aeronet Station'
        return dict(
            type='scattermapbox',
            below='',
            lon=clon,
            lat=clat,
            mode='markers',
            name=name,
            customdata=cstations,
            hovertemplate="name:%{customdata}<br>lon: %{lon:.2f}<br>" +
                          "lat: %{lat:.2f}", #"<br>value: %{text:.2f}",
            opacity=0.6,
            showlegend=False,
            marker=dict(
                # autocolorscale=True,
                # symbol='square',
                color='#f0b450',
                opacity=0.8,
                size=15,
                colorscale=self.colormaps[varname],
                cmin=self.bounds[varname][0],
                cmax=self.bounds[varname][-1],
                showscale=False,
            ),

        )


class ObsTimeSeriesHandler(object):
    """ Class to handle time series """

    def __init__(self, obs, start_date, end_date, variable, models=None):
        self.obs = obs
        if models is None:
            models = list(MODELS.keys())
        self.model = models
        self.variable = variable
        self.dataframe = []
        if DEBUG: print("ObsTimeSeries", start_date, end_date)
        self.date_range = pd.date_range(start_date, end_date, freq='D')

        fname_tpl = os.path.join(OBS[obs]['path'],
                                'feather',
                                '{{}}-{dat}-{{}}_interp.ft')

        months = np.unique([d.strftime("%Y%m") for d in self.date_range.to_pydatetime()])

        if DEBUG: print('MONTHS', months)
#         if not months:
#             months = [datetime.strptime(end_date, "%Y-%m-%d").strftime("%Y%m")]

        fname_obs = fname_tpl.format(dat=obs)
        notnans, obs_df = concat_dataframes(fname_obs, months, variable,
                rename_from=OBS[obs]['obs_var'])
        self.dataframe.append(obs_df)

        for mod in self.model:
            fname_mod = fname_tpl.format(dat=mod)
            _, mod_df = concat_dataframes(fname_mod, months, variable,
                    rename_from=None, notnans=notnans)
            self.dataframe.append(mod_df)


    def retrieve_timeseries(self, idx, st_name):

        old_indexes = self.dataframe[0]['station'].unique()
        new_indexes = np.arange(old_indexes.size)
        dict_idx = dict(zip(new_indexes, old_indexes))
        fig = go.Figure()
        for mod, df in zip([self.obs]+self.model, self.dataframe):
            if df is None:
                continue
            if DEBUG: print("MOD", mod, "COLS", df.columns)
            if df.columns[-1].upper() == self.variable:
                df = df.rename(columns = { df.columns[-1]: self.variable })
            timeseries = \
                df[df['station']==dict_idx[idx]].set_index('time')

            if 'lat' in df.columns:
                lat_col = 'lat'
                lon_col = 'lon'
            else:
                lat_col = 'latitude'
                lon_col = 'longitude'

            if mod == self.obs:
                sc_mode = 'markers'
                marker = {'size': 10, 'symbol': "triangle-up-dot", 'color': '#f0b450'}
                line = {}
                visible = True
                name = mod.upper()
            else:
                sc_mode = 'lines'
                marker = {}
                line = { 'color': MODELS[mod]['color'] }
                visible = 'legendonly'
                cur_lat = round(timeseries[lat_col][0], 2)
                cur_lon = round(timeseries[lon_col][0], 2)
                name = "{}".format(
                    MODELS[mod]['name'])

            if mod == 'median':
                line['dash'] = 'dash'

            fig.add_trace(dict(
                type='scatter',
                name=name,
                x=timeseries.index,
                y=timeseries[self.variable].round(2),
                mode=sc_mode,
                marker=marker,
                line=line,
                visible=visible
                )
            )

        title = "{} @ {} (lat = {:.2f}, lon = {:.2f})".format(
            VARS[self.variable]['name'], st_name, cur_lat, cur_lon,
        )

        fig.update_layout(
            title=dict(text=title, x=0.45, y=0.99),
            # uirevision=True,
            autosize=True,
            showlegend=True,
            plot_bgcolor='#F9F9F9',
            font_size=12,
            hovermode="x",        # highlight closest point on hover
            margin={"r": 10, "t": 35, "l": 10, "b": 10},
        )
        fig.update_xaxes(
            range=[self.date_range[0], self.date_range[-1]],
            rangeslider_visible=True,
            rangeselector=dict(
                buttons=list([
                    dict(step="all", label="all"),
                    dict(count=14, label="2w",
                         step="day", stepmode="backward"),
                    dict(count=7, # label="1w",
                         step="day", stepmode="backward"),
                ])
            )
        )

#        fig['layout']['xaxis'].update(range=['2020-04-01', '2020-04-17 09:00'])

        if DEBUG: print('FIG TYPE', type(fig))
        return fig


class TimeSeriesHandler(object):
    """ Class to handle time series """

    def __init__(self, model, date, variable):
        if isinstance(model, str):
            model = [model]
        self.model = model
        self.variable = variable
        self.fpaths = []
        try:
            self.month = datetime.strptime(date, "%Y%m%d").strftime("%Y%m")
            self.currdate = datetime.strptime(date, "%Y%m%d").strftime("%Y%m%d")
        except:
            self.month = datetime.strptime(date, "%Y-%m-%d").strftime("%Y%m")
            self.currdate = datetime.strptime(date, "%Y-%m-%d").strftime("%Y%m%d")

    def retrieve_single_point(self, tstep, lat, lon, model=None, method='netcdf', forecast=False):

        if not model:
            model = self.model[0]

        if DEBUG: print("----------", model)

#        obs_eval = model[0] not in MODELS and model[0] in OBS
#        if obs_eval:
#            all_models = [model[0]] + list(MODELS.keys())
#        else:
#            all_models = list(MODELS.keys())

        if forecast:
            method = 'netcdf'
            path_template = '{}{}.nc'.format(self.currdate, MODELS[model]['template'], self.variable)

        fpath = os.path.join(MODELS[model]['path'], method, path_template)

        return retrieve_single_point( fpath, tstep, lat, lon, self.variable,
                method=method, forecast=forecast)
        

    def retrieve_timeseries(self, lat, lon, model=None, method='netcdf', forecast=False):

        if not model:
            model = self.model

        # if DEBUG: print("----------", model)

        obs_eval = model[0] not in MODELS and model[0] in OBS
        if obs_eval:
            all_models = [model[0]] + list(MODELS.keys())
        else:
            all_models = list(MODELS.keys())

        for mod in all_models:
            if obs_eval:
                filedir = OBS[model[0]]['path']
                path_tpl = '{}-{}-{}_interp.ft'  # 202010-median-OD550_DUST_interp.ft
            else:   # if mod in MODELS:
                filedir = MODELS[mod]['path']
                path_tpl = '{}-{}-{}.ft'  # 202010-median-OD550_DUST_interp.ft

            if method == 'feather':
                path_template = path_tpl.format(self.month, mod, self.variable)
            elif method == 'netcdf':
                path_template = '{}*{}.nc'.format(self.month, MODELS[mod]['template'], self.variable)

            if forecast:
                method = 'netcdf'
                path_template = '{}{}.nc'.format(self.currdate, MODELS[mod]['template'], self.variable)

            fpath = os.path.join(filedir,
                                 method,
                                 path_template)
            self.fpaths.append(fpath)

        title = "{} @ lat = {} and lon = {}".format(
            VARS[self.variable]['name'], round(lat, 2), round(lon, 2)
        )

        mul = VARS[self.variable]['mul']

        fig = go.Figure()

        for mod, fpath in zip(all_models, self.fpaths):
            # print(mod, fpath)
            if mod not in MODELS and mod in OBS:
                variable = OBS[mod]['obs_var']
            else:
                variable = self.variable

            if not os.path.exists(fpath):
                if DEBUG: print("NOT retrieving", fpath, "File doesn't exist.")
                continue

            if DEBUG: print('Retrieving *** FPATH ***', fpath)
            try:
                ts_lat, ts_lon, ts_index, ts_values = retrieve_timeseries(
                        fpath, lat, lon, variable, method=method, forecast=forecast)
            except Exception as e:
                if DEBUG: print("NOT retrieving", fpath, "ERROR:", str(e))
                continue

            if isinstance(ts_lat, np.ndarray):
                ts_lat = float(ts_lat)
                ts_lon = float(ts_lon)
                ts_values = (ts_values*mul).round(2)
            else:
                ts_values = round((ts_values*mul), 2)

            if obs_eval and mod == model[0]:
                sc_mode = 'markers'
                marker = {'size': 12, 'symbol': "triangle-up-dot", 'color': '#f0b450'}
                line = {}
                visible = True
                name = "{}".format(mod.upper())
            elif obs_eval:
                sc_mode = 'lines'
                marker = {}
                line = { 'color': MODELS[mod]['color'] }
                if mod in model:
                    visible = True
                else:
                    visible = 'legendonly'
                name = "{}".format(MODELS[mod]['name'])
            else:
                sc_mode = 'lines'
                marker = {}
                line = { 'color': MODELS[mod]['color'] }
                if mod in model:
                    visible = True
                else:
                    visible = 'legendonly'
                name = "{} ({}, {})".format(
                        MODELS[mod]['name'], round(ts_lat, 2), round(ts_lon, 2))

            if mod == 'median':
                line['dash'] = 'dash'
            else:
                line['dash'] = 'solid'

            fig.add_trace(dict(
                    type='scattergl',
                    name=name,
                    x=ts_index,
                    y=ts_values,
                    mode=sc_mode,
                    marker=marker,
                    line=line,
                    visible=visible,
                )
            )

        fig.update_layout(
            title=dict(text=title, x=0.45, y=.99),
            # uirevision=True,
            autosize=True,
            showlegend=True,
            plot_bgcolor='#F9F9F9',
            font_size=12,
            # hovermode="closest",        # highlight closest point on hover
            hovermode="x",        # highlight closest point on hover
            margin={"r": 10, "t": 35, "l": 10, "b": 10},
        )

        return fig


class FigureHandler(object):
    """ Class to manage the figure creation """

    def __init__(self, model=None, selected_date=None):
        """ FigureHandler init """

        self.st_time = time.time()
        if isinstance(model, list):
            model = model[0]

        self.model = model

        if self.model not in MODELS and self.model in OBS:
            self.filedir = OBS[self.model]['path']
            self.filevars = [OBS[self.model]['obs_var']]
            self.confvars = [OBS[self.model]['mod_var']]
            filetpl = OBS[self.model]['template'].format(OBS[self.model]['obs_var'], selected_date) + '.nc'
            filepath = os.path.join(self.filedir, 'netcdf', filetpl)

        elif self.model in MODELS:
            if DEBUG: print("MODEL", model)
            self.filedir = MODELS[self.model]['path']
            self.filevars = VARS
            self.confvars = None

            filepath = NETCDF_TEMPLATE.format(
                self.filedir,
                selected_date,
                MODELS[self.model]['template']
            )
        else:
            self.model = None
            self.filedir = None
            self.filevars = None
            self.confvars = None
            filepath = None
            self.bounds = None

        if DEBUG: print("FILEPATH", filepath)
        if filepath is None or not os.path.exists(filepath):
            self.filedir = None
            self.filevars = None
            self.confvars = None
            filepath = None
            self.bounds = None
            self.varlist = None
            self.rdatetime = None
            self.tim = [0]
        elif filepath is not None:
            self.input_file = nc_file(filepath)
            if 'lon' in self.input_file.variables:
                lon = self.input_file.variables['lon'][:]
                lat = self.input_file.variables['lat'][:]
            else:
                lon = self.input_file.variables['longitude'][:]
                lat = self.input_file.variables['latitude'][:]
            time_obj = self.input_file.variables['time']
            self.tim = time_obj[:]
            self.what, _, rdate, rtime = time_obj.units.split()[:4]
            if len(rtime) > 5:
                rtime = rtime[:5]
            self.rdatetime = datetime.strptime("{} {}".format(rdate, rtime),
                                               "%Y-%m-%d %H:%M")
            varlist = [var for var in self.input_file.variables if (var.upper() in self.filevars) or (var in self.filevars)]
            self.varlist = varlist
            if DEBUG: print('VARLIST', varlist)
            self.xlon, self.ylat = np.meshgrid(lon, lat)

        if not self.varlist:
            self.varlist = VARS.keys()

        if DEBUG: print('VARLIST', self.varlist, 'CONFVAR', self.confvars)

        if self.confvars is not None:
            self.bounds = {
                varname.upper(): np.array(VARS[confvar]['bounds']).astype('float32')
                for varname, confvar in zip(self.filevars, self.confvars) if (varname.upper() in self.varlist) or (varname in self.varlist)
            }
        else:
            self.bounds = {
                varname.upper(): np.array(VARS[varname.upper()]['bounds']).astype('float32')
                for varname in self.varlist
            }

        self.colormaps = {
            varname.upper(): get_colorscale(self.bounds[varname.upper()], COLORMAP)
            for varname in self.varlist
        }
        # print(varlist, self.confvars, self.filevars, self.bounds, self.colormaps)

        if selected_date:
            self.selected_date_plain = selected_date

            self.selected_date = datetime.strptime(
                selected_date, "%Y%m%d").strftime("%Y-%m-%d")

            if not self.rdatetime:
                self.rdatetime = datetime.strptime(selected_date, "%Y%m%d")
                self.what = 'hours'

        self.fig = None
        if DEBUG: print("FILEDIR", self.filedir)

    def get_mapbox_style_buttons(self):
        """ Relayout map with different styles """
        return dict(
            direction="up",
            buttons=list([self.get_mapbox(style, relayout=True) for style in
                          STYLES.keys()]),
            # pad={"r": 0, "t": 0},
            showactive=True,
            x=0.9,
            y=0.09,
            xanchor="right",
            yanchor="top",
        )

    def get_mapbox(self, style='carto-positron', relayout=False, zoom=2.8, center=None):
        """ Returns mapbox layout """
        if center is None and hasattr(self, 'ylat'):
            center = go.layout.mapbox.Center(
                lat=(self.ylat.max()-self.ylat.min())/2 +
                self.ylat.min(),
                lon=(self.xlon.max()-self.xlon.min())/2 +
                self.xlon.min(),
            )
        elif center is not None:
            center = go.layout.mapbox.Center(center)
        else:
            center = go.layout.mapbox.Center({'lat': 30, 'lon': 15})
        mapbox_dict = dict(
            uirevision='forecast-multimodel',  # True,
            style=style,
            bearing=0,
            center=center,
            pitch=0,
            zoom=zoom
        )

        if not relayout:
            return mapbox_dict

        return dict(
            args=["mapbox", mapbox_dict],
            label=STYLES[style].capitalize(),
            method="relayout"
        )

    def get_center(self, center=None):
        """ Returns center of map """
        if center is None and hasattr(self, 'ylat'):
            center =  [
                    (self.ylat.max()-self.ylat.min())/2 + self.ylat.min(),
                    (self.xlon.max()-self.xlon.min())/2 + self.xlon.min(),
            ]
        elif center is None:
            center = [ 30, 15 ]

        return center

    def get_updated_trace(self, varname, tstep=0):
        """ Get updated trace """
        return dict(
            args=["scattermapbox", self.generate_var_tstep_trace(varname,
                                                                 tstep)],
            label=VARS[varname]['name'],
            method="restyle"
        )

    def set_data(self, varname, tstep=0):
        """ Set time dependent data """
        if self.model in OBS:
            mul = VARS[OBS[self.model]['mod_var']]['mul']
        else:
            mul = VARS[varname]['mul']

        realvar = [var for var in self.varlist if var.upper()==varname.upper()][0]
        # if DEBUG: print("***", mul, realvar, "***")
        var = self.input_file.variables[realvar][tstep]*mul
        idx = np.where((~var.ravel().mask) & (var.ravel() >= self.bounds[varname.upper()][0]))  # !=-9.e+33)
        xlon = self.xlon.ravel()[idx]
        ylat = self.ylat.ravel()[idx]
        var = var.ravel()[idx]
        # if DEBUG: print("***", xlon.shape, ylat.shape, var.shape, "***")
        return xlon.data, ylat.data, var.data

    def retrieve_cdatetime(self, tstep=0):
        """ Retrieve data from NetCDF file """
        tstep = int(tstep)
        tim = int(self.tim[tstep])
        if self.what == 'days':
            cdatetime = self.rdatetime + relativedelta(days=tim)
        elif self.what == 'hours':
            cdatetime = self.rdatetime + relativedelta(hours=tim)
        elif self.what == 'minutes':
            cdatetime = self.rdatetime + relativedelta(minutes=tim)
        elif self.what == 'seconds':
            cdatetime = self.rdatetime + relativedelta(seconds=tim)

        return cdatetime

    def generate_contour_tstep_trace_leaflet(self, varname, tstep=0):
        """ Generate trace to be added to data, per variable and timestep """
        from dash_server import app

        if varname not in VARS and self.model in OBS:
            name = VARS[OBS[self.model]['mod_var']]['name']
        else:
            name = VARS[varname]['name']
        if self.bounds:
            bounds = self.bounds[varname.upper()]
        else:
            bounds = [0, 1]

        if DEBUG: print(bounds)
        colorscale = COLORS_NEW

        geojson_url = app.get_asset_url(os.path.join('geojsons',
            GEOJSON_TEMPLATE.format(os.path.basename(MODELS[self.model]['path']),
                self.selected_date_plain, tstep, self.selected_date_plain,
                varname)))

        style = dict(weight=0, opacity=0, color='white', dashArray='', fillOpacity=0.6)

        # Create colorbar.
        ctg = ["{:.1f}".format(cls) if '.' in str(cls) else "{:d}".format(cls)
                for i, cls in enumerate(bounds[1:-1])]
        indices = list(range(len(ctg) + 2))
        colorbar = dl.Colorbar(
                min=0, max=len(ctg)+1,
                classes=indices,
                colorscale=colorscale,
                tickValues=indices[1:-1],
                tickText=ctg,
                position='topleft',
                width=250,
                height=15,
                style={ 'top': '70px' }
                )

        # Geojson rendering logic, must be JavaScript as it is executed in clientside.
        ns = Namespace("forecastTab", "forecastMaps")
        style_handle = ns("styleHandle")

        geojson = dl.GeoJSON(
                url=geojson_url,
                options=dict(style=style_handle),
                hideout=dict(colorscale=colorscale, bounds=bounds, style=style, colorProp="value")
                )  # url to geojson file

        return geojson, colorbar


    def generate_contour_tstep_trace(self, varname, tstep=0):
        """ Generate trace to be added to data, per variable and timestep """
        from dash_server import app

        geojson_file = GEOJSON_TEMPLATE.format(self.filedir,
                self.selected_date_plain, tstep, self.selected_date_plain, varname)

        if os.path.exists(geojson_file):
            geojson = orjson.loads(open(geojson_file).read())
        else:
            if DEBUG: print('ERROR', geojson_file, 'not available')
            geojson = {
                    "type": "FeatureCollection",
                    "features": []
                    }

        if varname not in VARS and self.model in OBS:
            name = VARS[OBS[self.model]['mod_var']]['name']
        else:
            name = VARS[varname]['name']
        # if DEBUG: print(self.bounds)
        if self.bounds:
            bounds = self.bounds[varname.upper()]
        else:
            bounds = [0, 1]
        loc_val = [
            (
                feature['id'],
                np.around(feature['properties']['value'], 2),
            )
            for feature in geojson['features']
            if feature['geometry']['coordinates']
        ]
        locations, values = np.array(loc_val).T if loc_val else ([], [])
        # if DEBUG: print(varname, self.colormaps[varname], values)
        return dict(
            type='choroplethmapbox',
            name=name+'_contours',
            geojson=geojson,
            z=values,
            ids=locations,
            locations=locations,
            zmin=bounds[0],
            zmax=bounds[-1],
            colorscale=self.colormaps[varname.upper()],
            showscale=False,
            showlegend=False,
            hoverinfo='none',
            marker=dict(
                opacity=0.6,
                line_width=0,
            ),
            colorbar=None,
        )

    def generate_var_tstep_trace_leaflet(self, varname=None, tstep=0):
        """ Generate trace to be added to data, per variable and timestep """
        colorscale = COLORS
        xlon, ylat, val = self.set_data(varname, tstep)
        df = pd.DataFrame(np.array([xlon, ylat, val]).T.round(2), columns=['lon', 'lat', 'value'])
        dicts = df.to_dict('rows')
        for item in dicts:
            item["tooltip"] = \
                    "Lat {:.2f} Lon {:.2f} Val {:.2f}".format(item['lat'], item['lon'], item['value'])
        geojson = dlx.dicts_to_geojson(dicts, lon="lon")
        # geobuf = dlx.geojson_to_geobuf(geojson)

        if DEBUG: print("GEOBUF CREATED ***********")
        # Geojson rendering logic, must be JavaScript as it is executed in clientside.
        ns = Namespace("forecastTab", "forecastMaps")
        point_to_layer = ns("pointToLayer")
        bind_tooltip = ns("bindTooltip")
        if DEBUG: print("BIND", str(bind_tooltip))
        # Create geojson.
        # return dl.GeoJSON(data=geobuf, format="geobuf",
        return dl.GeoJSON(data=geojson,
                options=dict(
                    pointToLayer=point_to_layer,
                    # onEachFeature=bind_tooltip,
                ),  # how to draw points
                hideout=dict(
                    colorProp='value',
                    circleOptions=dict(
                        fillOpacity=0,
                        stroke=False,
                        radius=0),
                    min=0,
                    max=val.max(),
                    colorscale=colorscale)
                )
        

    def generate_var_tstep_trace(self, varname=None, tstep=0):
        """ Generate trace to be added to data, per variable and timestep """
        if not varname:
            return dict(
                type='scattermapbox',
                # below='',
                lon=[15],
                lat=[30],
                hoverinfo='none',
                opacity=0,
                showlegend=False,
                marker=dict(
                    showscale=False,
                    size=0,
                    colorbar=None,
                ),
            )
        xlon, ylat, val = self.set_data(varname, tstep)
        if self.model in OBS:
            name = OBS[self.model]['name']
        else:
            name = MODELS[self.model]['name']
        if DEBUG: print("***", name, "***")
        return dict(
            type='scattermapbox',
            # below='',
            lon=xlon,
            lat=ylat,
            text=val,
            name=name,
            hovertemplate="lon: %{lon:.2f}<br>lat: %{lat:.2f}<br>" +
            "value: %{text:.2f}",
            opacity=0.6,
            showlegend=False,
            marker=dict(
                # autocolorscale=True,
                showscale=False,
                color=val,
                # opacity=0.6,
                size=0,
                colorscale=self.colormaps[varname.upper()],
                cmin=self.bounds[varname.upper()][0],
                cmax=self.bounds[varname.upper()][-1],
                colorbar=None,
            ),
        )

    def get_title(self, varname, tstep=0):
        """ return title according to the date """
        if self.model in OBS:
            name = OBS[self.model]['name']
            title = OBS[self.model]['title']
        else:
            name = MODELS[self.model]['name']
            title = VARS[varname]['title']
        rdatetime = self.retrieve_cdatetime(tstep=0)
        cdatetime = self.retrieve_cdatetime(tstep)
        return r'{} {}'.format(name, title % {
            'rhour':  rdatetime.strftime("%H"),
            'rday':   rdatetime.strftime("%d"),
            'rmonth': rdatetime.strftime("%b"),
            'ryear':  rdatetime.strftime("%Y"),
            'shour':  cdatetime.strftime("%H"),
            'sday':   cdatetime.strftime("%d"),
            'smonth': cdatetime.strftime("%b"),
            'syear':  cdatetime.strftime("%Y"),
            'step':   "{:02d}".format(tstep*FREQ),
        })

    def hour_to_step(self, hour):
        """ Convert hour to relative tstep """
        cdatetime = self.rdatetime.date() + relativedelta(hours=hour)

        for step in range(self.tim.size):
            if self.retrieve_cdatetime(step) == cdatetime:
                return step

        return 0

    def retrieve_var_tstep(self, varname=None, tstep=0, hour=None, static=True, aspect=(1,1), center=None, selected_tiles='carto-positron'):
        """ run plot """

        if hour is not None:
            tstep = int(self.hour_to_step(hour))
        else:
            tstep = int(tstep)

        if varname is not None and self.model in OBS:
            varname = OBS[self.model]['obs_var']

        if DEBUG: print('VARNAME', varname)

        if varname and self.filedir:
            if DEBUG: print('Adding contours ...')
            try:
                cont_time = time.time()
                geojson_contours, colorbar = self.generate_contour_tstep_trace_leaflet(varname, tstep)
                if DEBUG: print("****** CONTOURS EXEC TIME", str(time.time() - cont_time))
            except Exception as err:
                if DEBUG: print("----------- ERROR:", str(err))
                self.filedir = None
                # if DEBUG: print('ERROR: geojson {}'.format(geojson_url))
                data = {
                        "type": "FeatureCollection",
                        "features": []
                        }
                geojson_contours = dl.GeoJSON(
                        data=data,
                        )
                colorbar = None
        else:
            if DEBUG: print('Adding one point ...')
            data = {
                    "type": "FeatureCollection",
                    "features": []
                    }
            geojson_contours = dl.GeoJSON(
                data=data,
            )
            colorbar = None

        if DEBUG: print("ASPECT", aspect)
        center = self.get_center(center)
        if DEBUG: print("CENTER", center)


        if DEBUG: print('Update layout ...')
        if not varname:
            fig_title=html.P("")
            info_style = {"position": "absolute", "top": "10px", "left": "10px", "z-index": "1000"}
        elif varname and not self.filedir:
            fig_title = html.P(html.B("DATA NOT AVAILABLE"))
            info_style = {"position": "absolute", "top": "10px", "left": "10px", "z-index": "1000"}
        else:
            fig_title = html.P(html.B(
                [
                    item for sublist in self.get_title(varname, tstep).split('<br>') for item in [sublist, html.Br()]
                ][:-1]
            ))
            info_style = {"position": "absolute", "top": "10px", "left": "10px", "z-index": "1000"}
        info = html.Div(
            children=fig_title,
            id="{}-info".format(self.model),
            className="info",
            style=info_style
        )

        fig = dl.Map(children=[
            dl.TileLayer(
                id=dict(
                    tag="model-tile-layer",
                    index=self.model
                ),
                url=STYLES[selected_tiles]['url'],
                attribution=STYLES[selected_tiles]['attribution']
            ),
            dl.LayerGroup(
                # children=[],
                id=dict(
                    tag="model-map-layer",
                    index=self.model
                )
            ),
            dl.FullscreenControl(
                position='topright',
            ),
            geojson_contours,
            colorbar,
            info
            ],
            zoom=4.5-(aspect[0]),
            center=center,
            id=dict(
                tag='model-map',
                index=self.model
                )
        )
        if DEBUG: print("*** FIGURE EXECUTION TIME: {} ***".format(str(time.time() - self.st_time)))
        return fig


class ScoresFigureHandler(object):
    """ Class to manage the figure creation """

    def __init__(self, network, statistic, selection=None):

        if network == 'aeronet':
            self.sites = pd.read_table(os.path.join('./conf/',
                OBS[network]['sites']), delimiter=r"\s+", engine='python')
            self.size = 15
        else:
            self.sites = None
            self.size = 7

        filedir = OBS[network]['path']
        filename = "{}_{}.h5".format(selection, statistic)
        tab_name = "{}_{}".format(statistic, selection)
        filepath = os.path.join(filedir, "h5", filename)
        if DEBUG: print('SCORES filepath', filepath, 'SELECTION', tab_name)
        self.dframe = pd.read_hdf(filepath, tab_name).replace('_', ' ', regex=True)

        months = ' - '.join([datetime.strptime(sel, '%Y%m').strftime("%B %Y") for sel in selection.split('_')])

        self.title = """{model} {score}<br>{selection}""".format(
                score=STATS[statistic], model='{model}', selection=months)
        self.xlon = np.array([-25, 60])
        self.ylat = np.array([0, 65])
        self.stat = statistic

    def get_mapbox_style_buttons(self):
        """ Relayout map with different styles """
        return dict(
            direction="up",
            buttons=list([self.get_mapbox(style, relayout=True) for style in
                          STYLES.keys()]),
            # pad={"r": 0, "t": 0},
            showactive=True,
            x=0.9,
            y=0.09,
            xanchor="right",
            yanchor="top",
        )

    def get_mapbox(self, style='carto-positron', relayout=False, zoom=2.8, center=None):
        """ Returns mapbox layout """
        if center is None and hasattr(self, 'ylat'):
            center = go.layout.mapbox.Center(
                lat=(self.ylat.max()-self.ylat.min())/2 +
                self.ylat.min(),
                lon=(self.xlon.max()-self.xlon.min())/2 +
                self.xlon.min(),
            )
        elif center is not None:
            center = go.layout.mapbox.Center(center)
        else:
            center = go.layout.mapbox.Center({'lat': 30, 'lon': 15})
        mapbox_dict = dict(
            uirevision=True,
            style=style,
            bearing=0,
            center=center,
            pitch=0,
            zoom=zoom
        )

        if not relayout:
            return mapbox_dict

        return dict(
            args=["mapbox", mapbox_dict],
            label=STYLES[style].capitalize(),
            method="relayout"
        )

    def get_updated_trace(self, varname, tstep=0):
        """ Get updated trace """
        return dict(
            args=["scattermapbox", self.generate_trace(varname,
                                                       tstep)],
            label=VARS[varname]['name'],
            method="restyle"
        )


    def generate_trace(self, xlon, ylat, stats, vals):
        """ Generate trace to be added to data, per variable and timestep """
        if stats is None:
            hovertemplate="lon: %{lon:.2f}<br>lat: %{lat:.2f}<br>value: %{text}"
        else:
            hovertemplate="lon: %{lon:.2f}<br>lat: %{lat:.2f}<br>value: %{text}<br>station: %{customdata}"
        name = '{} score'.format(STATS[self.stat])
        return dict(
            type='scattermapbox',
            lon=xlon,
            lat=ylat,
            text=vals,
            customdata=stats,
            name=name,
            hovertemplate=hovertemplate,
            opacity=0.8,
            mode='markers',
            showlegend=False,
            marker=dict(
                showscale=True,
                # colorscale=STATS_CONF[self.stat]['cmap'],
                colorscale=get_colorscale(STATS_CONF[self.stat]['bounds'], STATS_CONF[self.stat]['cmap']),
                cmax=STATS_CONF[self.stat]['max'],
                cmin=STATS_CONF[self.stat]['min'],
                cmid=STATS_CONF[self.stat]['mid'],
                color=vals,
                size=self.size,
                colorbar=dict(
                    x=0.94,
                    y=0.45,
                    len=0.9,
                    tickmode='array',
                    tickvals=STATS_CONF[self.stat]['bounds'],
                    thickness=20,
                )
            ),
        )

    def retrieve_scores(self, model, aspect=(1,1), center=None):
        """ run plot """

        if self.sites is not None:
            stations = [st for st in self.sites['SITE']]
            for site in stations:
                self.dframe.loc[self.dframe['station'] == site, 'lon'] = \
                    str(self.sites.loc[self.sites['SITE'] == site, 'LONGITUDE'].values[0].round(2))
                self.dframe.loc[self.dframe['station'] == site, 'lat'] = \
                    str(self.sites.loc[self.sites['SITE'] == site, 'LATITUDE'].values[0].round(2))
        self.dframe = self.dframe.replace('-', np.nan)
        # self.dframe.dropna(inplace=True)
        if DEBUG: print(self.dframe.head(), model)
        if self.sites is not None:
            xlon, ylat, stats, vals = self.dframe[['lon', 'lat', 'station', model]].dropna().values.T
        else:
            xlon, ylat, vals = self.dframe[['lon', 'lat', model]].dropna().values.T
            stats = None

        self.fig = go.Figure()
        if DEBUG: print('Adding SCORES points ...', xlon, ylat, vals)
        self.fig.add_trace(self.generate_trace(xlon.astype(float), ylat.astype(float), stats, vals.astype(float)))

        if DEBUG: print('Update layout ...', self.title.format(model=MODELS[model]['name']))
        fig_title=dict(text='{}'.format(self.title.format(model=MODELS[model]['name'])),
                       xanchor='left',
                       yanchor='top',
                       x=0.01, y=0.95)

        self.fig.update_layout(
            title=fig_title,
            uirevision=True,
            autosize=True,
            hovermode="closest",        # highlight closest point on hover
            mapbox=self.get_mapbox(zoom=2.8-(0.5*aspect[0]), center=center),
            font_size=12-(0.5*aspect[0]),
            # width="100%",
            legend=dict(
                x=0.01,
                y=0.9,
                bgcolor="rgba(0,0,0,0)"
            ),
            updatemenus=[
                # get_animation_buttons(),
                # self.get_mapbox_style_buttons(),
                # self.get_variable_dropdown_buttons(),
            ],
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
        )

        # if DEBUG: print('Returning fig of size {}'.format(sys.getsizeof(self.fig)))
        return self.fig


class VisFigureHandler(object):
    """ Class to manage the figure creation """

    def __init__(self, selected_date=None):

        self.path_tpl = '/data/daily_dashboard/obs/visibility/{year}/{month}/{year}{month}{day}{tstep0:02d}{tstep1:02d}_visibility.csv'
        self.title = """Visibility reduced by airborne dust<br>{date} {tstep0:02d}-{tstep1:02d} UTC"""
        self.xlon = np.array([-25, 60])
        self.ylat = np.array([0, 65])
        self.ec = 'none'
        self.size = 80
        self.freq = 6
        self.colors = ('#714921', '#da7230', '#fcd775', 'CadetBlue')
        self.labels = ("<1 km", "1 - 2 km", "2 - 5 km", "uncertain")
        self.markers = ('o', 'o', 'o', '^')

        if selected_date:
            self.selected_date_plain = selected_date

            self.selected_date = datetime.strptime(
                selected_date, "%Y%m%d").strftime("%Y-%m-%d")

        else:
            self.selected_date_plain = None
            self.selected_date = None

    def get_mapbox_style_buttons(self):
        """ Relayout map with different styles """
        return dict(
            direction="up",
            buttons=list([self.get_mapbox(style, relayout=True) for style in
                          STYLES.keys()]),
            # pad={"r": 0, "t": 0},
            showactive=True,
            x=0.9,
            y=0.09,
            xanchor="right",
            yanchor="top",
        )

    def get_mapbox(self, style='carto-positron', relayout=False, zoom=2.8, center=None):
        """ Returns mapbox layout """
        if center is None and hasattr(self, 'ylat'):
            center = go.layout.mapbox.Center(
                lat=(self.ylat.max()-self.ylat.min())/2 +
                self.ylat.min(),
                lon=(self.xlon.max()-self.xlon.min())/2 +
                self.xlon.min(),
            )
        elif center is not None:
            center = go.layout.mapbox.Center(center)
        else:
            center = go.layout.mapbox.Center({'lat': 30, 'lon': 15})
        mapbox_dict = dict(
            uirevision=True,
            style=style,
            bearing=0,
            center=center,
            pitch=0,
            zoom=zoom
        )

        if not relayout:
            return mapbox_dict

        return dict(
            args=["mapbox", mapbox_dict],
            label=STYLES[style].capitalize(),
            method="relayout"
        )

    def get_updated_trace(self, varname, tstep=0):
        """ Get updated trace """
        return dict(
            args=["scattermapbox", self.generate_var_tstep_trace(varname,
                                                                 tstep)],
            label=VARS[varname]['name'],
            method="restyle"
        )

    def set_data(self, tstep=0):
        """ Set time dependent data """
        tstep0 = tstep
        tstep1 = tstep + self.freq

        year = datetime.strptime(self.selected_date_plain, '%Y%m%d').strftime('%Y')
        month = datetime.strptime(self.selected_date_plain, '%Y%m%d').strftime('%m')
        day = datetime.strptime(self.selected_date_plain, '%Y%m%d').strftime('%d')

        data = pd.read_table(self.path_tpl.format(year=year, month=month, day=day, tstep0=tstep0, tstep1=tstep1))

        # uncertain
        cx = np.where((data['WW'].astype(str) == "HZ") | (data['WW'].astype(str) == "5")| (data['WW'].astype(str) == "05"))

        # vis <= 1km
        c0t = np.where((data['VV'] <= 1000))[0]
        c0x = np.where([c0t == i for i in cx[0]])[-1]
        c0 = (np.delete(c0t, c0x),)

        # vis 1km <= 2km
        c1t = np.where((data['VV'] > 1000) & (data['VV'] <= 2000))[0]
        c1x = np.where([c1t == i for i in cx[0]])[-1]
        c1 = (np.delete(c1t, c1x),)

        # vis 2km <= 5km
        c2t = np.where((data['VV'] > 2000) & (data['VV'] <= 5000))[0]
        c2x = np.where([c2t == i for i in cx[0]])[-1]
        c2 = (np.delete(c2t, c2x),)

        xlon = data['LON'].values
        ylat = data['LAT'].values
        stats = data['STATION'].values

        return xlon, ylat, stats, (c0, c1, c2, cx)

    def generate_var_tstep_trace(self, xlon, ylat, stats, value, color, label, marker, tstep=0):
        """ Generate trace to be added to data, per variable and timestep """
        if tstep is None:
            return dict(
                type='scattermapbox',
                lon=[15],
                lat=[30],
                hoverinfo='none',
                opacity=0,
                showlegend=False,
                marker=dict(
                    showscale=False,
                    size=0,
                    colorbar=None,
                ),
            )
        name = 'visibility {}'.format(label)
        if value[0].size == 0:
            xlon_val = [-180]
            ylat_val = [-90]
            stat_val = 'none'
        else:
            xlon_val = xlon[value]
            ylat_val = ylat[value]
            stat_val = stats[value]
        if DEBUG: print('VIS ___', xlon_val, ylat_val)
        return dict(
            type='scattermapbox',
            lon=xlon_val,
            lat=ylat_val,
            text=stat_val,
            name=name,
            hovertemplate="lon: %{lon:.2f}<br>lat: %{lat:.2f}<br>station: %{text}",
            opacity=0.7,
            mode='markers',
            showlegend=True,
            marker=dict(
                showscale=False,
                color=color,
                size=15,
                colorbar=None,
                #symbol='triangle',
            ),
        )

    def get_title(self, tstep=0):
        """ return title according to the date """
        tstep0 = tstep
        tstep1 = tstep + self.freq
        fdate = datetime.strptime(self.selected_date_plain, '%Y%m%d').strftime('%d %B %Y')
        return self.title.format(date=fdate, tstep0=tstep0, tstep1=tstep1)

    def retrieve_var_tstep(self, tstep=0, hour=None, static=True, aspect=(1,1), center=None):
        """ run plot """

        tstep = int(tstep)

        xlon, ylat, stats, vals = self.set_data(tstep)
        self.fig = go.Figure()
        if tstep is not None:
            for value, color, label, marker in zip(vals, self.colors, self.labels, self.markers):
                if DEBUG: print('Adding VIS points ...', xlon, ylat, value, color, label, marker, tstep)
                self.fig.add_trace(self.generate_var_tstep_trace(xlon, ylat, stats, value, color, label, marker, tstep))
        else:
            if DEBUG: print('Adding one point ...')
            self.fig.add_trace(self.generate_var_tstep_trace())

        # axis_style = dict(
        #     zeroline=False,
        #     showline=False,
        #     showgrid=True,
        #     ticks='',
        #     showticklabels=False,
        # )

        if DEBUG: print('Update layout ...', self.get_title(tstep))
        if tstep is not None:
            fig_title=dict(text='{}'.format(self.get_title(tstep)),
                           xanchor='left',
                           yanchor='top',
                           x=0.01, y=0.95)
        else:
            fig_title={}

        self.fig.update_layout(
            title=fig_title,
            uirevision=True,
            autosize=True,
            hovermode="closest",        # highlight closest point on hover
            mapbox=self.get_mapbox(zoom=2.8-(0.5*aspect[0]), center=center),
            font_size=12-(0.5*aspect[0]),
            # width="100%",
            legend=dict(
                x=0.01,
                y=0.9,
                bgcolor="rgba(0,0,0,0)"
            ),
            updatemenus=[
                # get_animation_buttons(),
                # self.get_mapbox_style_buttons(),
                # self.get_variable_dropdown_buttons(),
            ],
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
        )

        # if DEBUG: print('Returning fig of size {}'.format(sys.getsizeof(self.fig)))
        return self.fig


class ProbFigureHandler(object):
    """ Class to manage the figure creation """

    def __init__(self, var=None, prob=None, selected_date=None):
        """ """

        if var is None:
            var = DEFAULT_VAR

        self.varname = var

        probs = PROB[var]['prob_thresh']
        if prob is None:
            prob = probs[0]

        self.bounds = range(10, 110, 10)

        self.prob = prob

        geojson_path = PROB[var]['geojson_path']
        geojson_file = PROB[var]['geojson_template']
        netcdf_path = PROB[var]['netcdf_path']
        netcdf_file = PROB[var]['netcdf_template']

        self.geojson = os.path.join(geojson_path, geojson_file).format(prob=prob, date=selected_date, var=var)
        self.filepath = os.path.join(netcdf_path, netcdf_file).format(prob=prob, date=selected_date, var=var)

        if os.path.exists(self.filepath):
            self.input_file = nc_file(self.filepath)

            if 'lon' in self.input_file.variables:
                lon = self.input_file.variables['lon'][:]
                lat = self.input_file.variables['lat'][:]
            else:
                lon = self.input_file.variables['longitude'][:]
                lat = self.input_file.variables['latitude'][:]
            time_obj = self.input_file.variables['time']
            self.tim = time_obj[:]
            self.what, _, rdate, rtime = time_obj.units.split()[:4]
            if len(rtime) > 5:
                rtime = rtime[:5]
            self.rdatetime = datetime.strptime("{} {}".format(rdate, rtime),
                                               "%Y-%m-%d %H:%M")
            varlist = [var for var in self.input_file.variables if var in VARS]
            self.xlon, self.ylat = np.meshgrid(lon, lat)

        self.colormaps = {
            self.varname: get_colorscale(self.bounds, COLORMAP_PROB)
        }

        if selected_date:
            self.selected_date_plain = selected_date

            self.selected_date = datetime.strptime(
                selected_date, "%Y%m%d").strftime("%Y-%m-%d")

        self.fig = None

    def get_mapbox_style_buttons(self):
        """ Relayout map with different styles """
        return dict(
            direction="up",
            buttons=list([self.get_mapbox(style, relayout=True) for style in
                          STYLES.keys()]),
            # pad={"r": 0, "t": 0},
            showactive=True,
            x=0.9,
            y=0.09,
            xanchor="right",
            yanchor="top",
        )

    def get_mapbox(self, style='carto-positron', relayout=False, zoom=2.8):
        """ Returns mapbox layout """
        if hasattr(self, 'ylat'):
            center = go.layout.mapbox.Center(
                lat=(self.ylat.max()-self.ylat.min())/2 +
                self.ylat.min(),
                lon=(self.xlon.max()-self.xlon.min())/2 +
                self.xlon.min(),
            )
        else:
            center = go.layout.mapbox.Center({'lat': 30, 'lon': 15})
        mapbox_dict = dict(
            uirevision=True,
            style=style,
            bearing=0,
            center=center,
            pitch=0,
            zoom=zoom
        )

        if not relayout:
            return mapbox_dict

        return dict(
            args=["mapbox", mapbox_dict],
            label=STYLES[style].capitalize(),
            method="relayout"
        )

    def get_updated_trace(self, varname, tstep=0):
        """ Get updated trace """
        return dict(
            args=["scattermapbox", self.generate_var_tstep_trace(varname,
                                                                 tstep)],
            label=VARS[varname]['name'],
            method="restyle"
        )

    def set_data(self, varname, tstep=0):
        """ Set time dependent data """
        mul = 1  # VARS[varname]['mul']
        var = self.input_file.variables[varname][tstep]*mul
        idx = np.where(var.ravel() >= VARS[varname]['bounds'][0])  # !=-9.e+33)
        xlon = self.xlon.ravel()[idx]
        ylat = self.ylat.ravel()[idx]
        var = var.ravel()[idx]

        return xlon, ylat, var

    def retrieve_cdatetime(self, tstep=0):
        tim = int(self.tim[tstep])
        """ Retrieve data from NetCDF file """
        if self.what == 'days':
            cdatetime = self.rdatetime + relativedelta(days=tim)
        elif self.what == 'hours':
            cdatetime = self.rdatetime + relativedelta(hours=tim)
        elif self.what == 'minutes':
            cdatetime = self.rdatetime + relativedelta(minutes=tim)
        elif self.what == 'seconds':
            cdatetime = self.rdatetime + relativedelta(seconds=tim)

        return cdatetime

    def generate_contour_tstep_trace(self, varname, tstep=0):
        """ Generate trace to be added to data, per variable and timestep """
        if varname is None:
            varname = self.varname

        geojson_file = self.geojson.format(step=tstep)

        if os.path.exists(geojson_file):
            if DEBUG: print('GEOJSON PROB', geojson_file)
            geojson = json.load(open(geojson_file))
        else:
            if DEBUG: print('ERROR', geojson_file, 'not available')
            geojson = {
                    "type": "FeatureCollection",
                    "features": []
                    }

        name = VARS[varname]['name']
        bounds = self.bounds
        loc_val = [
            (
                feature['id'],
                np.around(feature['properties']['value'], 2),
            )
            for feature in geojson['features']
            if feature['geometry']['coordinates']
        ]
        locations, values = np.array(loc_val).T if loc_val else ([], [])
        if DEBUG: print("*****", varname, self.colormaps[varname], values)
        return dict(
            type='choroplethmapbox',
            name=name+'_contours',
            geojson=geojson,
            z=values,
            ids=locations,
            locations=locations,
            zmin=bounds[0],
            zmax=bounds[-1],
            colorscale=self.colormaps[varname],
            showscale=False,
            showlegend=False,
            hoverinfo='none',
            marker=dict(
                opacity=0.6,
                line_width=0,
            ),
            colorbar=None,
#                 {
#                     "borderwidth": 0,
#                     "outlinewidth": 0,
#                     "thickness": 15,
#                     "tickfont": {"size": 14},
#                     "tickvals": self.bounds[varname][:-1],
#                     "tickmode": "array",
#                     "x": 0.95,
#                     "y": 0.5,
#                 },
        )

    def generate_var_tstep_trace(self, varname=None, tstep=0):
        """ Generate trace to be added to data, per variable and timestep """
        if varname is None:
            return dict(
                type='scattermapbox',
                below='',
                lon=[15],
                lat=[30],
                hoverinfo='none',
                opacity=0,
                showlegend=False,
                marker=dict(
                    showscale=False,
                    size=0,
                    colorbar=None,
                ),
            )
        varname = self.varname
        xlon, ylat, val = self.set_data(varname, tstep)
        name = VARS[varname]['name']
        return dict(
            type='scattermapbox',
            below='',
            lon=xlon,
            lat=ylat,
            text=val,
            name=name,
            hovertemplate="lon: %{lon:.2f}<br>lat: %{lat:.2f}<br>" +
            "value: %{text:.2f}",
            opacity=0.6,
            showlegend=False,
            marker=dict(
                # autocolorscale=True,
                showscale=False,
                color=val,
                # opacity=0.6,
                size=0,
                colorscale=self.colormaps[varname],
                cmin=self.bounds[0],
                cmax=self.bounds[-1],
                colorbar=None,
            ),
        )

    def get_title(self, varname, tstep=0):
        """ return title according to the date """
        tstep += 1
        rdatetime = self.rdatetime
        cdatetime = self.retrieve_cdatetime(tstep)
        return PROB[varname]['title'].format(
            prob=self.prob,
            rday=rdatetime.strftime("%d"),
            rmonth=rdatetime.strftime("%b"),
            ryear=rdatetime.strftime("%Y"),
            sday=cdatetime.strftime("%d"),
            smonth=cdatetime.strftime("%b"),
            syear=cdatetime.strftime("%Y"),
        )

    def retrieve_var_tstep(self, varname=None, day=0, static=True, aspect=(1,1)):
        """ run plot """
        tstep = int(day)
        if varname is None:
            varname = self.varname
        if DEBUG: print("***", varname, day, static, self.geojson, self.filepath)
        self.fig = go.Figure()
        if varname and os.path.exists(self.geojson.format(step=day)):
            if DEBUG: print('Adding contours ...')
            self.fig.add_trace(self.generate_contour_tstep_trace(varname, tstep))
        if varname and os.path.exists(self.filepath) and static:
            if DEBUG: print('Adding points ...')
            self.fig.add_trace(self.generate_var_tstep_trace(varname, tstep))
        elif varname is None or not os.path.exists(self.filepath):
            if DEBUG: print('Adding one point ...')
            self.fig.add_trace(self.generate_var_tstep_trace())

        # axis_style = dict(
        #     zeroline=False,
        #     showline=False,
        #     showgrid=True,
        #     ticks='',
        #     showticklabels=False,
        # )

        if DEBUG: print('Update layout ...')
        if not varname:
            if DEBUG: print('ONE')
            fig_title=dict(text='',
                           xanchor='center',
                           yanchor='middle',
                           x=0.5, y=0.5)
        elif varname and not os.path.exists(self.filepath):
            if DEBUG: print('TWO')
            fig_title=dict(text='<b>DATA NOT AVAILABLE</b>',
                           xanchor='center',
                           yanchor='middle',
                           x=0.5, y=0.5)
        else:
            if DEBUG: print('THREE')
            fig_title=dict(text='{}'.format(self.get_title(varname, tstep)),
                           xanchor='left',
                           yanchor='top',
                           x=0.01, y=0.95)
            if DEBUG: print('ADD IMAGES')
            if varname and varname in VARS:
                ypos = 0.9-(aspect[0]/30)
                size = 0.18+(aspect[0]/6)
                if DEBUG: print("YPOS", aspect[0], ypos)
                self.fig.add_layout_image(
                    dict(
                        source=Image.open(PROB[varname]['image_scale']),
                        xref="paper", yref="paper",
                        x=0.01, y=ypos,
                        sizex=size, sizey=size,
                        xanchor="left", yanchor="top",
                        layer='above',
                    ))
#        if varname and os.path.exists(self.filepath):
#            fig_title=dict(text='{}'.format(self.get_title(varname, tstep)),
#                           xanchor='left',
#                           yanchor='top',
#                           x=0.01, y=0.95)
#        else:
#            fig_title={}
#        size = 0.5
#        ypos = 1.05
#        self.fig.add_layout_image(
#            dict(
#                source=Image.open(PROB[varname]['image_scale']),
#                xref="paper", yref="paper",
#                x=0.01, y=ypos,
#                sizex=size, sizey=size,
#                xanchor="left", yanchor="top",
#                layer='above',
#            ))
        self.fig.update_layout(
            title=fig_title,
            uirevision=True,
            autosize=True,
            hovermode="closest",        # highlight closest point on hover
            mapbox=self.get_mapbox(zoom=2.8-(0.5*aspect[0])),
            font_size=12-(0.5*aspect[0]),
            # width="100%",
            updatemenus=[
                # get_animation_buttons(),
                # self.get_mapbox_style_buttons(),
                # self.get_variable_dropdown_buttons(),
            ],
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
        )

        # if DEBUG: print('Returning fig of size {}'.format(sys.getsizeof(self.fig)))
        return self.fig


class WasFigureHandler(object):
    """ Class to manage the figure creation """

    def __init__(self, was='burkinafaso', model='median', variable='SCONC_DUST', selected_date=None):
        """ Initialize WasFigureHandler with shapefile and netCDF data """
        self.model = model
        self.was = was
        self.variable = variable

        if self.was:
            # read shapefile
            if DEBUG: print(WAS[self.was]['shp'])
            self.was_df = gpd.read_file(WAS[self.was]['shp'])
            self.was_df['lon_lat'] = self.was_df['geometry'].apply(lambda row: row.centroid)
            self.was_df['LON'] = self.was_df['lon_lat'].apply(lambda row: row.x)
            self.was_df['LAT'] = self.was_df['lon_lat'].apply(lambda row: row.y)
            self.was_df = self.was_df.drop('lon_lat', axis=1)
            self.wlon = self.was_df['LON']
            self.wlat = self.was_df['LAT']

        if self.model and selected_date:
            # read nc file
            if DEBUG: print("MODEL", model)
            filepath = NETCDF_TEMPLATE.format(
                MODELS[self.model]['path'],
                selected_date,
                MODELS[self.model]['template']
            )
            if os.path.exists(filepath):
                self.input_file = nc_file(filepath)
                if 'lon' in self.input_file.variables:
                    lon = self.input_file.variables['lon'][:]
                    lat = self.input_file.variables['lat'][:]
                else:
                    lon = self.input_file.variables['longitude'][:]
                    lat = self.input_file.variables['latitude'][:]
                time_obj = self.input_file.variables['time']
                self.tim = time_obj[:]
                self.what, _, rdate, rtime = time_obj.units.split()[:4]
                if len(rtime) > 5:
                    rtime = rtime[:5]
                self.rdatetime = datetime.strptime("{} {}".format(rdate, rtime),
                                                   "%Y-%m-%d %H:%M")
                varlist = [var for var in self.input_file.variables if var in VARS]

                self.xlon, self.ylat = np.meshgrid(lon, lat)
                self.vardata = self.input_file.variables[variable][:]*1e9
            else:
                self.input_file = None

#         self.bounds = {
#             varname: np.array(VARS[varname]['bounds']).astype('float32')
#             for varname in varlist
#         }
# 
#         self.colormaps = {
#             varname: get_colorscale(self.bounds[varname], COLORMAP)
#             for varname in varlist
#         }

        if selected_date:
            self.selected_date_plain = selected_date

            self.selected_date = datetime.strptime(
                selected_date, "%Y%m%d").strftime("%Y-%m-%d")

        self.fig = None

    def get_mapbox_style_buttons(self):
        """ Relayout map with different styles """
        return dict(
            direction="up",
            buttons=list([self.get_mapbox(style, relayout=True) for style in
                          STYLES.keys()]),
            # pad={"r": 0, "t": 0},
            showactive=True,
            x=0.9,
            y=0.09,
            xanchor="right",
            yanchor="top",
        )

    def get_mapbox(self, style='carto-positron', relayout=False, zoom=1):
        """ Returns mapbox layout """
        if hasattr(self, 'ylat'):
            center = go.layout.mapbox.Center(
                lat=(self.wlat.max()-self.wlat.min())/2 +
                self.wlat.min(),
                lon=(self.wlon.max()-self.wlon.min())/2 +
                self.wlon.min(),
            )
        else:
            center = go.layout.mapbox.Center({'lat': 30, 'lon': 15})

        mapbox_dict = dict(
            uirevision=True,
            style=style,
            bearing=0,
            center=center,
            pitch=0,
            zoom=zoom
        )

        if not relayout:
            return mapbox_dict

        return dict(
            args=["mapbox", mapbox_dict],
            label=STYLES[style].capitalize(),
            method="relayout"
        )

    def get_updated_trace(self, varname, tstep=0):
        """ Get updated trace """
        return dict(
            args=["scattermapbox", self.generate_var_tstep_trace(varname,
                                                                 tstep)],
            label=VARS[varname]['name'],
            method="restyle"
        )

    def set_data(self, day=1):
        """ Set time dependent data """

        d_idx = []
        d_date = self.rdatetime + relativedelta(days=day)

        for n, tstep in enumerate(self.tim[:]):
            ctime = (self.rdatetime + relativedelta(hours=float(tstep)))
            if ctime.strftime("%Y%m%d") == d_date.strftime("%Y%m%d"):
                d_idx.append(n)

        return self.vardata[d_idx,:,:].max(axis=0)

    def get_regions_data(self, day=1):
        input_dir = WAS[self.was]['path'].format(was=self.was, date=self.selected_date_plain)
        input_file = WAS[self.was]['template'].format(date=self.selected_date_plain, var=self.variable)

        input_path = os.path.join(input_dir, input_file)

        if os.path.exists(input_path):
            df = pd.read_hdf(input_path, 'was_{}'.format(self.selected_date_plain)).set_index('day')

        names = []
        colors = []
        definitions = []
        if not hasattr(self, 'xlon'):
            return names, colors, definitions

        names, colors, definitions = df.loc['Day{}'.format(day)].values.T
        # print(names, colors, definitions)
        return names, colors, definitions

    def retrieve_cdatetime(self, tstep=0):
        tim = int(self.tim[tstep])
        """ Retrieve data from NetCDF file """
        if self.what == 'days':
            cdatetime = self.rdatetime + relativedelta(days=tim)
        elif self.what == 'hours':
            cdatetime = self.rdatetime + relativedelta(hours=tim)
        elif self.what == 'minutes':
            cdatetime = self.rdatetime + relativedelta(minutes=tim)
        elif self.what == 'seconds':
            cdatetime = self.rdatetime + relativedelta(seconds=tim)

        return cdatetime

    def generate_contour_tstep_trace(self, day=1):
        """ Generate trace to be added to data, per variable and timestep """

        if hasattr(self, 'was_df'):
            geojson = orjson.loads(self.was_df['geometry'].to_json())
        else:
            geojson = {
                    "type": "FeatureCollection",
                    "features": []
                    }

            return dict(
                        type='choroplethmapbox',
                        name='',  # str(self.was)+'_contours',
                        geojson=geojson,
                    )
        colormap =  list(WAS[self.was]['colors'].keys())
        names, colors, definitions = self.get_regions_data(day=day)
        loc_val = [
            (
                feature['id'],
                colormap.index(color),
            )
            for feature, color in zip(geojson['features'], colors)
            if feature['geometry']['coordinates']
        ]
        locations, values = np.array(loc_val).T if loc_val else ([], [])
        if DEBUG: print(locations, '--', values)
        # if DEBUG: print(varname, self.colormaps[varname], values)
        # colormap function of values
        uniques = np.unique(values)
        colormap = [colormap[int(i)] for i in np.unique(values)]
        if DEBUG: print(colormap)
        return dict(
            type='choroplethmapbox',
            name='',  # str(self.was)+'_contours',
            geojson=geojson,
            z=values,
            ids=locations,
            locations=locations,
            showscale=False,
            showlegend=True,
            customdata=["Region: {}<br>Warning level: {}".format(name,
                definition) for name, definition in zip(names, definitions)],
            hovertemplate="%{customdata}",
            colorscale=get_colorscale(np.arange(len(colormap)), ListedColormap(colormap), True),
            marker=dict(
                opacity=0.6,
                line_width=0.5,
                line_color='white',
            ),
            colorbar=None,
        )

    def get_title(self, day=1):
        """ return title according to the date """
        rdatetime = self.rdatetime
        cdatetime = self.rdatetime + relativedelta(days=day)
        return r'{}'.format(WAS[self.was]['title'] % {
            'rhour':  rdatetime.strftime("%H"),
            'rday':   rdatetime.strftime("%d"),
            'rmonth': rdatetime.strftime("%b"),
            'ryear':  rdatetime.strftime("%Y"),
            'shour':  cdatetime.strftime("%H"),
            'sday':   cdatetime.strftime("%d"),
            'smonth': cdatetime.strftime("%b"),
            'syear':  cdatetime.strftime("%Y"),
            #'step':   "{:02d}".format(tstep*FREQ),
        })

    def retrieve_var_tstep(self, day=1, static=True, aspect=(1,1)):
        """ run plot """
        self.fig = go.Figure()
        day = int(day)
        if DEBUG: print('Adding contours ...')
        self.fig.add_trace(self.generate_contour_tstep_trace(day))
        if DEBUG: print('Update layout ...')
        try:
            fig_title=dict(text='{}'.format(self.get_title(day)),
                           xanchor='left',
                           yanchor='top',
                           x=0.01, y=0.95)
        except:
            fig_title={}
        self.fig.update_layout(
            legend=dict(
                x=0.01,
                y=0.85,
                bgcolor="rgba(0,0,0,0)"
            ),
            title=fig_title,
            uirevision=True,
            autosize=True,
            hovermode="closest",        # highlight closest point on hover
            mapbox=self.get_mapbox(zoom=4.5-(0.5*aspect[0])),
            font_size=12-(0.5*aspect[0]),
            #height=800,
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
        )

        # if DEBUG: print('Returning fig of size {}'.format(sys.getsizeof(self.fig)))
        return self.fig

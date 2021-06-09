# -*- coding: utf-8 -*-
""" Data Handler """

# import plotly
import plotly.graph_objs as go
from matplotlib.colors import ListedColormap
import numpy as np
from netCDF4 import Dataset as nc_file
import pandas as pd
import geopandas as gpd
from shapely import geometry
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
from collections import OrderedDict
from PIL import Image
import calendar
import os

from utils import concat_dataframes
from utils import retrieve_timeseries
from utils import get_colorscale


DIR_PATH = os.path.dirname(os.path.realpath(__file__))

DEBUG = True

COLORS = ['#a1ede3', '#5ce3ba', '#fcd775', '#da7230',
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

STATS = OrderedDict({ 'bias': 'BIAS', 'corr': 'CORR', 'rmse': 'RMSE', 'frge': 'FRGE', 'totn': 'TOTAL CASES' })

# Frequency = 3 Hourly
FREQ = 3

DEFAULT_VAR = 'OD550_DUST'
DEFAULT_MODEL = 'median'

STYLES = {
    "carto-positron": "Light",
    "open-street-map": "Open street map",
    "stamen-terrain": "Terrain",
}


MODEBAR_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": ["pan2d",
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

        self.station_names = np.array([st_name[~st_name.mask].tostring().decode('utf-8')
                              for st_name in
                              self.input_file.variables['station_name'][:]])

        self.values = {
            varname: self.input_file.variables[varname][:]
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
        clon = self.lon[notnan]
        clat = self.lat[notnan]
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
                color='#F1B545',
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


    def retrieve_timeseries(self, idx, name):

        old_indexes = self.dataframe[0]['station'].unique()
        new_indexes = np.arange(old_indexes.size)
        dict_idx = dict(zip(new_indexes, old_indexes))
        fig = go.Figure()
        for mod, df in zip([self.obs]+self.model, self.dataframe):
            if DEBUG: print("MOD", mod, "COLS", df.columns)
            timeseries = \
                df[df['station']==dict_idx[idx]].set_index('time')
            #visible_ts = timeseries[timeseries.index.isin(self.date_range)]

            if 'lat' in df.columns:
                lat_col = 'lat'
                lon_col = 'lon'
            else:
                lat_col = 'latitude'
                lon_col = 'longitude'

            if mod == self.obs:
                sc_mode = 'markers'
                marker = {'size': 10, 'symbol': "triangle-up-dot"}
                marker['color'] = '#F1B545'
                visible = True
            else:
                sc_mode = 'lines+markers'
                marker = {'size': 5}
                visible = 'legendonly'
                cur_lat = round(timeseries[lat_col][0], 2)
                cur_lon = round(timeseries[lon_col][0], 2)

            if mod == 'median':
                marker['color'] = 'black'
                line = {'dash' : 'dash'}
            else:
                line = {'dash' : 'solid'}


            fig.add_trace(dict(
                type='scatter',
                name="{}".format(
                    mod.upper()),
                x=timeseries.index,
                y=timeseries[self.variable],
                mode=sc_mode,
                marker=marker,
                line=line,
                visible=visible
                )
            )

        title = "{} @ {} (lat = {:.2f}, lon = {:.2f})".format(
            VARS[self.variable]['name'], name, cur_lat, cur_lon,
        )

        fig.update_layout(
            title=dict(text=title, x=0.45, y=0.99),
            # uirevision=True,
            autosize=True,
            showlegend=True,
            hovermode="x",        # highlight closest point on hover
            #margin={"r": 10, "t": 0, "l": 10, "b": 10},
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

    def retrieve_timeseries(self, lat, lon, model=None, method='netcdf', forecast=False):

        if not model:
            model = self.model

        obs_eval = model[0] not in MODELS and model[0] in OBS 

        for mod in model:
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
            if DEBUG: print('*** FPATH ***', fpath)
            self.fpaths.append(fpath)

        title = "{} @ lat = {} and lon = {}".format(
            VARS[self.variable]['name'], round(lat, 2), round(lon, 2)
        )

        mul = VARS[self.variable]['mul']

        fig = go.Figure()

        for mod, fpath in zip(model, self.fpaths):
            # print(mod, fpath)
            if mod not in MODELS and mod in OBS:
                variable = OBS[mod]['obs_var']
            else:
                variable = self.variable

            ts_lat, ts_lon, ts_index, ts_values = retrieve_timeseries(
                    fpath, lat, lon, variable, method=method, forecast=forecast)

            if isinstance(ts_lat, np.ndarray):
                ts_lat = float(ts_lat)
                ts_lon = float(ts_lon)
                ts_values = (ts_values*mul).round(2)
            else:
                ts_values = round((ts_values*mul), 2)

            if obs_eval and mod == model[0]:
                sc_mode = 'markers'
                marker = {'size': 10, 'symbol': "triangle-up-dot"}
                marker['color'] = '#F1B545'
                visible = True
                name = "{}".format(mod.upper())
            elif obs_eval:
                sc_mode = 'lines+markers'
                marker = {'size': 5}
                visible = 'legendonly'
                name = "{}".format(mod.upper())
            else:
                sc_mode = 'lines+markers'
                marker = {'size': 5}
                visible = True
                name = "{} ({}, {})".format(
                        mod.upper(), round(ts_lat, 2), round(ts_lon, 2))

            if mod == 'median':
                marker['color'] = 'black'
                line = {'dash' : 'dash'}
            else:
                line = {'dash' : 'solid'}

            fig.add_trace(dict(
                    type='scatter',
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
            # hovermode="closest",        # highlight closest point on hover
            hovermode="x",        # highlight closest point on hover
            margin={"r": 10, "t": 35, "l": 10, "b": 10},
        )

        return fig


class FigureHandler(object):
    """ Class to manage the figure creation """

    def __init__(self, model=None, selected_date=None):
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
            self.filedir = None
            self.filevars = None
            self.confvars = None
            filepath = None

        if filepath is not None:
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
            varlist = [var for var in self.input_file.variables if var in self.filevars]
            self.xlon, self.ylat = np.meshgrid(lon, lat)

            if self.confvars is not None:
                self.bounds = {
                    varname: np.array(VARS[confvar]['bounds']).astype('float32')
                    for varname, confvar in zip(self.filevars, self.confvars) if varname in varlist
                }
            else:
                self.bounds = {
                    varname: np.array(VARS[varname]['bounds']).astype('float32')
                    for varname in varlist
                }

            self.colormaps = {
                varname: get_colorscale(self.bounds[varname], COLORMAP)
                for varname in varlist
            }
            # print(varlist, self.confvars, self.filevars, self.bounds, self.colormaps)

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
        var = self.input_file.variables[varname][tstep]*mul
        idx = np.where(var.ravel() >= self.bounds[varname][0])  # !=-9.e+33)
        xlon = self.xlon.ravel()[idx]
        ylat = self.ylat.ravel()[idx]
        var = var.ravel()[idx]

        return xlon, ylat, var

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

    def generate_contour_tstep_trace(self, varname, tstep=0):
        """ Generate trace to be added to data, per variable and timestep """
        geojson_file = GEOJSON_TEMPLATE.format(self.filedir,
                self.selected_date_plain, tstep, self.selected_date_plain, varname)

        if os.path.exists(geojson_file):
            geojson = json.load(open(geojson_file))
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
        bounds = self.bounds[varname]
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
            colorscale=self.colormaps[varname],
            showscale=False,
            showlegend=False,
            hoverinfo='none',
            marker=dict(
                opacity=0.6,
                line_width=0,
            ),
            colorbar=None,
        )

    def generate_var_tstep_trace(self, varname=None, tstep=0):
        """ Generate trace to be added to data, per variable and timestep """
        if not varname:
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
        xlon, ylat, val = self.set_data(varname, tstep)
        if self.model in OBS:
            name = OBS[self.model]['name']
        else:
            name = MODELS[self.model]['name']
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
                cmin=self.bounds[varname][0],
                cmax=self.bounds[varname][-1],
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
        rdatetime = self.rdatetime
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

    def retrieve_var_tstep(self, varname=None, tstep=0, hour=None, static=True, aspect=(1,1), center=None):
        """ run plot """

        if hour is not None:
            tstep = int(self.hour_to_step(hour))
        else:
            tstep = int(tstep)

        if varname is not None and self.model in OBS:
            varname = OBS[self.model]['obs_var']

        if DEBUG: print('VARNAME', varname)

        self.fig = go.Figure()
        if varname:
            if DEBUG: print('Adding contours ...')
            self.fig.add_trace(self.generate_contour_tstep_trace(varname, tstep))
        else:
            if DEBUG: print('Adding one point ...')
            self.fig.add_trace(self.generate_var_tstep_trace())
        if varname and static:
            if DEBUG: print('Adding points ...')
            self.fig.add_trace(self.generate_var_tstep_trace(varname, tstep))

        # axis_style = dict(
        #     zeroline=False,
        #     showline=False,
        #     showgrid=True,
        #     ticks='',
        #     showticklabels=False,
        # )

        if DEBUG: print('Update layout ...')
        if varname:
            fig_title=dict(text='<b>{}</b>'.format(self.get_title(varname, tstep)),
                           xanchor='left',
                           yanchor='top',
                           x=0.01, y=0.95)
        else:
            fig_title={}
        if DEBUG: print('ADD IMAGES')
        if varname and varname in VARS:
            ypos = 0.87-(aspect[0]/50)
            size = 0.18+(aspect[0]/50)
            if DEBUG: print("YPOS", aspect[0], ypos)
            self.fig.add_layout_image(
                dict(
                    source=Image.open(VARS[varname]['image_scale']),
                    xref="paper", yref="paper",
                    x=0.01, y=ypos,
                    sizex=size, sizey=size,
                    xanchor="left", yanchor="top",
                    layer='above',
                ))
        self.fig.update_layout(
            title=fig_title,
            uirevision='forecast-multimodel',  # True,
            autosize=True,
            hovermode="closest",        # highlight closest point on hover
            mapbox=self.get_mapbox(zoom=2.8-(0.5*aspect[0]), center=center),
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


class VisFigureHandler(object):
    """ Class to manage the figure creation """

    def __init__(self, selected_date=None):

        self.path_tpl = '/data/interactive_test/obs/visibility/{year}/{month}/{year}{month}{day}{tstep0:02d}{tstep1:02d}_visibility.csv'
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
                size=30,
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
            fig_title=dict(text='<b>{}</b>'.format(self.get_title(tstep)),
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
            geojson = json.load(open(geojson_file))
        else:
            print('ERROR', geojson_file, 'not available')
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
        print("***", varname, day, static, self.geojson, self.filepath)
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
        if varname and os.path.exists(self.filepath):
            fig_title=dict(text='<b>{}</b>'.format(self.get_title(varname, tstep)),
                           xanchor='left',
                           yanchor='top',
                           x=0.01, y=0.95)
        else:
            fig_title={}
        self.fig.add_layout_image(
            dict(
                source=Image.open(PROB[varname]['image_scale']),
                xref="paper", yref="paper",
                x=0.01, y=1,
                sizex=0.35, sizey=0.35,
                xanchor="left", yanchor="top",
                layer='above',
            ))
        self.fig.update_layout(
            title=fig_title,
            uirevision=True,
            autosize=True,
            hovermode="closest",        # highlight closest point on hover
            mapbox=self.get_mapbox(zoom=2.8-(0.5*aspect[0])),
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
            print(WAS[self.was]['shp'])
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

        df = pd.read_hdf(input_path, 'was_{}'.format(self.selected_date_plain)).set_index('day')

        names = []
        colors = []
        definitions = []
        if not hasattr(self, 'xlon'):
            return names, colors, definitions

        names, colors, definitions = df.loc['Day{}'.format(day)].values.T
        print(names, colors, definitions)
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
            geojson = json.loads(self.was_df['geometry'].to_json())
        else:
            geojson = {
                    "type": "FeatureCollection",
                    "features": []
                    }
        colormap =  ['green'] + list(WAS[self.was]['colors'].keys())
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
        print(locations, '--', values)
        print(colormap)
        # if DEBUG: print(varname, self.colormaps[varname], values)
        return dict(
            type='choroplethmapbox',
            name='',  # str(self.was)+'_contours',
            geojson=geojson,
            z=values,
            ids=locations,
            locations=locations,
            #zmin=bounds[0],
            #zmax=bounds[-1],
            showscale=False,
            showlegend=False,
            customdata=["Region: {}<br>Warning level: {}".format(name,
                definition) for name, definition in zip(names, definitions)],
            hovertemplate="%{customdata}",
            #hoverinfo='none',
            #mode='markers',
            colorscale=get_colorscale(np.arange(len(colormap)-1)-0.5 , ListedColormap(colormap), True),
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
            fig_title=dict(text='<b>{}</b>'.format(self.get_title(day)),
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
            mapbox=self.get_mapbox(zoom=6.5-(0.5*aspect[0])),
            #height=800,
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
        )

        # if DEBUG: print('Returning fig of size {}'.format(sys.getsizeof(self.fig)))
        return self.fig

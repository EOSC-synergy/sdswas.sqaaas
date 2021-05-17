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
import calendar
import os

from utils import concat_dataframes
from utils import retrieve_timeseries
from utils import get_colorscale


DIR_PATH = os.path.dirname(os.path.realpath(__file__))

DEBUG =  True

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

# Frequency = 3 Hourly
FREQ = 3

DEFAULT_VAR = 'OD550_DUST'
DEFAULT_MODEL = 'median'

STYLES = {
    "carto-positron": "Light",
    "open-street-map": "Open street map",
    "stamen-terrain": "Terrain",
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
        print('VARLIST', self.varlist)

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
        print(len(clon), len(clat), len(cstations))
        name = 'Aeronet Station'
        return dict(
            type='scattermapbox',
            below='',
            lon=clon,
            lat=clat,
            mode='markers',
            #text=val,
            name=name,
            customdata=cstations,
            hovertemplate="name:%{customdata}<br>lon: %{lon:.4f}<br>" +
                          "lat: %{lat:.4f}", #"<br>value: %{text:.4f}",
            opacity=0.6,
            showlegend=False,
            marker=dict(
                # autocolorscale=True,
                # symbol='square',
                color='royalblue',
                opacity=0.6,
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
        print("ObsTimeSeries", start_date, end_date)
        self.date_range = pd.date_range(start_date, end_date, freq='D')

        fname_tpl = os.path.join(OBS[obs]['path'],
                                'feather',
                                '{{}}-{dat}-{{}}_interp.ft')

        months = np.unique([d.strftime("%Y%m") for d in self.date_range.to_pydatetime()])

        print('MONTHS', months)
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
            print("MOD", mod, "COLS", df.columns)
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
                visible = True
                print(mod)
                print(timeseries[self.variable].size)
            else:
                sc_mode = 'lines+markers'
                marker = {'size': 5}
                visible = 'legendonly'
                cur_lat = round(timeseries[lat_col][0], 2)
                cur_lon = round(timeseries[lon_col][0], 2)


            fig.add_trace(dict(
                    type='scatter',
                    name="{}".format(
                        mod.upper()),
                    x=timeseries.index,
                    y=timeseries[self.variable],
                    mode=sc_mode,
                    marker=marker,
                    visible=visible
                )
            )

        title = "{} @ {} (lat = {:.4f}, lon = {:.4f})".format(
            VARS[self.variable]['name'], name, cur_lat, cur_lon,
        )

        fig.update_layout(
            title=dict(text=title, x=0.45, y=1.),
            uirevision=True,
            autosize=True,
            showlegend=True,
            hovermode="x",        # highlight closest point on hover
            margin={"r": 10, "t": 30, "l": 10, "b": 10},
        )
        fig.update_xaxes(
            range=[self.date_range[0], self.date_range[-1]],
            rangeslider_visible=True,
            rangeselector=dict(
                buttons=list([
#                     dict(count=6, label="6m",
#                          step="month", stepmode="backward"),
#                     dict(count=1, label="YTD",
#                          step="year", stepmode="todate"),
#                     dict(count=1, label="1y",
#                          step="year", stepmode="backward"),
                    dict(step="all", label="all"),
                    dict(count=1, label="1m",
                         step="month", stepmode="backward"),
                    dict(count=14, label="2w",
                         step="day", stepmode="backward"),
                    dict(count=7, # label="1w",
                         step="day", stepmode="backward"),
                ])
            )
        )

#        fig['layout']['xaxis'].update(range=['2020-04-01', '2020-04-17 09:00'])

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
        except:
            self.month = datetime.strptime(date, "%Y-%m-%d").strftime("%Y%m")

    def retrieve_timeseries(self, lat, lon, model=None, method='netcdf'):

        if not model:
            model = self.model

        for mod in model:
            if method == 'feather':
                path_template = '{}-{}-{}.ft'.format(self.month, mod, self.variable)
            elif method == 'netcdf':
                path_template = '{}*{}.nc'.format(self.month, MODELS[mod]['template'], self.variable)
            fpath = os.path.join(MODELS[mod]['path'],
                                    method,
                                    path_template)
            self.fpaths.append(fpath)

        title = "{} @ lat = {} and lon = {}".format(
            VARS[self.variable]['name'], round(lat, 2), round(lon, 2)
        )
        fig = go.Figure()

        for mod, fpath in zip(model, self.fpaths):
            # print(mod, fpath)
            ts_lat, ts_lon, ts_index, ts_values = retrieve_timeseries(fpath, lat, lon, self.variable, method=method)

            fig.add_trace(dict(
                    type='scatter',
                    name="{} ({}, {})".format(
                        mod.upper(), ts_lat.round(2), ts_lon.round(2)),
                    x=ts_index,
                    y=ts_values,
                    mode='lines+markers',
                )
            )
        fig.update_layout(
            title=dict(text=title, x=0.45, y=1.),
            uirevision=True,
            autosize=True,
            showlegend=True,
            # hovermode="closest",        # highlight closest point on hover
            hovermode="x",        # highlight closest point on hover
            margin={"r": 20, "t": 30, "l": 20, "b": 10},
        )
        fig.update_xaxes(
            rangeslider_visible=True,
            rangeselector=dict(
                buttons=list([
#                     dict(count=6, label="6m",
#                          step="month", stepmode="backward"),
#                     dict(count=1, label="YTD",
#                          step="year", stepmode="todate"),
#                     dict(count=1, label="1y",
#                          step="year", stepmode="backward"),
                    dict(step="all", label="all"),
                    dict(count=1, label="1m",
                         step="month", stepmode="backward"),
                    dict(count=14, label="2w",
                         step="day", stepmode="backward"),
                    dict(count=7, # label="1w",
                         step="day", stepmode="backward"),
                ])
            )
        )

#        fig['layout']['xaxis'].update(range=['2020-04-01', '2020-04-17 09:00'])

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

    def get_mapbox(self, style='carto-positron', relayout=False, zoom=3):
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
        geojson_file = GEOJSON_TEMPLATE.format(self.filedir,
                self.selected_date_plain, tstep, self.selected_date_plain, varname)

        if os.path.exists(geojson_file):
            geojson = json.load(open(geojson_file))
        else:
            print('ERROR', geojson_file, 'not available')
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
            hovertemplate="lon: %{lon:.4f}<br>lat: %{lat:.4f}<br>" +
            "value: %{text:.4f}",
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

    def retrieve_var_tstep(self, varname=None, tstep=0, static=True, aspect=(1,1)):
        """ run plot """
        self.fig = go.Figure()
        tstep = int(tstep)
        if varname is not None and self.model in OBS:
            varname = OBS[self.model]['obs_var']

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
        self.fig.update_layout(
            title=fig_title,
            uirevision=True,
            autosize=True,
            hovermode="closest",        # highlight closest point on hover
            mapbox=self.get_mapbox(zoom=3-(0.5*aspect[0])),
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

    def get_mapbox(self, style='carto-positron', relayout=False, zoom=3):
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
            hovertemplate="lon: %{lon:.4f}<br>lat: %{lat:.4f}<br>" +
            "value: %{text:.4f}",
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
        self.fig.update_layout(
            title=fig_title,
            uirevision=True,
            autosize=True,
            hovermode="closest",        # highlight closest point on hover
            mapbox=self.get_mapbox(zoom=3-(0.5*aspect[0])),
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
            title=fig_title,
            uirevision=True,
            autosize=True,
            hovermode="closest",        # highlight closest point on hover
            mapbox=self.get_mapbox(zoom=7-(0.5*aspect[0])),
            #height=800,
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
        )

        # if DEBUG: print('Returning fig of size {}'.format(sys.getsizeof(self.fig)))
        return self.fig

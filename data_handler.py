#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Data Handler """

# import plotly
import plotly.graph_objs as go
from matplotlib.colors import ListedColormap
import numpy as np
from netCDF4 import Dataset as nc_file
import feather
import math
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os

from utils import get_colorscale


DEBUG = True

COLORS = ['#a1ede3', '#5ce3ba', '#fcd775', '#da7230',
          '#9e6226', '#714921', '#392511', '#1d1309']

COLORMAP = ListedColormap(COLORS)

VARS = json.load(open('conf/vars.json'))
MODELS = json.load(open('conf/models.json'))

# Frequency = 3 Hourly
FREQ = 3

DEFAULT_VAR = 'od550_dust'
DEFAULT_MODEL = 'median'

STYLES = {
    "carto-positron": "Light",
    "open-street-map": "Open street map",
#    "carto-darkmatter": "Dark",
    "stamen-terrain": "Terrain",
#    "stamen-toner": "White/Black",
#    "stamen-watercolor": "Watercolor"
}

GEOJSON_TEMPLATE = "{}/geojson/{:02d}_{}_{}.geojson"
NETCDF_TEMPLATE = "{}/netcdf/{}{}.nc4"


def find_nearest(array, value):
    idx = np.searchsorted(array, value, side="left")
    if idx > 0 and (idx == len(array) or math.fabs(value - array[idx-1]) <
                    math.fabs(value - array[idx])):
        return array[idx-1]
    else:
        return array[idx]


class Observations1dHandler(object):
    """ Class which handles 1D obs data """

    def __init__(self, filepath, selected_date):
        self.input_file = nc_file(filepath)
        self.lon = self.input_file.variables['longitude'][:]
        self.lat = self.input_file.variables['latitude'][:]
        time_obj = self.input_file.variables['time']
        self.tim = time_obj[:]
        self.what, _, rdate, rtime = time_obj.units.split()[:4]
        self.rdatetime = datetime.strptime("{} {}".format(rdate, rtime[:5]),
                                           "%Y-%m-%d %H:%M")
        # varlist = [var for var in self.input_file.variables if var in VARS]
        varlist = ['od550aero']

        self.station_names = [st_name[~st_name.mask].tostring().decode('utf-8')
                              for st_name in
                              self.input_file.variables['station_name'][:]]

        self.values = {
            varname: self.input_file.variables[varname][:]
            for varname in varlist
        }

        self.bounds = {
            varname: np.array(VARS['od550_dust']['bounds']).astype('float32')
            for varname in varlist
        }

        self.colormaps = {
            varname: get_colorscale(self.bounds[varname], COLORMAP)
            for varname in varlist
        }

        try:
            self.selected_date = datetime.strptime(
                selected_date, "%Y%m%d").strftime("%Y-%m-%d")
        except:
            self.selected_date = selected_date

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

    def generate_obs1d_tstep_trace(self, varname):
        """ Generate trace to be added to data, per variable and timestep """
        varname = 'od550aero'
        val = self.values[varname][0]
        name = 'Aeronet Station'
        return dict(
            type='scattermapbox',
            below='',
            lon=self.lon,
            lat=self.lat,
            mode='markers',
            text=val,
            name=name,
            customdata=self.station_names,
            hovertemplate="name:%{customdata}<br>lon: %{lon:.4f}<br>" +
                          "lat: %{lat:.4f}<br>value: %{text:.4f}",
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


class TimeSeriesHandler(object):
    """ Class to handle time series """

    def __init__(self, model, variable):
        if isinstance(model, str):
            model = [model]
        self.model = model
        self.variable = variable
        self.dataframe = []
        for mod in model:
            fpath = os.path.join(MODELS[mod]['path'],
                                    'feather',
                                    '{}.ft'.format(variable))
            self.dataframe.append(feather.read_dataframe(fpath))

    def retrieve_timeseries(self, lat, lon, model=None):

        if not model:
            model = self.model

        title = "{} @ lat = {} and lon = {}".format(
            VARS[self.variable]['name'], round(lat, 4), round(lon, 4)
        )
        fig = go.Figure()
        for mod, df in zip(model, self.dataframe):
            df_lats = find_nearest(df['lat'].values, lat)
            df_lons = find_nearest(df['lon'].values, lon)
            timeseries = \
                df.loc[(df['lat'] == df_lats) &
                       (df['lon'] == df_lons),
                       ('time', self.variable)].set_index('time')
            if DEBUG: print(mod, df_lats, df_lons)
            fig.add_trace(dict(
                    type='scatter',
                    name="{} ({}, {})".format(
                        mod.upper(), round(df_lats, 4), round(df_lons, 4)),
                    x=timeseries.index,
                    y=timeseries[self.variable],
                    mode='lines+markers',
                )
            )
        fig.update_layout(
            title=dict(text=title, x=0.45, y=1.),
            uirevision=True,
            autosize=True,
            showlegend=True,
            hovermode="closest",        # highlight closest point on hover
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

        fig['layout']['xaxis'].update(range=['2020-04-01', '2020-04-17 09:00'])

        return fig


class FigureHandler(object):
    """ Class to manage the figure creation """

    def __init__(self, model=None, selected_date=None):
        if isinstance(model, list):
            model = model[0]

        if model:
            self.model = model
            if DEBUG: print("MODEL", model)
            filepath = NETCDF_TEMPLATE.format(
                MODELS[self.model]['path'],
                selected_date,
                MODELS[self.model]['template']
            )
            self.input_file = nc_file(filepath)
            lon = self.input_file.variables['lon'][:]
            lat = self.input_file.variables['lat'][:]
            time_obj = self.input_file.variables['time']
            self.tim = time_obj[:]
            self.what, _, rdate, rtime = time_obj.units.split()[:4]
            if len(rtime) > 5:
                rtime = rtime[:5]
            self.rdatetime = datetime.strptime("{} {}".format(rdate, rtime),
                                               "%Y-%m-%d %H:%M")
            varlist = [var for var in self.input_file.variables if var in VARS]
            self.xlon, self.ylat = np.meshgrid(lon, lat)
            self.bounds = {
                varname: np.array(VARS[varname]['bounds']).astype('float32')
                for varname in varlist
            }

            self.colormaps = {
                varname: get_colorscale(self.bounds[varname], COLORMAP)
                for varname in varlist
            }

        if selected_date:
            try:
                self.selected_date = datetime.strptime(
                    selected_date, "%Y%m%d").strftime("%Y-%m-%d")
            except:
                self.selected_date = selected_date

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
        mul = VARS[varname]['mul']
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
        geojson = \
            json.load(open(GEOJSON_TEMPLATE
                           .format(MODELS[self.model]['path'],
                                   tstep,
                                   self.selected_date,
                                   varname)))

        name = VARS[varname]['name']
        bounds = self.bounds[varname]
        loc_val = [
            (
                feature['id'],
                np.around(feature['properties']['value'], 2),
            )
            for feature in geojson['features']
            if feature['geometry']['coordinates']
        ]
        locations, values = np.array(loc_val).T
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
                cmin=self.bounds[varname][0],
                cmax=self.bounds[varname][-1],
                colorbar=None,
            ),
        )

    def get_title(self, varname, tstep=0):
        """ return title according to the date """
        rdatetime = self.rdatetime
        cdatetime = self.retrieve_cdatetime(tstep)
        return r'{} {}'.format(MODELS[self.model]['name'],
                               VARS[varname]['title'] % {
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

#         if DEBUG: print('Adding frames ...')
#         fig['frames'] = [
#             dict(
#                 data=[
#                     self.generate_contour_tstep_trace(varname, tstep=num),
#                     self.generate_var_tstep_trace(varname, tstep=num),
#                 ],
#                 layout=dict(title_text=self.get_title(varname, tstep=num)),
#                 name=varname+str(num))
#             for num in range(self.tim.size)
#         ]
#
#         sliders = [
#             dict(
#                 steps=[
#                     dict(
#                         args=[
#                             [frame.name],
#                             dict(
#                                 mode='immediate',
#                                 frame=dict(duration=TIMES['animation'],
#                                            redraw=True),
#                                 transition=dict(
#                                     duration=TIMES['transition'],
#                                     # easing="quadratic-in-out",
#                                 )
#                             )
#                         ],
#                         method='animate',
#                         label='{:d}'.format(timestep*3),
#                         value=timestep,
#                     )
#                     for timestep, frame in enumerate(fig.frames)
#                 ],
#                 transition=dict(duration=TIMES['slider_transition'],
#                                 easing="cubic-in-out"),
#                 x=1.0,
#                 y=1.08,
#                 len=0.49,
#                 pad={"r": 0, "t": 0},
#                 xanchor="right",
#                 yanchor="top",
#                 currentvalue=dict(visible=False),
#                 # currentvalue=dict(font=dict(size=12),
#                 #     prefix='Timestep: ',
#                 #     visible=True,
#                 #     xanchor= 'center'),
#                 )
#         ]

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
#             xaxis=dict(
#                 range=[self.xlon.min(), self.xlon.max()]
#             ),
#             yaxis=dict(
#                 range=[self.ylat.min(), self.ylat.max()]
#             ),
            # sliders=sliders
        )

        # if DEBUG: print('Returning fig of size {}'.format(sys.getsizeof(self.fig)))
        return self.fig

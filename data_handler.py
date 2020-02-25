#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Data Handler """

# import plotly
import plotly.graph_objs as go
import matplotlib as mpl
from matplotlib import cm
import numpy as np
from netCDF4 import Dataset as nc_file
# import xarray as xr
import math
import json

from datetime import datetime
from dateutil.relativedelta import relativedelta


# mapbox_access_token = \
# "pk.eyJ1IjoiZmJlbmluY2EiLCJhIjoiY2p1ODZhdW9qMDZ3eTN5b2IxN2JzdzUyeSJ9.m0QotzSgIz0Bi0gIynzG6A"

animation_time = 900
transition_time = 300
slider_transition_time = 300


_COLORS = [[0, 'rgb(255,255,255)'],
           [0.01, 'rgb(255,255,255)'],
           [0.02, 'rgb(161,237,227)'],
           [0.04, 'rgb(92,227,186)'],
           [0.08, 'rgb(252,215,117)'],
           [0.12, 'rgb(218,114,48)'],
           [0.16, 'rgb(158,98,38)'],
           [0.32, 'rgb(113,73,33)'],
           [0.64, 'rgb(57,37,17)'],
           [1, 'rgb(29,19,9)']]


# COLORS = ['#ffffff', '#a1ede3', '#5ce3ba', '#fcd775', '#da7230',
#           '#9e6226', '#714921', '#392511', '#1d1309']
COLORS = ['#a1ede3', '#5ce3ba', '#fcd775', '#da7230',
          '#9e6226', '#714921', '#392511', '#1d1309']

COLORMAP = mpl.colors.ListedColormap(COLORS)
# COLORMAP.set_under(COLORS[0])
# COLORMAP.set_over(COLORS[-1])

VARS = json.load(open('conf/vars.json'))

DEFAULT_VAR = 'od550_dust'

STYLES = {
    "open-street-map": "Open street map",
    "carto-positron": "Light",
    "carto-darkmatter": "Dark",
    "stamen-terrain": "Terrain",
    "stamen-toner": "White/Black",
    "stamen-watercolor": "Watercolor"
}


def magnitude(num):
    """ Calculate magnitude """
    return int(math.floor(math.log10(num)))


def normalize_vals(vals, valsmin, valsmax, rnd=2):
    """ Normalize values to 0-1 scale """
    vals = np.array(vals)
    if rnd < 2:
        rnd = 2
    return np.around((vals-valsmin)/(valsmax-valsmin), rnd)


def get_colorscale(varname):
    """ Create colorscale """
    bounds = np.array(VARS[varname]['bounds']).astype('float32')
    magn = magnitude(bounds[-1])
    n_bounds = normalize_vals(bounds, bounds[0], bounds[-1], magn)
    norm = mpl.colors.BoundaryNorm(bounds, len(bounds)-1, clip=True)
    s_map = cm.ScalarMappable(norm=norm, cmap=COLORMAP)

    return [[idx, 'rgba' + str(s_map.to_rgba(val, bytes=True))] for idx, val in
            zip(n_bounds, bounds)]


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
                         frame=dict(duration=animation_time,
                                    redraw=True),
                         transition=dict(duration=transition_time,
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
                                    redraw=False),
                         transition=dict(duration=0),
                         mode='immediate'
                         )
                 ])
            ],
        pad={"r": 0, "t": 0},
        x=0.50,
        y=1.06,
        xanchor="right",
        yanchor="top"
    )


class FigureHandler(object):
    """ Class to manage the figure creation """

    def __init__(self, filepath):
        self.input_file = nc_file(filepath)
        self.lon = self.input_file.variables['lon'][:]
        self.lat = self.input_file.variables['lat'][:]
        time_obj = self.input_file.variables['time']
        self.tim = time_obj[:]
        self.what, _, rdate = time_obj.units.split()[:3]
        self.rdatetime = datetime.strptime("{}".format(rdate), "%Y-%m-%d")
        self.varlist = [var for var in self.input_file.variables if var not in
                        ('lon', 'lat', 'alt', 'lev', 'longitude',
                         'latitude', 'altitude', 'levels', 'time')]
        self.xlon, self.ylat = np.meshgrid(self.lon, self.lat)
        self.bounds = {
            varname: np.array(VARS[varname]['bounds']).astype('float32')
            for varname in self.varlist
        }

        self.colormaps = {
            varname: get_colorscale(varname)
            for varname in self.varlist
        }

    def get_mapbox_style_buttons(self):
        """ Relayout map with different styles """
        return dict(
            type="buttons",
            direction="left",
            buttons=list([self.get_mapbox(style, relayout=True) for style in
                          STYLES.keys()]),
            pad={"r": 0, "t": 0},
            showactive=True,
            x=1.0,
            y=-0.01,
            xanchor="right",
            yanchor="top",
        )

    def get_mapbox(self, style='open-street-map', relayout=False):
        """ Returns mapbox layout """
        mapbox_dict = dict(
            # accesstoken=mapbox_access_token,
            bearing=0,
            center=go.layout.mapbox.Center(
                lat=(self.lat.max()-self.lat.min())/2 + self.lat.min(),
                lon=(self.lon.max()-self.lon.min())/2 + self.lon.min(),
            ),
            pitch=0,
            zoom=3,
            style=style,
        )

        if relayout is False:
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
        idx = np.where(var.ravel() >= VARS[varname]['bounds'][1])  # !=-9.e+33)
        # print(x.ravel()[idx])
        xlon = self.xlon.ravel()[idx]
        ylat = self.ylat.ravel()[idx]
        var = var.ravel()[idx]

        return xlon, ylat, var

    def retrieve_cdatetime(self, tstep=0):
        """ Retrieve data from NetCDF file """
        # print(type(self.tim), self.tim[tstep], type(tstep), tstep)
        if self.what == 'days':
            cdatetime = self.rdatetime + relativedelta(days=self.tim[tstep])
        elif self.what == 'hours':
            cdatetime = self.rdatetime + relativedelta(hours=self.tim[tstep])
        elif self.what == 'minutes':
            cdatetime = self.rdatetime + relativedelta(minutes=self.tim[tstep])
        elif self.what == 'seconds':
            cdatetime = self.rdatetime + relativedelta(seconds=self.tim[tstep])

        # print(cdatetime.strftime("%Y%m%d %H:%M"), tstep)
        return cdatetime

    def generate_var_tstep_trace(self, varname, tstep=0):
        """ Generate trace to be added to data, per variable and timestep """
        xlon, ylat, val = self.set_data(varname, tstep)
        name = VARS[varname]['name']
        # colorscale = list(zip(norm_bounds, COLORS))
        # colorscale = get_colorscale(norm_bounds, bounds)
        colorscale = self.colormaps[varname]
        # print(name, magn, norm_bounds, colorscale)
        return dict(
            type='scattermapbox',
            lon=xlon,
            lat=ylat,
            text=val,
            mode='markers',
            showlegend=False,
            opacity=0.6,
            # fill=val,
            name=name,
            hovertemplate="""lon: %{lon:.4f}<br>
                       lat: %{lat:.4f}<br>
                       value: %{text:.4f}<br>""",
            marker=dict(
                # autocolorscale=True,
                color=val,
                size=8,
                colorscale=colorscale,
                opacity=0.6,
                colorbar={
                    "borderwidth": 0,
                    "outlinewidth": 0,
                    "thickness": 15,
                    "tickfont": {"size": 14},
                    "tickmode": "array",
                    "tickvals": self.bounds[varname],
                },
                cmin=self.bounds[varname][0],
                cmax=self.bounds[varname][-1],
                # showscale=True,
            ),

        )

    def retrieve_var_tstep(self, varname, tstep=0):
        """ run plot """
        fig = go.Figure()
        tstep = int(tstep)
        cdatetime = self.retrieve_cdatetime(tstep)
        fig.add_trace(self.generate_var_tstep_trace(varname, tstep))

        title = VARS[varname]['title'] % {
            'hour':  cdatetime.strftime("%H"),
            'day':   cdatetime.strftime("%d"),
            'month': cdatetime.strftime("%b"),
            'year':  cdatetime.strftime("%Y"),
        }

        # axis_style = dict(
        #     zeroline=False,
        #     showline=False,
        #     showgrid=True,
        #     ticks='',
        #     showticklabels=False,
        # )

        frames = [
            dict(
                data=self.generate_var_tstep_trace(varname, tstep=num),
                # traces=[0],
                name=varname+str(num))
            for num in range(25)
        ]

        fig['frames'] = frames

        # print([f['name'] for f in frames])

        sliders = [
            dict(
                steps=[
                    dict(
                        method='animate',
                        args=[
                            [varname+str(tstep)],
                            dict(
                                mode='immediate',
                                frame=dict(duration=animation_time,
                                           redraw=True),
                                transition=dict(
                                    duration=slider_transition_time,
                                    easing="quadratic-in-out",
                                )
                            )
                        ],
                        label='{:d}'.format(tstep*3),
                        value=tstep,
                    )
                    for tstep in range(25)
                ],
                transition=dict(duration=slider_transition_time,
                                easing="cubic-in-out"),
                x=1.0,
                y=1.06,
                len=0.49,
                pad={"r": 0, "t": 0},
                xanchor="right",
                yanchor="top",
                currentvalue=dict(visible=False),
                # currentvalue=dict(font=dict(size=12),
                #     prefix='Timestep: ',
                #     visible=True,
                #     xanchor= 'center'),
                )
        ]

        fig.update_layout(
            title=dict(text=title, y=0.95),
            autosize=True,
            hovermode="closest",        # highlight closest point on hover
            mapbox=self.get_mapbox(),
            width=1200,
            height=800,
            updatemenus=[
                get_animation_buttons(),
                self.get_mapbox_style_buttons(),
            ],

            sliders=sliders
        )

        return fig

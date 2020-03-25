#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Data Handler """

# import plotly
import plotly.graph_objs as go
import matplotlib as mpl
# import matplotlib.pyplot as plt
import numpy as np
from netCDF4 import Dataset as nc_file
# import xarray as xr
import json

from utils import get_colorscale
from utils import get_animation_buttons

from datetime import datetime
from dateutil.relativedelta import relativedelta


animation_time = 900
transition_time = 500
slider_transition_time = 500


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

COLORSCALE = [
    [0.0, 'rgba(161, 237, 227, 255)'],
    [0.02, 'rgba(161, 237, 227, 255)'],

    [0.02, 'rgba(92, 227, 186, 255)'],
    [0.05, 'rgba(92, 227, 186, 255)'],

    [0.05, 'rgba(252, 215, 117, 255)'],
    [0.11, 'rgba(252, 215, 117, 255)'],

    [0.11, 'rgba(218, 114, 48, 255)'],
    [0.17, 'rgba(218, 114, 48, 255)'],

    [0.17, 'rgba(158, 98, 38, 255)'],
    [0.24, 'rgba(158, 98, 38, 255)'],

    [0.24, 'rgba(113, 73, 33, 255)'],
    [0.49, 'rgba(113, 73, 33, 255)'],

    [0.49, 'rgba(57, 37, 17, 255)'],
    [1.0, 'rgba(57, 37, 17, 255)']
]

COLORMAP = mpl.colors.ListedColormap(COLORS[:-1])
# COLORMAP.set_under(COLORS[0])
COLORMAP.set_over(COLORS[-1])

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
            varname: get_colorscale(varname, self.bounds[varname], COLORMAP)
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
        idx = np.where(var.ravel() >= VARS[varname]['bounds'][0])  # !=-9.e+33)
        xlon = self.xlon.ravel()[idx]
        ylat = self.ylat.ravel()[idx]
        var = var.ravel()[idx]

        return xlon, ylat, var

    def retrieve_cdatetime(self, tstep=0):
        """ Retrieve data from NetCDF file """
        if self.what == 'days':
            cdatetime = self.rdatetime + relativedelta(days=self.tim[tstep])
        elif self.what == 'hours':
            cdatetime = self.rdatetime + relativedelta(hours=self.tim[tstep])
        elif self.what == 'minutes':
            cdatetime = self.rdatetime + relativedelta(minutes=self.tim[tstep])
        elif self.what == 'seconds':
            cdatetime = self.rdatetime + relativedelta(seconds=self.tim[tstep])

        return cdatetime

    def generate_contour_tstep_trace(self, varname, tstep=0):
        """ Generate trace to be added to data, per variable and timestep """
        geojson = \
            json.load(open("./data/geojson/{:02d}_2019-07-10_{}.geojson"
                           .format(tstep, varname)))
        name = VARS[varname]['name']
        bounds = self.bounds[varname]
        colorscale = COLORSCALE  # self.colormaps[varname]
        mul = VARS[varname]['mul']
        values = []
        for geo_id, feature in enumerate(geojson['features']):
            values.append(feature['properties']['value']*mul)
            feature['id'] = geo_id
        return dict(
            type='choroplethmapbox',
            name=name,  # +'_contours',
            geojson=geojson,
            z=values,
            locations=["{}".format(i) for i in range(len(values))],
            zmin=bounds[0], zmax=bounds[-1],
            colorscale=colorscale,
            showscale=False,
            hoverinfo='none',
            marker=dict(
                opacity=0.6,
                line_width=0,
            )
        )

    def generate_var_tstep_trace(self, varname, tstep=0):
        """ Generate trace to be added to data, per variable and timestep """
        xlon, ylat, val = self.set_data(varname, tstep)
        name = VARS[varname]['name']
        colorscale = COLORSCALE  # self.colormaps[varname]
        return dict(
            type='scattermapbox',
            below='',
            lon=xlon,
            lat=ylat,
            text=val,
            name=name,
            hovertemplate="lon: %{lon:.4f}<br>lat: %{lat:.4f}<br>" +
                          "value: %{text:.4f}",
            marker=dict(
                # autocolorscale=True,
                color=val,
                size=0,
                colorscale=colorscale,
                colorbar={
                    "tick0": self.bounds[varname][0],
                    "dtick": 1,
                    "borderwidth": 0,
                    "outlinewidth": 0,
                    "thickness": 15,
                    "tickfont": {"size": 14},
                    "tickmode": "array",
                    "tickvals": self.bounds[varname],
                },
                cmin=self.bounds[varname][0],
                cmax=self.bounds[varname][-1],
                showscale=True,
            ),

        )

    def get_title(self, varname, tstep=0):
        cdatetime = self.retrieve_cdatetime(tstep)
        return VARS[varname]['title'] % {
            'hour':  cdatetime.strftime("%H"),
            'day':   cdatetime.strftime("%d"),
            'month': cdatetime.strftime("%b"),
            'year':  cdatetime.strftime("%Y"),
        }

    def retrieve_var_tstep(self, varname, tstep=0):
        """ run plot """
        fig = go.Figure()
        tstep = int(tstep)
        fig.add_trace(self.generate_contour_tstep_trace(varname, tstep))
        fig.add_trace(self.generate_var_tstep_trace(varname, tstep))

        # axis_style = dict(
        #     zeroline=False,
        #     showline=False,
        #     showgrid=True,
        #     ticks='',
        #     showticklabels=False,
        # )

        fig['frames'] = [
            dict(
                data=[
                    self.generate_contour_tstep_trace(varname, tstep=num),
                    self.generate_var_tstep_trace(varname, tstep=num),
                ],
                layout=dict(title_text=self.get_title(varname, tstep=num)),
                name=varname+str(num))
            for num in range(self.tim.size)
        ]

        sliders = [
            dict(
                steps=[
                    dict(
                        args=[
                            [frame.name],
                            dict(
                                mode='immediate',
                                frame=dict(duration=animation_time,
                                           redraw=True),
                                transition=dict(
                                    duration=slider_transition_time,
                                    # easing="quadratic-in-out",
                                )
                            )
                        ],
                        method='animate',
                        label='{:d}'.format(tstep*3),
                        value=tstep,
                    )
                    for tstep, frame in enumerate(fig.frames)
                ],
                transition=dict(duration=slider_transition_time,
                                easing="cubic-in-out"),
                x=1.0,
                y=1.08,
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
            title=dict(text=self.get_title(varname, tstep), y=0.86),
            autosize=True,
            hovermode="closest",        # highlight closest point on hover
            mapbox=self.get_mapbox(),
            # width="100%",
            height=800,
            updatemenus=[
                get_animation_buttons(),
                self.get_mapbox_style_buttons(),
            ],
            # margin={"r": 0, "t": 0.1, "l": 0.1, "b": 0.1},
            sliders=sliders
        )

        return fig

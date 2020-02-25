#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Data Handler """

# import plotly
import plotly.graph_objs as go
import matplotlib as mpl
from matplotlib import cm
import numpy as np
import math
import xarray as xr
import os.path

import json
import jmespath
from datetime import datetime
from dateutil.relativedelta import relativedelta


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


# def scalarmappable(cmap, cmin, cmax):
#     colormap = cm.get_cmap(cmap)
#     norm = Normalize(vmin=cmin, vmax=cmax)
#     return cm.ScalarMappable(norm=norm, cmap=colormap)
#
# def get_scatter_colors(sm, df):
#     grey = 'rgba(128,128,128,1)'
#     return ['rgba' + str(sm.to_rgba(m, bytes = True, alpha = 1)) \
#             if not np.isnan(m) else grey for m in df]


def get_colorscale(varname):
    """ Create colorscale """
    bounds = np.array(VARS[varname]['bounds']).astype('float32')
    magn = magnitude(bounds[-1])
    n_bounds = normalize_vals(bounds, bounds[0], bounds[-1], magn)
    norm = mpl.colors.BoundaryNorm(bounds, len(bounds)-1, clip=True)
    s_map = cm.ScalarMappable(norm=norm, cmap=COLORMAP)

    return [[idx, 'rgba' + str(s_map.to_rgba(val, bytes=True))] for idx, val in
            zip(n_bounds, bounds)]


def get_animation_buttons(self):
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


# dict(
#     type="buttons",
#     direction="down",
#     buttons = list([self.retrieve_var_tstep(varname) for
#                     varname in self.varlist if varname !=
#                     DEFAULT_VAR]),
#     pad={"r": 10, "t": 10},
#     showactive=True,
#     x=1.1,
#     xanchor="left",
#     y=1.06,
#     yanchor="top"
# ),
# annotations=[
#     dict(
#         x=1.13,
#         y=0.99,
#         align="right",
#         valign="top",
#         text='VARIABLES',
#         showarrow=False,
#         xref="paper",
#         yref="paper",
#         xanchor="center",
#         yanchor="top"
#     )
# ]


class FigureHandler(object):
    """ Class to manage the figure creation """

    def __init__(self, filepath, rdate):
        """ Class initialization """
        self.filetpl = os.path.join(filepath,
                                    "{step}_{date}_{variable}.geojson"
                                    .format(date=rdate))
        self.rdatetime = datetime.strptime(rdate, "%Y-%m-%d")
        # self.varlist = [var for var in VARS if var not in
        #                 ('lon', 'lat', 'alt', 'lev', 'longitude',
        #                  'latitude', 'altitude', 'levels', 'time')]
        self.bounds = {
            varname: np.array(VARS[varname]['bounds']).astype('float32')
            for varname in VARS
        }
        self.colormaps = {
            varname: get_colorscale(varname)
            for varname in VARS
        }
        self.loaded_data = {}

    def get_geojson(self, filename, varname):
        """ Return geojson features per color layer """
        if filename in self.loaded_data:
            layers = self.loaded_data[filename]
        else:
            bounds = self.bounds[varname]
            print('loading geojson ...')
            data = json.load(open(filename))
            print('done')

            print('extractinig features ...')
            features = {
                COLORS[b]: jmespath.search(
                    "features[?properties.value > `{}`] && features[?properties.value <= `{}`]"
                    .format(bounds[b], bounds[b+1]), data)
                for b in range(len(bounds)-1)
            }

            features[COLORS[len(bounds)]] = jmespath.search(
                "features[?properties.value > `{}`]".format(bounds[-1]), data)

            print([(c, len(f)) for (c, f) in features.items()], 'done')

            layers = [{
                'sourcetype': 'geojson',
                'source': {"type": "FeatureCollection", "features":
                           features[color]},
                'type': "fill",
                'below': "traces",
                'color': color,
            } for color in features]

            self.loaded_data[filename] = layers

        ret = {
            'style': "open-street-map",
            'center': {'lon': 5, 'lat': 15.5},
            'zoom': 3,
            'layers': layers,
            # 'customdata': [feat['properties']['value'] for color in colors
            # for feat in features[color]]
        }

        print('returning', features["#FEEDA3"][0])
        return ret

    def get_mapbox(self, style='open-street-map', relayout=False):
        """ Returns mapbox layout """
        mapbox_dict = dict(
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
            method="relayout",
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
        geojson_file = self.filetpl.format(step=tstep, variable=varname)
        name = VARS[varname]['name']
        # colorscale = self.colormaps[varname]
        # print(name, magn, norm_bounds, colorscale)
        return dict(
            type='scattermapbox',
#             lon=xlon,
#             lat=ylat,
#             text=val,
#             # mode='lines',
#             showlegend=False,
#             opacity=0.6,
#             # fill="toself",
#             name=name,
#             hovertemplate=\
#                 """lon: %{lon:.4f}<br>lat: %{lat:.4f}<br>value:%{text:.4f}<br>""",
#             marker=dict(
#                 autocolorscale=True,
#                 color=val,
#                 size=8,
#                 colorscale=colorscale,
#                 opacity=0.6,
#                 colorbar={
#                     "borderwidth": 0,
#                     "outlinewidth": 0,
#                     "thickness": 15,
#                     "tickfont": {"size": 14},
#                     "tickmode": "array",
#                     "tickvals": self.bounds[varname],
#                     # "title": "ºC",
#                 },  # gives your legend some units
#                 cmin=self.bounds[varname][0],
#                 cmax=self.bounds[varname][-1],
#                 # showscale=True,
#             ),
        )

    def retrieve_var_tstep(self, varname, tstep=0):
        """ run plot """
        fig = go.Figure()
        tstep = int(tstep)
#         cdatetime = self.retrieve_cdatetime(tstep)
#         fig.add_trace(self.generate_var_tstep_trace(varname, tstep))

#         title = VARS[varname]['title'] % {
#             'hour':  cdatetime.strftime("%H"),
#             'day':   cdatetime.strftime("%d"),
#             'month': cdatetime.strftime("%b"),
#             'year':  cdatetime.strftime("%Y"),
#         }

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

        # print([st['args'][0] for st in sliders[0]['steps']])

        fig.update_layout(
            title=dict(text=title, y=0.95),
            autosize=True,
            hovermode="closest",
            mapbox=get_mapbox(),
            showlegend=False,
            # margin={'l':0, 'r':0, 'b':0, 't':0},
            width=1200,
            height=800,
            updatemenus=[
                get_animation_buttons(),
                get_mapbox_style_buttons(),
            ],
            sliders=sliders
        )

        # return dict(data=data, layout=layout)
        return fig

# if __name__ == "__main__":
#     FIG = FigureHandler().run_plot()
#     py.iplot(FIG, filename="dust_out.html") #, width=1000)
#     plotly.plot(FIG,
#     filename='/esarchive/scratch/Earth/fbeninca/plotly_test/test.html',
#     auto_open=False)

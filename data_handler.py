#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Data Handler """

# import plotly
import plotly.graph_objs as go
import matplotlib as mpl
from matplotlib import cm
import numpy as np
from netCDF4 import Dataset as nc_file
import math

import json
import jmespath
from datetime import datetime
from dateutil.relativedelta import relativedelta

test_mapbox2 = {
    'style': "stamen-terrain",
    'center': {'lon': -73.6, 'lat': 45.5},
    'zoom': 12, 'layers': [{
        'source': {
            'type': "FeatureCollection",
            'features': [{
                'type': "Feature",
                'geometry': {
                    'type': "MultiPolygon",
                    'coordinates': [[[
                        [-73.606352888, 45.507489991], [-73.606133883, 45.50687600],
                        [-73.605905904, 45.506773980], [-73.603533905, 45.505698946],
                        [-73.602475870, 45.506856969], [-73.600031904, 45.505696003],
                        [-73.599379992, 45.505389066], [-73.599119902, 45.505632008],
                        [-73.598896977, 45.505514039], [-73.598783894, 45.505617001],
                        [-73.591308727, 45.516246185], [-73.591380782, 45.516280145],
                        [-73.596778656, 45.518690062], [-73.602796770, 45.521348046],
                        [-73.612239983, 45.525564037], [-73.612422919, 45.525642061],
                        [-73.617229085, 45.527751983], [-73.617279234, 45.527774160],
                        [-73.617304713, 45.527741334], [-73.617492052, 45.527498362],
                        [-73.617533258, 45.527512253], [-73.618074188, 45.526759105],
                        [-73.618271651, 45.526500673], [-73.618446320, 45.526287943],
                        [-73.618968507, 45.525698560], [-73.619388002, 45.525216750],
                        [-73.619532966, 45.525064183], [-73.619686662, 45.524889290],
                        [-73.619787038, 45.524770086], [-73.619925742, 45.524584939],
                        [-73.619954486, 45.524557690], [-73.620122362, 45.524377961],
                        [-73.620201713, 45.524298907], [-73.620775593, 45.523650879]
                    ]]]
                }
            }]
        },
        'type': "fill", 'below': "traces", 'color': "royalblue"}]
}

def test_mapbox():
    print('loading geojson ...')
    data = json.load(open("/home/Earth/fbeninca/Programs/VISCA/VISCA/out-data/202001/Metadata_2601/00_feb_2601_monthly_prlr.geojson"))
    print('done')
    colors = "#FEEDA3", "#FDD97B", "#FDB154", "#FB8C44"
    print('extracting features ...')
    features = {color: jmespath.search("features[?properties.fill=='{}']".format(color), data)
                for color in colors}
    print([(c, len(f)) for (c, f) in features.items()], 'done')
    ret = {
        'style': "open-street-map",
        'center': {'lon': 5, 'lat': 15.5},
        'zoom': 3,
        'layers': [{
            'sourcetype': 'geojson',
            'source': {"type":"FeatureCollection", "features":
                       features[color]},
            'type': "fill",
            'below': "traces",
            'color': color,
        } for color in features],
        #'customdata': [feat['properties']['value'] for color in colors for feat in features[color]]
    }
    print('returning', features["#FEEDA3"][0])
    return ret
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


VARS = {
    'od550_dust': {
        'name': 'Dust Optical Depth',
        # 'bounds': [0, .1, .2, .4, .8, 1.2, 1.6, 3.2, 6.4, 10],
        'bounds': [0, .1, .2, .4, .8, 1.2, 1.6, 3.2, 6.4, 10],
        'mul': 1,
        'title' : u"Dust Optical Depth (550nm) Forecast run on %(hour)s %(day)s %(month)s %(year)s",
        'default': True,
    },
    'sconc_dust': {
        'name': 'Dust Surface Concentration',
        'bounds': [0, 5, 20, 50, 200, 500, 2000, 5000, 20000, 100000],
        'mul': 1e9,
        'title' : u"Dust Surface Conc. Forecast run on %(hour)s %(day)s %(month)s %(year)s",
        'default': False,
    },
    'dust_load': {
        'name': 'Dust Load',
        'bounds': [0, .1, .2, .4, .8, 1.2, 1.6, 3.2, 6.4, 10],
        'mul': 1e3,
        'title' : "Dust Load Forecast run on %(hour)s %(day)s %(month)s %(year)s",
        'default': False,
    },
    'dust_depw': {
        'name': 'Dust Wet Deposition',
        'bounds': [0, 0.5, 5, 10, 50, 100, 400, 800, 1600, 10000],
        'mul': 1e6,
        'title' : u"Dust Wet Deposition Forecast run on %(hour)s %(day)s %(month)s %(year)s",
        'default': False,
    },
    'dust_depd': {
        'name': 'Dust Dry Deposition',
        'bounds': [0, 0.5, 5, 10, 50, 100, 400, 800, 1600, 10000],
        'mul': 1e6,
        'title' : u"Dust Dry Deposition Forecast run on %(hour)s %(day)s %(month)s %(year)s",
        'default': False,
    },
    'dust_ext_sfc': {
        'name': 'Dust Surface Extinction',
        'bounds': [0, 5, 10, 25, 100, 250, 1000, 2500, 10000, 100000],
        'mul': 1e6,
        'title' : u"Dust Surface Extinction Forecast run on %(hour)s %(day)s %(month)s %(year)s",
        'default': False,
    },
}

DEFAULT_VAR = [v for v in VARS.keys() if VARS[v]['default'] is True][0]

def magnitude(num):
    """ Calculate magnitude """
    return int(math.floor(math.log10(num)))


def normalize_vals(vals, valsmin, valsmax, rnd=2):
    """ Normalize values to 0-1 scale """
    vals = np.array(vals)
    if rnd < 2:
        rnd = 2
    return np.around((vals-valsmin)/(valsmax-valsmin), rnd)

#def scalarmappable(cmap, cmin, cmax):
#    colormap = cm.get_cmap(cmap)
#    norm = Normalize(vmin=cmin, vmax=cmax)
#    return cm.ScalarMappable(norm=norm, cmap=colormap)
#
#def get_scatter_colors(sm, df):
#    grey = 'rgba(128,128,128,1)'
#    return ['rgba' + str(sm.to_rgba(m, bytes = True, alpha = 1)) \
#            if not np.isnan(m) else grey for m in df]

def get_colorscale(varname):
    """ Create colorscale """
    bounds = np.array(VARS[varname]['bounds']).astype('float32')
    magn = magnitude(bounds[-1])
    n_bounds = normalize_vals(bounds, bounds[0], bounds[-1], magn)
    norm = mpl.colors.BoundaryNorm(bounds, len(bounds)-1, clip=True)
    s_map = cm.ScalarMappable(norm=norm, cmap=COLORMAP)

    return [[idx, 'rgba' + str(s_map.to_rgba(val, bytes=True))] for idx, val in
            zip(n_bounds, bounds)]


class FigureHandler(object):
    """ Class to manage the figure creation """

    def __init__(self, filepath):
        self.input_file = nc_file(filepath, 'r')
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
        self.styles = {
            "open-street-map": "Open street map",
            "carto-positron": "Light",
            "carto-darkmatter": "Dark",
            "stamen-terrain": "Terrain",
            "stamen-toner": "White/Black",
            "stamen-watercolor": "Watercolor"
        } # "dark", "light", "streets", "satellite-streets"]
        self.bounds = {varname:np.array(VARS[varname]['bounds']).astype('float32')
                       for varname in self.varlist}
        self.colormaps = {varname:get_colorscale(varname)
                          for varname in self.varlist}

    def get_animation_buttons(self):
        """ Returns play and stop buttons """
        return dict(
            type="buttons",
            direction="left",
            buttons=[dict(label="&#9654;",
                          method="animate",
                          args=[None,
                                dict(frame=dict(duration=animation_time,
                                                redraw=True),
                                     transition=dict(duration=transition_time,
                                                     easing="quadratic-in-out"),
                                     fromcurrent=True,
                                     mode='immediate'
                                    )
                               ]),
                     dict(label="&#9724;",
                          method="animate",
                          args=[[None],
                                dict(frame=dict(duration=0,
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
                          self.styles.keys()]),
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
            label=self.styles[style].capitalize(),
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
        idx = np.where(var.ravel() >= VARS[varname]['bounds'][1]) #!=-9.e+33)
        #print(x.ravel()[idx])
        xlon = self.xlon.ravel()[idx]
        ylat = self.ylat.ravel()[idx]
        var = var.ravel()[idx]

        return xlon, ylat, var

    def retrieve_cdatetime(self, tstep=0):
        """ Retrieve data from NetCDF file """
        #print(type(self.tim), self.tim[tstep], type(tstep), tstep)
        if self.what == 'days':
            cdatetime = self.rdatetime + relativedelta(days=self.tim[tstep])
        elif self.what == 'hours':
            cdatetime = self.rdatetime + relativedelta(hours=self.tim[tstep])
        elif self.what == 'minutes':
            cdatetime = self.rdatetime + relativedelta(minutes=self.tim[tstep])
        elif self.what == 'seconds':
            cdatetime = self.rdatetime + relativedelta(seconds=self.tim[tstep])

        #print(cdatetime.strftime("%Y%m%d %H:%M"), tstep)
        return cdatetime

    def generate_var_tstep_trace(self, varname, tstep=0):
        """ Generate trace to be added to data, per variable and timestep """
        xlon, ylat, val = self.set_data(varname, tstep)
        name = VARS[varname]['name']
        colorscale = self.colormaps[varname]
        #print(name, magn, norm_bounds, colorscale)
        return dict(
            type='scattermapbox',
            lon=xlon,
            lat=ylat,
            text=val,
            #mode='lines',
            showlegend=False,
            opacity=0.6,
            #fill="toself",
            name=name,
            hovertemplate=\
                """lon: %{lon:.4f}<br>lat: %{lat:.4f}<br>value: %{text:.4f}<br>""",
            marker=dict(
                autocolorscale=True,
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
                    "tickvals" : self.bounds[varname],
                    #"title": "ºC",
                }, #gives your legend some units
                cmin=self.bounds[varname][0],
                cmax=self.bounds[varname][-1],
                #showscale=True,
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

        #print([f['name'] for f in frames])

        sliders = [dict(steps=
                        [dict(method='animate',
                              args=[[varname+str(tstep)],
                                    dict(mode='immediate',
                                         frame=dict(duration=animation_time,
                                                    redraw=True),
                                         transition=dict(duration=slider_transition_time,
                                                         easing="quadratic-in-out",
                                                        )
                                        )
                                   ],
                              label='{:d}'.format(tstep*3),
                              value=tstep,
                             ) for tstep in range(25)],
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

        #print([st['args'][0] for st in sliders[0]['steps']])

        fig.update_layout(
            title=dict(text=title, y=0.95),
            autosize=True,
            hovermode="closest",        # highlight closest point on hover
            mapbox=test_mapbox(),
            showlegend=False,
            # margin={'l':0, 'r':0, 'b':0, 't':0},
            width=1200,
            height=800,
            updatemenus=[
                self.get_animation_buttons(),
                self.get_mapbox_style_buttons(),
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
            ],
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

            sliders=sliders
        )

        #return dict(data=data, layout=layout)
        return fig

#if __name__ == "__main__":
#    FIG = FigureHandler().run_plot()
#    py.iplot(FIG, filename="dust_out.html") #, width=1000)
#    plotly.plot(FIG,
#    filename='/esarchive/scratch/Earth/fbeninca/plotly_test/test.html',
#    auto_open=False)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Data Handler """

# import plotly
import plotly.graph_objs as go
from matplotlib.colors import ListedColormap
# import matplotlib.pyplot as plt
import numpy as np
from netCDF4 import Dataset as nc_file
# import xarray as xr
import json

from utils import get_colorscale

from datetime import datetime
from dateutil.relativedelta import relativedelta
import sys


COLORS = ['#a1ede3', '#5ce3ba', '#fcd775', '#da7230',
          '#9e6226', '#714921', '#392511', '#1d1309']

COLORMAP = ListedColormap(COLORS)

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

    def __init__(self, filepath, selected_date):
        self.input_file = nc_file(filepath)
        lon = self.input_file.variables['lon'][:]
        lat = self.input_file.variables['lat'][:]
        time_obj = self.input_file.variables['time']
        self.tim = time_obj[:]
        self.what, _, rdate = time_obj.units.split()[:3]
        self.rdatetime = datetime.strptime("{}".format(rdate), "%Y-%m-%d")
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

        try:
            self.selected_date = datetime.strptime(
                selected_date, "%Y%m%d").strftime("%Y-%m-%d")
        except:
            self.selected_date = selected_date

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

    def get_mapbox(self, style='open-street-map', relayout=False, zoom=3):
        """ Returns mapbox layout """
        mapbox_dict = dict(
            bearing=0,
            center=go.layout.mapbox.Center(
                lat=(self.ylat.max()-self.ylat.min())/2 + self.ylat.min(),
                lon=(self.xlon.max()-self.xlon.min())/2 + self.xlon.min(),
            ),
            pitch=0,
            zoom=zoom,
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
            json.load(open("./data/geojson/{:02d}_{}_{}.geojson"
                           .format(tstep, self.selected_date, varname)))

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
        print(varname, self.colormaps[varname], values)
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
        )

    def generate_var_tstep_trace(self, varname, tstep=0):
        """ Generate trace to be added to data, per variable and timestep """
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
                color=val,
                opacity=0.6,
                size=0,
                colorscale=self.colormaps[varname],
                cmin=self.bounds[varname][0],
                cmax=self.bounds[varname][-1],
                showscale=True,
                colorbar={
                    "borderwidth": 0,
                    "outlinewidth": 0,
                    "thickness": 15,
                    "tickfont": {"size": 14},
                    "tickvals": self.bounds[varname][:-1],
                    "tickmode": "array",
                },
            ),

        )

    def get_title(self, varname, tstep=0):
        """ return title according to the date """
        rdatetime = self.rdatetime
        cdatetime = self.retrieve_cdatetime(tstep)
        return r'{}'.format(VARS[varname]['title'] % {
            'rhour':  rdatetime.strftime("%H"),
            'rday':   rdatetime.strftime("%d"),
            'rmonth': rdatetime.strftime("%b"),
            'ryear':  rdatetime.strftime("%Y"),
            'shour':  cdatetime.strftime("%H"),
            'sday':   cdatetime.strftime("%d"),
            'smonth': cdatetime.strftime("%b"),
            'syear':  cdatetime.strftime("%Y"),
            'step':   "{:02d}".format(tstep*3),
        })

    def retrieve_var_tstep(self, varname, tstep=0):
        """ run plot """
        fig = go.Figure()
        tstep = int(tstep)
        print('Adding contours ...')
        fig.add_trace(self.generate_contour_tstep_trace(varname, tstep))
        print('Adding points ...')
        fig.add_trace(self.generate_var_tstep_trace(varname, tstep))

        # axis_style = dict(
        #     zeroline=False,
        #     showline=False,
        #     showgrid=True,
        #     ticks='',
        #     showticklabels=False,
        # )

#         print('Adding frames ...')
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

        print('Update layout ...')
        fig.update_layout(
            title=dict(text=self.get_title(varname, tstep), x=0.02, y=0.93),
            uirevision=True,
            autosize=True,
            hovermode="closest",        # highlight closest point on hover
            mapbox=self.get_mapbox(),
            # width="100%",
            height=800,
            updatemenus=[
                # get_animation_buttons(),
                self.get_mapbox_style_buttons(),
            ],
            margin={"r": 0, "t": 30, "l": 20, "b": 20},
#             xaxis=dict(
#                 range=[self.xlon.min(), self.xlon.max()]
#             ),
#             yaxis=dict(
#                 range=[self.ylat.min(), self.ylat.max()]
#             ),
            # sliders=sliders
        )

        print('Returning fig of size {}'.format(sys.getsizeof(fig)))
        return fig

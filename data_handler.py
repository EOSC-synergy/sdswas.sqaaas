#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Data Handler """

import plotly
import plotly.graph_objs as go
import matplotlib as mpl
from matplotlib import cm
import numpy as np
from netCDF4 import Dataset as nc_file
import math

from datetime import datetime
from dateutil.relativedelta import relativedelta


mapbox_access_token = \
"pk.eyJ1IjoiZmJlbmluY2EiLCJhIjoiY2p1ODZhdW9qMDZ3eTN5b2IxN2JzdzUyeSJ9.m0QotzSgIz0Bi0gIynzG6A"

animation_time = 1000
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


COLORS = ['#ffffff', '#a1ede3', '#5ce3ba', '#fcd775', '#da7230',
          '#9e6226', '#714921', '#392511', '#1d1309']


COLORMAP = mpl.colors.ListedColormap(COLORS[1:-1])
COLORMAP.set_under(COLORS[0])
COLORMAP.set_over(COLORS[-1])


VARS = {
    'od550_dust': {
        'name': 'Dust Optical Depth',
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

DEFAULT_VAR = [var for var in VARS.keys() if VARS[var]['default'] == True][0]

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

def get_colorscale(n_bounds, bounds):
    """ Create colorscale """
    norm = mpl.colors.BoundaryNorm(bounds, len(bounds)-1, clip=True)
    s_map = cm.ScalarMappable(norm=norm, cmap=COLORMAP)

    return [[i, 'rgba' + str(s_map.to_rgba(v, bytes=True))] for i, v in
            zip(n_bounds, bounds)]


class FigureHandler:
    """ Class to manage the figure creation """

    def __init__(self, filepath):
        self.f = nc_file(filepath, 'r')
        self.lon = self.f.variables['lon'][:]
        self.lat = self.f.variables['lat'][:]
        time_obj = self.f.variables['time']
        self.tim = time_obj[:]
        self.what, _, rdate = time_obj.units.split()[:3]
        self.rdatetime = datetime.strptime("{}".format(rdate), "%Y-%m-%d")
        self.varlist = [v for v in self.f.variables if v not in
                        ('lon', 'lat', 'alt', 'lev', 'longitude',
                         'latitude', 'altitude', 'levels', 'time')]
        self.xlon, self.ylat = np.meshgrid(self.lon, self.lat)
        self.styles = ["dark", "light", "streets", "satellite-streets"]

    def get_mpb(self, style='dark', relayout=False):
        """ Returns mapbox layout """
        mapbox_dict = dict(
            accesstoken=mapbox_access_token,
            bearing=0,
            center=go.layout.mapbox.Center(
                lat=(self.lat.max()-self.lat.min())/2 + self.lat.min(),
                lon=(self.lon.max()-self.lon.min())/2 + self.lon.min(),
            ),
            pitch=0,
            zoom=3,
            style=style,
        )

        if relayout == False:
            return mapbox_dict

        return dict(
            args=["mapbox", mapbox_dict ],
            label=style.capitalize(),
            method="relayout"
        )

    def get_updated_trace(self, varname, tstep=0):
        return dict(
            args=["scattermapbox", self.generate_var_tstep_trace(varname,
                                                                 tstep)],
            label=VARS[varname]['name'],
            method="restyle"
        )

    def set_data(self, varname, tstep=0):
        """ Set time dependent data """
        mul = VARS[varname]['mul']
        var = self.f.variables[varname][tstep]*mul
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
        bounds = np.array(VARS[varname]['bounds']).astype('float32')
        name = VARS[varname]['name']
        magn = magnitude(bounds[-1])
        norm_bounds = normalize_vals(bounds, bounds[0], bounds[-1], magn)
        #colorscale = list(zip(norm_bounds, COLORS))
        colorscale = get_colorscale(norm_bounds, bounds)
        #print(name, magn, norm_bounds, colorscale)
        return dict(
            type='scattermapbox',
            lon=xlon,
            lat=ylat,
            text=val,
            mode='markers',
            showlegend=False,
            opacity=0.6,
            name=name,
            hovertemplate=\
                """lon: %{lon:.4f}<br>lat: %{lat:.4f}<br>value: %{text:.4f}<br>""",
            marker=dict(
                autocolorscale=False,
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
                    "tickvals" : bounds,
                    #"title": "ºC",
                }, #gives your legend some units
                cmin=bounds[0],
                cmax=bounds[-1],
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

#        axis_style = dict(
#            zeroline=False,
#            showline=False,
#            showgrid=True,
#            ticks='',
#            showticklabels=False,
#        )

        frames=[dict(
            data=self.generate_var_tstep_trace(varname, tstep=num),
            #traces=[0],
            name=varname+str(num))
            for num in range(0,25,1)]

        fig['frames'] = frames

        #print([f['name'] for f in frames])

        sliders = [dict(steps=
                        [dict(method='animate',
                              args=[[varname+str(tstep)],
                                  dict(mode='immediate',
                                       frame=dict(duration=animation_time,
                                                  redraw=True),
                                       transition=dict(duration=slider_transition_time,
                                                       easing="cubic-in-out",
                                                     )
                                    )
                                ],
                              label='{:d}'.format(tstep*3),
                              value=tstep,
                             ) for tstep in range(0,25,1)],
                        transition=dict(duration=slider_transition_time,
                                        easing="cubic-in-out"),
                        x=0.08,#slider starting position  
                        y=0,
                        len=0.93,
                        currentvalue=dict(font=dict(size=12),
                            prefix='Timestep: ',
                            visible=True,
                            xanchor= 'center'),
                        )
                   ]

        #print([st['args'][0] for st in sliders[0]['steps']])

        fig.update_layout(
            title=dict(text=title, y=0.93),
            autosize=True,
            hovermode="closest",        # highlight closest point on hover
            mapbox=self.get_mpb(),
            width=1200,
            height=800,
            updatemenus=[
                dict(
                    type="buttons",
                    buttons=[dict(label="Play",
                                  method="animate",
                                  args=[None,
                                        dict(frame=dict(duration=animation_time, redraw=True),
                                        transition=dict(duration=transition_time,
                                                       easing="quadratic-in-out"),
                                        fromcurrent=True,
                                        mode='immediate'
                                        )
                                    ]),
                             dict(label="Pause",
                                  method="animate",
                                  args=[[None],
                                        dict(frame=dict(duration=0,
                                                        redraw=True),
                                        transition=dict(duration=0),
                                        mode='immediate'
                                        )
                    ])
                            ],
                    x=0,
                    xanchor="left",
                    y=-0.04,
                    yanchor="top"
                ),
                dict(
                    type="buttons",
                    direction="left",
                    buttons = list([self.get_mpb(style, relayout=True) for style in
                                    self.styles]),
                    pad={"r": 10, "t": 10},
                    showactive=True,
                    x=0.7,
                    xanchor="left",
                    y=1.08,
                    yanchor="top"
                ),
#                dict(
#                    type="buttons",
#                    direction="down",
#                    buttons = list([self.retrieve_var_tstep(varname) for
#                                    varname in self.varlist if varname !=
#                                    DEFAULT_VAR]),
#                    pad={"r": 10, "t": 10},
#                    showactive=True,
#                    x=1.1,
#                    xanchor="left",
#                    y=1.06,
#                    yanchor="top"
#                ),
            ],
#            annotations=[
#                dict(
#                    x=1.13,
#                    y=0.99,
#                    align="right",
#                    valign="top",
#                    text='VARIABLES',
#                    showarrow=False,
#                    xref="paper",
#                    yref="paper",
#                    xanchor="center",
#                    yanchor="top"
#                )
#            ]

#            slider=slider,
            sliders=sliders
        )

        #return dict(data=data, layout=layout)
        return fig

#        geo=go.layout.Geo(
#            scope='europe',
#            projection=go.layout.geo.Projection(type='equirectangular'),
#            showland=True,
#            showcountries=True,
#            showcoastlines=True,
#            landcolor='rgb(243, 243, 243)',
#            countrycolor='rgb(204, 204, 204)',
#            lonaxis=go.layout.geo.Lonaxis(
#                showgrid=True,
#                gridcolor='rgb(102, 102, 102)',
#                gridwidth=0.5
#            ),
#            lataxis=go.layout.geo.Lataxis(
#                showgrid=True,
#                gridcolor='rgb(102, 102, 102)',
#                gridwidth=0.5
#            ),
#        ),
#        annotations=Annotations([
#            Annotation(
#                text=anno_text,
#                xref='paper',
#                yref='paper',
#                x=0,
#                y=1,
#                yanchor='bottom',
#                showarrow=False
#            )
#        ]),
# Shift 'lon' from [0,360] to [-180,180], make numpy array
#tmp_lon = np.array([lon[n]-360 if l>=180 else lon[n]
#                   for n,l in enumerate(lon)])  # => [0,180]U[-180,2.5]
#
#i_east, = np.where(tmp_lon>=0)  # indices of east lon
#i_west, = np.where(tmp_lon<0)   # indices of west lon
#lon = np.hstack((tmp_lon[i_west], tmp_lon[i_east]))  # stack the 2 halves

# Correspondingly, shift the 'air' array
#tmp_air = np.array(air)
#air = np.hstack((tmp_air[:,i_west], tmp_air[:,i_east]))

#print(np.nanmax(var))
#print(np.nanmin(var))
#print(type(var))

#trace1 = go.Contour(
#    showlegend=True,
#    opacity=0.6,
#    name='Dust Optical Depth',
#    hovertemplate="""lon: %{x}\n
#lat: %{y}\n
#aod: %{z}\n""",
#    hoverlabel=dict(bordercolor='yellow'),
#    z=var[0],
#    x=lon,
#    y=lat,
#    #    [ 0.  ,  0.01,  0.02,  0.04,  0.08,  0.12,  0.16,  0.32,  0.64,  1.  ]
#    zauto=True,  # custom contour levels
#    zmin=np.nanmin(var),      # first contour level
#    zmax=np.nanmax(var),        # last contour level  => colorscale is centered about 0
#    colorscale=colorscale,
#    colorbar={
#        "borderwidth": 0,
#        "outlinewidth": 0,
#        "thickness": 15,
#        "tickfont": {"size": 14},
#        #"title": "ºC",
#    }, #gives your legend some units
#
#    contours={
#        "end": np.nanmax(var),
#        "showlines": False,
#        "size": 0.5, #this is your contour interval
#        "start": np.nanmin(var)
#    },
#
#
#)



if __name__ == "__main__":
    FIG = FigureHandler().run_plot()
#    py.iplot(FIG, filename="dust_out.html") #, width=1000)
    plotly.plot(FIG, filename='/esarchive/scratch/Earth/fbeninca/plotly_test/test.html', auto_open=False)

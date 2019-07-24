#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Plotly-
"""

import plotly
import plotly.graph_objs as go
from plotly.graph_objs import \
        Contour, Scatter, Annotations, Figure, Layout
import matplotlib as mpl
from matplotlib import cm
import numpy as np
from netCDF4 import Dataset as nc_file
import math

from datetime import datetime
from dateutil.relativedelta import relativedelta


mapbox_access_token = \
"pk.eyJ1IjoiZmJlbmluY2EiLCJhIjoiY2p1ODZhdW9qMDZ3eTN5b2IxN2JzdzUyeSJ9.m0QotzSgIz0Bi0gIynzG6A"


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
        #'bounds': [.1, .2, .4, .8, 1.2, 1.6, 3.2, 6.4],
        'mul': 1,
    },
    'sconc_dust': {
        'name': 'Dust Surface Concentration',
        'bounds': [0, 5, 20, 50, 200, 500, 2000, 5000, 20000, 100000],
        #'bounds': [5, 20, 50, 200, 500, 2000, 5000, 20000],
        'mul': 1e9,
    },
}


def magnitude(x):
    return int(math.floor(math.log10(x)))


def normalize_vals(vals, valsmin, valsmax, rnd=2):
    vals = np.array(vals)
    if rnd < 2: rnd = 2
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
#
def get_colorscale(n_bounds, bounds):
    norm = mpl.colors.BoundaryNorm(n_bounds, len(n_bounds)-1, clip=True)
    s_map = cm.ScalarMappable(norm=norm, cmap=COLORMAP)

    return [[i, 'rgba' + str(s_map.to_rgba(v, bytes=True))] for i,v in
            zip(n_bounds, bounds) ]


class FigureHandler:

    def __init__(self, filepath):
        self.f = nc_file(filepath, 'r')
        self.lon = self.f.variables['lon'][:]
        self.lat = self.f.variables['lat'][:]
        time_obj = self.f.variables['time']
        self.tim = time_obj[:]
        self.what, _, rdate = time_obj.units.split()[:3]
        self.rdatetime = datetime.strptime("{}".format(rdate), "%Y-%m-%d")
#        self.varmax = None
#        self.varmin = None
        self.varlist = [v for v in self.f.variables if v not in
                        ('lon', 'lat', 'alt', 'lev', 'longitude',
                         'latitude', 'altitude', 'levels', 'time')]
        self.xlon, self.ylat = np.meshgrid(self.lon, self.lat)


    def set_data(self, varname, tstep=0):
        """ Set time dependent data """
        mul = VARS[varname]['mul']
        var = self.f.variables[varname][tstep]*mul
#        self.varmax = np.nanmax(self.var)
#        self.varmin = np.nanmin(self.var)
        #print(self.var)
        idx = np.where(var.ravel() >= VARS[varname]['bounds'][1]) #!=-9.e+33)
        #print(x.ravel()[idx])
        xlon = self.xlon.ravel()[idx]
        ylat = self.ylat.ravel()[idx]
        var = var.ravel()[idx]

        return xlon, ylat, var

    def retrieve_cdatetime(self, tstep=0):
        # Retrieve data from NetCDF file
        #print(type(self.tim), self.tim[tstep], type(tstep), tstep)
        if self.what == 'days':
            cdatetime = self.rdatetime + relativedelta(days=self.tim[tstep])
        elif self.what == 'hours':
            cdatetime = self.rdatetime + relativedelta(hours=self.tim[tstep])
        elif self.what == 'minutes':
            cdatetime = self.rdatetime + relativedelta(minutes=self.tim[tstep])
        elif self.what == 'seconds':
            cdatetime = self.rdatetime + relativedelta(seconds=self.tim[tstep])

        print(cdatetime.strftime("%Y%m%d %H:%M"))
        return cdatetime

    def run_plot(self, tstep=0):
        """ run plot """
        fig = go.Figure()
        tstep = int(tstep)
        #data = []
        cdatetime = self.retrieve_cdatetime(tstep)
        for var in self.varlist:
            xlon, ylat, val = self.set_data(var, tstep)
            bounds = np.array(VARS[var]['bounds']).astype('float32')
            name = VARS[var]['name']
            magn = magnitude(bounds[-1])
            norm_bounds = normalize_vals(bounds, bounds[0], bounds[-1], magn)
            #colorscale = list(zip(norm_bounds, COLORS))
            colorscale = get_colorscale(norm_bounds, bounds)
            print(name, magn, norm_bounds, colorscale)
            visible = True
            if name != 'Dust Optical Depth':
                visible = 'legendonly'
                #continue
            fig.add_trace(
            #data.append(
                dict( #go.Scattermapbox(
                    type='scattermapbox',
                    visible=visible,
                    lon=xlon,
                    lat=ylat,
                    text=val,
                    mode='markers',
                    showlegend=True,
                    opacity=0.4,
                    name=name,
                    hovertemplate=
                        """lon: %{lon:.4f}<br>lat: %{lat:.4f}<br>value: %{text:.4f}<br>""",
                    marker=dict( #go.scattermapbox.Marker(
                        autocolorscale=False,
                        color=val,
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
                        cmin=bounds[0], #self.varmin,      # first contour level
                        cmax=bounds[-1], #self.varmax,        # last contour level  => colorscale is centered about 0
                        showscale=True,
                    ),

                )
            ) #trace1] #+traces_cc

        title = u"""Dust OD Forecast for %(hour)s %(day)s %(month)s %(year)s""" % {
            'hour':  cdatetime.strftime("%H"),
            'day':   cdatetime.strftime("%d"),
            'month': cdatetime.strftime("%b"),
            'year':  cdatetime.strftime("%Y"),
        }

    #    anno_text = "Data courtesy of \
    #    <a href='http://www.esrl.noaa.gov/psd/data/composites/day/'>\
    #    NOAA Earth System Research Laboratory</a>"

#        axis_style = dict(
#            zeroline=False,
#            showline=False,
#            showgrid=True,
#            ticks='',
#            showticklabels=False,
#        )

        #layout = dict(
        fig.update_layout(
            #title=title,
            showlegend=True,
#            autosize=True,
            hovermode="closest",        # highlight closest point on hover
#            xaxis=go.layout.XAxis(
#                axis_style,
#                range=[x.min(), x.max()]  # restrict x-axis to range of lon
#            ),
#            yaxis=go.layout.YAxis(
#                axis_style,
#                range=[y.min(), y.max()]  # restrict y-axis to range of lat
#            ),
            mapbox=go.layout.Mapbox(
                accesstoken=mapbox_access_token,
                bearing=0,
                center=go.layout.mapbox.Center(
                    lat=(self.lat.max()-self.lat.min())/2 + self.lat.min(),
                    lon=(self.lon.max()-self.lon.min())/2 + self.lon.min(),
                ),
                pitch=0,
                zoom=3,
                style='dark',
            ),
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
            width=1200,
            height=1000,
        )

        #return dict(data=data, layout=layout)
        return fig
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

# Make shortcut to Basemap object,
# not specifying projection type for this example
#m = Basemap(resolution='c')

# Make trace-generating function (return a Scatter object)
#def make_scatter(x,y):
#    return Scatter(
#        x=x,
#        y=y,
#        mode='lines',
#        line=Line(color="black"),
#        name=' '  # no name on hover
#    )

# Functions converting coastline/country polygons to lon/lat traces
def polygons_to_traces(poly_paths, n_poly):
    '''
    pos arg 1. (poly_paths): paths to polygons
    pos arg 2. (n_poly): number of polygon to convert
    '''
    # init. plotting list
    res = dict(
        x=[],
        y=[],
        mode='lines',
        line=go.scatter.Line(color="grey", width=1),
        name=' '
    )

    for i_poly in range(n_poly):
        poly_path = poly_paths[i_poly]

        # get the Basemap coordinates of each segment
        coords_cc = np.array(
            [(vertex[0], vertex[1])
             for (vertex, code) in poly_path.iter_segments(simplify=False)]
        )

        # convert coordinates to lon/lat by 'inverting' the Basemap projection
        lon_cc, lat_cc = m(coords_cc[:, 0], coords_cc[:, 1], inverse=True)


        # add plot.ly plotting options
        res['x'] = res['x'] + lon_cc.tolist() + [np.nan]
        res['y'] = res['y'] + lat_cc.tolist() + [np.nan]

        # traces.append(make_scatter(lon_cc,lat_cc))

    return [res]

# Function generating coastline lon/lat traces
def get_coastline_traces():
    """ coastlines """
    poly_paths = m.drawcoastlines().get_paths() # coastline polygon paths
    n_poly = 91  # use only the 91st biggest coastlines (i.e. no rivers)
    return polygons_to_traces(poly_paths, n_poly)

# Function generating country lon/lat traces
def get_country_traces():
    """ countries """
    poly_paths = m.drawcountries().get_paths() # country polygon paths
    n_poly = len(poly_paths)  # use all countries
    return polygons_to_traces(poly_paths, n_poly)



if __name__ == "__main__":
    FIG = FigureHandler().run_plot()
#    py.iplot(FIG, filename="dust_out.html") #, width=1000)
    plotly.plot(FIG, filename='/esarchive/scratch/Earth/fbeninca/plotly_test/test.html', auto_open=False)

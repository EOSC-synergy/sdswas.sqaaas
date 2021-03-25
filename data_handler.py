# -*- coding: utf-8 -*-
""" Data Handler """

# import plotly
import plotly.graph_objs as go
from matplotlib.colors import ListedColormap
import numpy as np
from netCDF4 import Dataset as nc_file
import pandas as pd
import feather
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

COLORMAP = ListedColormap(COLORS)

VARS = json.load(open(os.path.join(DIR_PATH, 'conf/vars.json')))
MODELS = json.load(open(os.path.join(DIR_PATH, 'conf/models.json')))
OBS = json.load(open(os.path.join(DIR_PATH, 'conf/obs.json')))

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
        filepath = "{}.nc".format(os.path.join(OBS[obs]['path'], 'netcdf', OBS[obs]['template'].format(months[0])))
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

    def __init__(self, obs, start_date, end_date, variable):
        self.obs = obs
        self.model = list(MODELS.keys())
        self.variable = variable
        self.dataframe = []
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
                cur_lat = round(timeseries[lat_col][0], 4)
                cur_lon = round(timeseries[lon_col][0], 4)


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
            VARS[self.variable]['name'], round(lat, 4), round(lon, 4)
        )
        fig = go.Figure()

        for mod, fpath in zip(model, self.fpaths):
            print(mod, fpath)
            ts_lat, ts_lon, ts_index, ts_values = retrieve_timeseries(fpath, lat, lon, self.variable, method=method)

            fig.add_trace(dict(
                    type='scatter',
                    name="{} ({}, {})".format(
                        mod.upper(), ts_lat.round(4), ts_lon.round(4)),
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

#        fig['layout']['xaxis'].update(range=['2020-04-01', '2020-04-17 09:00'])

        return fig


class FigureHandler(object):
    """ Class to manage the figure creation """

    def __init__(self, model=None, selected_date=None):
        if isinstance(model, list):
            model = model[0]

        self.model = model
        if model:
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
            self.bounds = {
                varname: np.array(VARS[varname]['bounds']).astype('float32')
                for varname in varlist
            }

            self.colormaps = {
                varname: get_colorscale(self.bounds[varname], COLORMAP)
                for varname in varlist
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
        geojson_file = GEOJSON_TEMPLATE.format(MODELS[self.model]['path'],
                self.selected_date_plain, tstep, self.selected_date_plain, varname)

        if os.path.exists(geojson_file):
            geojson = json.load(open(geojson_file))
        else:
            print('ERROR', geojson_file, 'not available')
            geojson = {
                    "type": "FeatureCollection",
                    "features": []
                    }

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

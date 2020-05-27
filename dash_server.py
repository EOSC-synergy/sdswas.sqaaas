#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Dash Server """

import debug
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output
from dash.dependencies import Input
from dash.dependencies import State

from data_handler import FigureHandler
from data_handler import TimeSeriesHandler
from data_handler import DEFAULT_VAR
from data_handler import DEFAULT_MODEL
from data_handler import FREQ
from data_handler import VARS
from data_handler import MODELS
from data_handler import Observations1dHandler

from datetime import datetime as dt
import math

import tabs
from tabs import end_date

# models
# F_PATH = './data/MODEL/netcdf/{}12_3H_NMMB-BSC_OPER.nc4'
#
F_PATH = './data/models/{}/netcdf/{}{}.nc4'
TS_PATH = './data/feather/{}.ft'


def get_timeseries(model, var, lat, lon):
    """ Retrieve timeseries """
    # print(var, selected_date, tstep)
    print('SERVER: TS init ... ')
    th = TimeSeriesHandler(model, var)
    print('SERVER: TS generation ... ')
    return th.retrieve_timeseries(lat, lon)


def get_figure(model, var, selected_date=end_date, tstep=0):
    """ Retrieve figure """
    # print(var, selected_date, tstep)
    try:
        selected_date = dt.strptime(
            selected_date, "%Y-%m-%d %H:%M:%S").strftime("%Y%m%d")
    except:
        pass
    print('SERVER: Figure init ... ')
    fh = FigureHandler(model, selected_date)
    print('SERVER: Figure generation ... ')
    return fh.retrieve_var_tstep(var, tstep)


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
# server = app.server
# app.config.suppress_callback_exceptions = True

print('SERVER: start creating app layout')
app.layout = html.Div(
    children=[
        dcc.Tabs(children=[
            dcc.Tab(label='Forecast',
                    className='horizontal-menu',
                    children=[
                        tabs.line_tool,
                        html.Div(
                            dcc.Graph(
                                id='graph-with-slider',
                                figure=get_figure(DEFAULT_MODEL,
                                                  DEFAULT_VAR, end_date, 0),
                            ),
                        ),
                        dcc.Interval(id='slider-interval',
                                     interval=3000,
                                     n_intervals=0,
                                     disabled=True),
                        tabs.time_slider,
                        tabs.time_series,
                    ]),
            ]),
            dcc.Tab(label='Evaluation',
                    className='horizontal-menu',
                    children=[]),
            dcc.Tab(label='Observations',
                    className='horizontal-menu',
                    children=[]),
        ],
)

print('SERVER: stop creating app layout')


@app.callback(
    [Output('timeseries-modal', 'figure'),
     Output("ts-modal", "is_open")],
    [Input('graph-with-slider', 'clickData')],
    [State('graph-with-slider', 'hoverData'),
     State('model-dropdown', 'value'),
     State('variable-dropdown', 'value')],
)
def show_timeseries(cdata, hdata, model, variable):

    if hdata:
        lat = hdata['points'][0]['lat']
        lon = hdata['points'][0]['lon']
        return get_timeseries(model, variable, lat, lon), True

    return None, False


@app.callback([
    Output('slider-interval', 'disabled'),
    Output('slider-interval', 'n_intervals')],
    [Input('btn-play', 'n_clicks')],
    [State('slider-interval', 'disabled'),
     State('slider-graph', 'value')])
def start_stop_autoslider(n, disabled, value):
    print("VALUE", value)
    if n:
        return not disabled, int(value/FREQ)
    return disabled, int(value/FREQ)


@app.callback(
    Output('slider-graph', 'value'),
    [Input('slider-interval', 'n_intervals')])
def update_slider(n):
    print('SERVER: updating slider-graph ' + str(n))
    if not n:
        return

    if n >= 24:
        tstep = int(round(24*math.modf(n/24)[0], 0))
    else:
        tstep = int(n)
    print('SERVER: updating slider-graph ' + str(tstep*FREQ))
    return tstep*FREQ


@app.callback(
    Output('graph-with-slider', 'figure'),
    [Input('model-date-picker', 'date'),
     Input('model-dropdown', 'value'),
     Input('variable-dropdown', 'value'),
     Input('obs-dropdown', 'value'),
     Input('slider-graph', 'value')],
    [State('graph-with-slider', 'relayoutData')])
def update_figure(date, model, variable, obs, tstep, relayoutdata):
    print('SERVER: calling figure from picker callback')
    # print('SERVER: interval ' + str(n))
    print('SERVER: tstep ' + str(tstep))

    if date is not None:
        date = date.split(' ')[0]
        try:
            date = dt.strptime(
                date, "%Y-%m-%d").strftime("%Y%m%d")
        except:
            pass
        print('SERVER: callback date {}'.format(date))
    else:
        date = end_date

    if model is None:
        model = DEFAULT_MODEL

    if variable is None:
        variable = DEFAULT_VAR

    if tstep is not None:
        tstep = int(tstep/FREQ)
    else:
        tstep = 0

    print('SERVER: tstep calc ' + str(tstep))

    fig = get_figure(model, variable, date, tstep)

    if obs:
        obs_handler = Observations1dHandler('./data/obs/aeronet/netcdf/od550aero_202004.nc', date)
        obs_trace = obs_handler.generate_obs1d_tstep_trace(variable)
        fig.add_trace(obs_trace)

    if relayoutdata:
        relayoutdata = {k:relayoutdata[k] for k in relayoutdata if k not in ('mapbox._derived',)}
        fig.layout.update(relayoutdata)

    return fig


# Dash CSS
# app.css.append_css({"external_url": '{}/css/bWLwgP.css'.format(os.getcwd())})

# Loading screen CSS
# app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/brPBPO.css"})


if __name__ == '__main__':
    app.run_server(debug=True, processes=8, threaded=False, host='localhost', port=9999)

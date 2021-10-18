#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Dash Server """

# import debug
import dash
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
from dash.dependencies import Output
from dash.dependencies import Input
from dash.dependencies import State
from dash.dependencies import ALL
from dash.dependencies import MATCH
from dash.exceptions import PreventUpdate
import flask
from flask_caching import Cache
from pathlib import Path

from data_handler import DEFAULT_VAR
from data_handler import DEFAULT_MODEL
from data_handler import VARS 
from data_handler import MODELS
from data_handler import DEBUG
from data_handler import DATES

from tabs.forecast import tab_forecast
from tabs.forecast import sidebar_forecast
from tabs.forecast_callbacks import register_callbacks as fcst_callbacks
from tabs.evaluation import tab_evaluation
from tabs.evaluation import sidebar_evaluation
from tabs.evaluation_callbacks import register_callbacks as eval_callbacks
from tabs.observations import tab_observations
from tabs.observations import sidebar_observations
from tabs.observations_callbacks import register_callbacks as obs_callbacks

import socket

HOSTNAME = socket.gethostbyaddr(socket.gethostname())[0]

TIMEOUT = 10


fontawesome = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/4.7.0/css/font-awesome.min.css'

srv = flask.Flask(__name__)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP,
                                                dbc.themes.GRID,
                                                fontawesome
                                                ],
                url_base_pathname='/daily_dashboard/',
                server=srv)
app.css.config.serve_locally = True
app.scripts.config.serve_locally = True
app.config.update({
    # as the proxy server will remove the prefix
    'routes_pathname_prefix': '/',

    # the front-end will prefix this string to the requests
    # that are made to the proxy server
    'requests_pathname_prefix': '/daily_dashboard/'
})
app.config.suppress_callback_exceptions = True
server = app.server

cache_dir = "/dev/shm"
Path(cache_dir).mkdir(parents=True, exist_ok=True)

cache_config = {
    "DEBUG": True,
    # "CACHE_TYPE": "FileSystemCache",
    "CACHE_TYPE": "FileSystemCache",
    "CACHE_DIR": cache_dir,
}

cache = Cache(server, config=cache_config)
cache_timeout = 1

try:
    cache.clear()
except:
    pass

if DEBUG: print('SERVER: start creating app layout')
app.layout = html.Div(
    children=[
        html.Div(
            id='app-sidebar',
            children=[],
            className='sidebar'
        ),
        dcc.Tabs(id='app-tabs', value='forecast-tab', children=[
            tab_forecast(),
            tab_evaluation(),
            tab_observations(),
        ]),
    ],
    className="content",
)

if DEBUG: print('SERVER: stop creating app layout')


@app.callback(
    Output('app-sidebar', 'children'),
    [Input('app-tabs', 'value')],
)
def render_sidebar(tab):
    """ Function rendering requested tab """
    tabs = {
        'forecast-tab' : [
            sidebar_forecast,
            (VARS, DEFAULT_VAR, MODELS, DEFAULT_MODEL)
            ],
        'evaluation-tab' : [
            sidebar_evaluation,
            None
            ],
        'observations-tab' : [
            sidebar_observations,
            None
            ]
    }

    if tabs[tab][1] is None:
        return tabs[tab][0]()

    return tabs[tab][0](*tabs[tab][1])


fcst_callbacks(app, cache, cache_timeout)
eval_callbacks(app)
obs_callbacks(app)


if __name__ == '__main__':
    app.run_server(debug=True, processes=4, threaded=False,
                   host=HOSTNAME, port=7777)

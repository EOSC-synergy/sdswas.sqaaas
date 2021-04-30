#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Dash Server """

# import debug
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output
from dash.dependencies import Input
from dash.dependencies import State
from dash.dependencies import ALL
from dash.dependencies import MATCH
from dash.exceptions import PreventUpdate
import flask
from flask_caching import Cache

from data_handler import DEFAULT_VAR
from data_handler import DEFAULT_MODEL
from data_handler import VARS 
from data_handler import MODELS
from data_handler import DEBUG

import tabs
from tabs.forecast import tab_forecast
from tabs.forecast import sidebar_forecast
from tabs.forecast_callbacks import register_callbacks as fcst_callbacks
from tabs.evaluation import tab_evaluation
from tabs.evaluation import sidebar_evaluation
from tabs.evaluation_callbacks import register_callbacks as eval_callbacks
from tabs.observations import tab_observations
from tabs.observations import sidebar_observations


TIMEOUT = 10


srv = flask.Flask(__name__)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP,
                                                dbc.themes.GRID],
                server=srv)
app.css.config.serve_locally = True
app.scripts.config.serve_locally = True
server = app.server

app.config.suppress_callback_exceptions = True

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
            tab_observations,
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


fcst_callbacks(app)
eval_callbacks(app)


if __name__ == '__main__':
    import socket
    hostname = socket.gethostbyaddr(socket.gethostname())[0]
    app.run_server(debug=True, processes=4, threaded=False,
                   host=hostname, port=7777)

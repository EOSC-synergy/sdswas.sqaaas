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
import flask
from flask_caching import Cache

from data_handler import DEFAULT_VAR
from data_handler import DEFAULT_MODEL
from data_handler import STYLES
from data_handler import FREQ
from data_handler import DEBUG

from tools import get_eval_timeseries
from tools import get_timeseries
from tools import get_figure
from tools import get_obs1d
from tools import calc_matrix

import tabs
from tabs import start_date
from tabs import end_date

from datetime import datetime as dt
import math


TIMEOUT = 10


srv = flask.Flask(__name__)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP,
                                                dbc.themes.GRID],
#                url_base_pathname='/dash/',
                server=srv)
app.css.config.serve_locally = True
app.scripts.config.serve_locally = True
app.config.update({
    # as the proxy server will remove the prefix
#    'routes_pathname_prefix': '/',

    # the front-end will prefix this string to the requests
    # that are made to the proxy server
#    'requests_pathname_prefix': '/dash/'
})
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
            dcc.Tab(label='Forecast',
                    value='forecast-tab',
                    className='horizontal-menu',
                    children=[
                        dbc.Container(
                            id='graph-collection',
                            children=[],
                            fluid=True,
                        ),
                        dcc.Interval(id='slider-interval',
                                        interval=2000,
                                        n_intervals=0,
                                        disabled=True),
                        tabs.time_slider,
                        tabs.time_series,
                        ]
                    ),
            dcc.Tab(label='Evaluation',
                    value='evaluation-tab',
                    className='horizontal-menu',
                    children=[
                        html.Span(
                            dcc.DatePickerRange(
                                id='eval-date-picker',
                                min_date_allowed=dt.strptime(start_date, "%Y%m%d"),
                                max_date_allowed=dt.strptime(end_date, "%Y%m%d"),
                                initial_visible_month=dt.strptime(end_date, "%Y%m%d"),
                                display_format='DD MMM YYYY',
                                end_date=end_date,
                            ),
                            className="linetool",
                        ),
                        html.Span(
                            dcc.Dropdown(
                                id='obs-dropdown',
                                options=[{'label': 'Aeronet v3 lev15',
                                        'value': 'aeronet'}],
                                placeholder='Select observation network',
                                # clearable=False,
                                searchable=False
                            ),
                            className="linetool",
                        ),
                        html.Div(
                            dcc.Graph(
                                id='graph-eval',
                                figure=get_figure(),
                            ),
                        ),
                        tabs.eval_time_series,
                    ]),
            dcc.Tab(label='Observations',
                    className='horizontal-menu',
                    children=[]),
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
    if tab == 'evaluation-tab':
        return tabs.sidebar_evaluation

    return tabs.sidebar_forecast


@app.callback(
    Output({'type': 'graph-with-slider', 'index': MATCH}, 'figure'),
    [Input(style, 'n_clicks') for style in STYLES],
    [State({'type': 'graph-with-slider', 'index': MATCH}, 'figure')]
)
def update_layout(*args):
    ctx = dash.callback_context
    figures = args[-1]

    if ctx.triggered:
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        figures['layout']['mapbox']['style'] = button_id
    else:
        figures['layout']['mapbox']['style'] = 'carto-positron'
    return figures


# retrieve timeseries according to coordinates selected
@app.callback(
    [Output('ts-modal', 'children'),
     Output('ts-modal', 'is_open')],
    [Input('model-date-picker', 'date'),
     Input({'type': 'graph-with-slider', 'index': ALL}, 'clickData'),
     Input({'type': 'graph-with-slider', 'index': ALL}, 'id')],
    [State('model-dropdown', 'value'),
     State('variable-dropdown-forecast', 'value')],
)
def show_timeseries(date, cdata, element, model, variable):
    lat = lon = None
    for click, elem in zip(cdata, element):
        if elem['index'] in model and click:
            lat = click['points'][0]['lat']
            lon = click['points'][0]['lon']
            break

    if DEBUG: print('"""""', model)
    if lat and lon:
        return dbc.ModalBody(
            dcc.Graph(
                id='timeseries-modal',
                figure=get_timeseries(model, date, variable, lat, lon),
            )
        ), True

    return dbc.ModalBody(
        dcc.Graph(
            id='timeseries-modal',
            figure={},
        )
    ), False


# start/stop animation
@app.callback(
    [Output('slider-interval', 'disabled'),
     Output('slider-interval', 'n_intervals')],
    [Input('btn-play', 'n_clicks')],
    [State('slider-interval', 'disabled'),
     State('slider-graph', 'value')])
def start_stop_autoslider(n, disabled, value):
    if DEBUG: print("VALUE", value)
    if not value:
        value = 0
    if n:
        return not disabled, int(value/FREQ)
    return disabled, int(value/FREQ)


# update slider value according to the number of intervals
@app.callback(
    Output('slider-graph', 'value'),
    [Input('slider-interval', 'n_intervals')])
def update_slider(n):
    if DEBUG: print('SERVER: updating slider-graph ' + str(n))
    if not n:
        return

    if n >= 24:
        tstep = int(round(24*math.modf(n/24)[0], 0))
    else:
        tstep = int(n)
    if DEBUG: print('SERVER: updating slider-graph ' + str(tstep*FREQ))
    return tstep*FREQ


# update forecast figure according to all parameters
@app.callback(
    Output('graph-collection', 'children'),
    [Input('model-date-picker', 'date'),
     Input('model-dropdown', 'value'),
     Input('variable-dropdown-forecast', 'value'),
     Input('slider-graph', 'value')],
    [State('slider-interval', 'disabled')])
def update_figure(date, model, variable, tstep, static):
    if DEBUG: print('SERVER: calling figure from picker callback')
    # if DEBUG: print('SERVER: interval ' + str(n))
    if DEBUG: print('SERVER: tstep ' + str(tstep))

    if date is not None:
        date = date.split(' ')[0]
        try:
            date = dt.strptime(
                date, "%Y-%m-%d").strftime("%Y%m%d")
        except:
            pass
        if DEBUG: print('SERVER: callback date {}'.format(date))
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

    if DEBUG: print('SERVER: tstep calc ' + str(tstep))

    figures = []
    if not model:
        fig = get_figure(model, variable, date, tstep, static)
        figures.append(
            dbc.Row([
                dbc.Col([
                    dcc.Graph(
                        id={
                            'type': 'graph-with-slider',
                            'index': 'none',
                        },
                        figure=fig,
                    )
                ])
            ])
        )
        return figures

    idx = 0
    ncols, nrows = calc_matrix(len(model))
    for mod in model:
        figures.append(
            dcc.Graph(
                id={
                    'type': 'graph-with-slider',
                    'index': mod,
                },
                figure=get_figure(mod, variable, date, tstep,
                                  static, (nrows, ncols)),
                style={'height': '{}vh'.format(int(85/nrows))},
            )
        )
        idx += 1

    res = [
        dbc.Row(
            [
                dbc.Col(figures[row+col+(row*(ncols-1))],
                        width=int(12/ncols),
                        )
                for col in range(ncols)
                if len(figures) > row+col+(row*(ncols-1))
            ],
            align="start",
            no_gutters=True,
        ) for row in range(nrows)
    ]
    if DEBUG: print(ncols, nrows, len(res), [(type(i), len(i.children)) for i in res])
    return res


# retrieve evaluation timeseries according to station selected
@app.callback(
    [Output('ts-eval-modal', 'children'),
     Output('ts-eval-modal', 'is_open')],
    [Input('eval-date-picker', 'start_date'),
     Input('eval-date-picker', 'end_date'),
     Input('obs-dropdown', 'value'),
     Input('graph-eval', 'clickData'),
     Input('graph-eval', 'id')],
)
def show_eval_timeseries(start_date, end_date, obs, cdata, element):
    print(start_date, end_date, obs, cdata, element)
    lat = lon = None
    if cdata:
#         lat = click['points'][0]['lat']
#         lon = click['points'][0]['lon']
        idx = cdata['points'][0]['pointIndex']
        if idx != 0:
            name = cdata['points'][0]['customdata']

            if DEBUG: print('"""""', obs)
            return dbc.ModalBody(
                dcc.Graph(
                    id='timeseries-eval-modal',
                    figure=get_eval_timeseries(obs, start_date, end_date, DEFAULT_VAR, idx-1, name),
                )
            ), True

    return dbc.ModalBody(
        dcc.Graph(
            id='timeseries-eval-modal',
            figure={},
        )
    ), False


# update evaluation figure according to all parameters
@app.callback(
    Output('graph-eval', 'figure'),
    [Input('eval-date-picker', 'start_date'),
     Input('eval-date-picker', 'end_date'),
     Input('obs-dropdown', 'value')],
    [State('graph-eval', 'relayoutData')])
def update_eval(sdate, edate, obs, relayoutdata):
    if DEBUG: print('SERVER: calling figure from EVAL picker callback')
    # if DEBUG: print('SERVER: interval ' + str(n))

    if sdate is not None:
        sdate = sdate.split()[0]
        try:
            sdate = dt.strptime(
                sdate, "%Y-%m-%d").strftime("%Y%m%d")
        except:
            pass
        if DEBUG: print('SERVER: callback start_date {}'.format(sdate))
    else:
        sdate = end_date

    if edate is not None:
        edate = edate.split()[0]
        try:
            edate = dt.strptime(
                edate, "%Y-%m-%d").strftime("%Y%m%d")
        except:
            pass
        if DEBUG: print('SERVER: callback end_date {}'.format(edate))
    else:
        edate = end_date
    fig = get_figure(model=None, var=DEFAULT_VAR)  # , selected_date=date)

    if fig:
        if obs:
            fig.add_trace(get_obs1d(sdate, edate, obs, DEFAULT_VAR))

        if relayoutdata:
            relayoutdata = {k: relayoutdata[k]
                            for k in relayoutdata
                            if k not in ('mapbox._derived',)}
            fig.layout.update(relayoutdata)

    return fig


# Dash CSS
# app.css.append_css({"external_url": '{}/css/bWLwgP.css'.format(os.getcwd())})

# Loading screen CSS
# app.css.append_css({"external_url":
# "https://codepen.io/chriddyp/pen/brPBPO.css"})


if __name__ == '__main__':
    import socket
    hostname = socket.gethostbyaddr(socket.gethostname())[0]
    app.run_server(debug=True, processes=4, threaded=False,
                   host=hostname, port=7777)

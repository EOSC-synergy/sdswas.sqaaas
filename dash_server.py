#!/usr/bin/env python
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

from data_handler import FigureHandler
from data_handler import TimeSeriesHandler
from data_handler import DEFAULT_VAR
from data_handler import DEFAULT_MODEL
from data_handler import STYLES
from data_handler import FREQ
from data_handler import DEBUG
from data_handler import Observations1dHandler

from datetime import datetime as dt
import math

import tabs
from tabs import start_date
from tabs import end_date


def calc_matrix(n):
    sqrt_n = math.sqrt(n)
    ncols = sqrt_n == int(sqrt_n) and int(sqrt_n) or int(sqrt_n) + 1
    nrows = n%ncols > 0 and int(n/ncols)+1 or int(n/ncols)
    return ncols, nrows


def get_timeseries(model, var, lat, lon):
    """ Retrieve timeseries """
    # if DEBUG: print(var, selected_date, tstep)
    if DEBUG: print('SERVER: TS init for models {} ... '.format(str(model)))
    th = TimeSeriesHandler(model, var)
    if DEBUG: print('SERVER: TS generation ... ')
    return th.retrieve_timeseries(lat, lon)


def get_figure(model=None, var=None, selected_date=end_date, tstep=0,
               static=True, aspect=(1, 1)):
    """ Retrieve figure """
    # if DEBUG: print(var, selected_date, tstep)
    try:
        selected_date = dt.strptime(
            selected_date, "%Y-%m-%d %H:%M:%S").strftime("%Y%m%d")
    except:
        pass
    if model:
        if DEBUG: print('SERVER: Figure init ... ')
        fh = FigureHandler(model, selected_date)
        if DEBUG: print('SERVER: Figure generation ... ')
        return fh.retrieve_var_tstep(var, tstep, static, aspect)
    if DEBUG: print('SERVER: No Figure')
    return FigureHandler().retrieve_var_tstep()


srv = flask.Flask(__name__)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP,
                                                dbc.themes.GRID],
                server=srv)
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
                                        interval=1000,
                                        n_intervals=0,
                                        disabled=True),
                        tabs.time_slider,
                        # tabs.progress_bar,
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
                    ]),
            dcc.Tab(label='Observations',
                    className='horizontal-menu',
                    children=[]),
        ]),
    ],
    className="content",
)

if DEBUG: print('SERVER: stop creating app layout')


# @app.callback(
#     [Output("progress", "value"),
#      Output("progress", "children"),
#      Output("progress-interval", "disabled"),
#      Output("progress-modal", "is_open")],
#     [Input("progress-interval", "n_intervals"),
#      Input({'type': 'graph-with-slider', 'index': ALL}, 'clickData')],
#     [State('progress-interval', 'disabled')],
# )
# def update_progress(n, cdata, disabled):
#
#     if cdata and disabled:
#         # check progress of some background process, in this
#         # example we'll just
#         # use n_intervals constrained to be in 0-100
#         progress = min(n % 110, 100)
#         # only add text after 5% progress to ensure text isn't
#         # squashed too much
#         return progress, \
#             "{progress} %" if progress >= 5 else "", \
#             False, True
#
#     return "", "", True, False


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
    [ # Output('progress-modal', 'is_open'),
     Output('ts-modal', 'children'),
     Output('ts-modal', 'is_open')],
    [Input({'type': 'graph-with-slider', 'index': ALL}, 'clickData'),
     Input({'type': 'graph-with-slider', 'index': ALL}, 'id')],
    [State('model-dropdown', 'value'),
     State('variable-dropdown-forecast', 'value')],
)
def show_timeseries(cdata, element, model, variable):
    lat = lon = None
    for click, elem in zip(cdata, element):
        if elem['index'] in model and click:
            lat = click['points'][0]['lat']
            lon = click['points'][0]['lon']
            break

    if DEBUG: print('"""""', model)
    if lat and lon:
        return dbc.ModalBody(
            dcc.Loading(
                dcc.Graph(
                    id='timeseries-modal',
                    figure=get_timeseries(model, variable, lat, lon),
                )
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
                    ),
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


# update evaluation figure according to all parameters
@app.callback(
    Output('graph-eval', 'figure'),
    [Input('eval-date-picker', 'date'),
     Input('obs-dropdown', 'value')],
    [State('graph-eval', 'relayoutData')])
def update_eval(date, obs, relayoutdata):
    if DEBUG: print('SERVER: calling figure from EVAL picker callback')
    # if DEBUG: print('SERVER: interval ' + str(n))

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

    fig = get_figure(model=None, var=DEFAULT_VAR, selected_date=date)

    if fig:
        if obs:
            obs_handler = Observations1dHandler('./data/obs/aeronet/netcdf/od550aero_202004.nc', date)
            obs_trace = obs_handler.generate_obs1d_tstep_trace(DEFAULT_VAR)
            fig.add_trace(obs_trace)

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
    app.run_server(debug=False, processes=4, threaded=False,
                   host='localhost', port=9999)

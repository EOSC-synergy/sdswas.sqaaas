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
    # print(var, selected_date, tstep)
    print('SERVER: TS init ... ')
    th = TimeSeriesHandler(model, var)
    print('SERVER: TS generation ... ')
    return th.retrieve_timeseries(lat, lon)


def get_figure(model=None, var=None, selected_date=end_date, tstep=0, static=True):
    """ Retrieve figure """
    # print(var, selected_date, tstep)
    try:
        selected_date = dt.strptime(
            selected_date, "%Y-%m-%d %H:%M:%S").strftime("%Y%m%d")
    except:
        pass
    if model:
        print('SERVER: Figure init ... ')
        fh = FigureHandler(model, selected_date)
        print('SERVER: Figure generation ... ')
        return fh.retrieve_var_tstep(var, tstep, static)
    print('SERVER: No Figure')
    return FigureHandler().retrieve_var_tstep()


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.themes.GRID])
# server = app.server
# app.config.suppress_callback_exceptions = True

print('SERVER: start creating app layout')
app.layout = html.Div(
    children=[
        tabs.sidebar_forecast,
        dcc.Tabs(children=[
            dcc.Tab(label='Forecast',
                    className='horizontal-menu',
                    children=[
                        dbc.Container(
                            id='graph-collection',
                            children=[
                            dbc.Row([
                                dbc.Col([
                                        dcc.Loading([
                                            html.Div(
                                                id='graph-container-0',
                                                children=[
                                                    dcc.Graph(
                                                        id='graph-with-slider-0',
                                                        figure=get_figure(DEFAULT_MODEL,
                                                                        DEFAULT_VAR, end_date, 0),
                                                    )],
                                                # className="graph-model",
        #                                         style={'display': 'table-cell',
        #                                             'float': 'left',
        #                                             'width': '100%',
        #                                             'height': '100%',
        #                                             },
                                            )],
                                            type="circle",)
                                            ]
                                        ),
                                    ],
                                    no_gutters=True,
                                ),
                            ],
                            fluid=True,
                            style={"height": "100vh"},
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
                    className='horizontal-menu',
                    children=[
                        html.Span(
                            dcc.DatePickerSingle(
                                id='eval-date-picker',
                                min_date_allowed=dt.strptime(start_date, "%Y%m%d"),
                                max_date_allowed=dt.strptime(end_date, "%Y%m%d"),
                                initial_visible_month=dt.strptime(end_date, "%Y%m%d"),
                                display_format='DD MMM YYYY',
                                date=end_date,
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

print('SERVER: stop creating app layout')


# retrieve timeseries according to coordinates selected
@app.callback(
    [Output('timeseries-modal', 'figure'),
     Output("ts-modal", "is_open")],
    [Input('graph-with-slider-0', 'clickData')],
    [State('graph-with-slider-0', 'hoverData'),
     State('model-dropdown', 'value'),
     State('variable-dropdown', 'value')],
)
def show_timeseries(cdata, hdata, model, variable):
    if hdata:
        lat = hdata['points'][0]['lat']
        lon = hdata['points'][0]['lon']
        return get_timeseries(model, variable, lat, lon), True

    return None, False


# start/stop animation
@app.callback([
    Output('slider-interval', 'disabled'),
    Output('slider-interval', 'n_intervals')],
    [Input('btn-play', 'n_clicks')],
    [State('slider-interval', 'disabled'),
     State('slider-graph', 'value')])
def start_stop_autoslider(n, disabled, value):
    print("VALUE", value)
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
    print('SERVER: updating slider-graph ' + str(n))
    if not n:
        return

    if n >= 24:
        tstep = int(round(24*math.modf(n/24)[0], 0))
    else:
        tstep = int(n)
    print('SERVER: updating slider-graph ' + str(tstep*FREQ))
    return tstep*FREQ


# update forecast figure according to all parameters
@app.callback(
    Output('graph-collection', 'children'),
    [Input('model-date-picker', 'date'),
     Input('model-dropdown', 'value'),
     Input('variable-dropdown', 'value'),
     Input('slider-graph', 'value')],
    [State('graph-with-slider-0', 'relayoutData'),
     State('slider-interval', 'disabled')])
def update_figure(date, model, variable, tstep, relayoutdata, static):
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

    figures = []
    if not model:
        fig = get_figure(model, variable, date, tstep, static)
        figures.append(
            dbc.Row([
                dbc.Col([
                    dcc.Loading([
                        html.Div(
                            id='graph-container-0',
                            children=[
                                dcc.Graph(
                                    id='graph-with-slider-0',
                                    figure=fig,
                                    # className="graph-model",
                    #                 style={'display': 'table-cell',
                    #                        'width': '100%',
                    #                        'height': '100%',
                    #                        },
                                )
                            ]
                        )
                    ],
                        type="circle",
                    )
                ])
            ])
        )
        return figures

    idx = 0
    ncols, nrows = calc_matrix(len(model))
    for mod in model:
        fig = get_figure(mod, variable, date, tstep, static)

        if fig and relayoutdata:
            relayoutdata = {k: relayoutdata[k]
                            for k in relayoutdata
                            if k not in ('mapbox._derived',)}
            fig.layout.update(relayoutdata)

        figures.append(
            dcc.Loading([
                html.Div(
                    id='graph-container-{}'.format(idx),
                    children=[
                        dcc.Graph(
                            id='graph-with-slider-{}'.format(idx),
                            figure=fig,
                        )],
                    # className="graph-model",
#                     style={ #'display': 'table-cell',
#                          'width': 'calc(100%/{}) !important'.format(ncols),
#                          'height': 'calc(100%/{}) !important'.format(nrows),
#                          },
            )],
            type="circle",
            )
        )
        idx += 1

    res = [
        dbc.Row(
            [
                dbc.Col(figures[row+col+(row*(ncols-1))], width=int(12/ncols))
                for col in range(ncols)
                if len(figures) > row+col+(row*(ncols-1))
            ],
            # align="center",
            no_gutters=True,
            className="h-{}".format(int(100/nrows)),
        ) for row in range(nrows)
    ]
    print(ncols, nrows, len(res), [(type(i), len(i.children)) for i in res])
    return res


# update evaluation figure according to all parameters
@app.callback(
    Output('graph-eval', 'figure'),
    [Input('eval-date-picker', 'date'),
     Input('obs-dropdown', 'value')],
    [State('graph-eval', 'relayoutData')])
def update_eval(date, obs, relayoutdata):
    print('SERVER: calling figure from EVAL picker callback')
    # print('SERVER: interval ' + str(n))

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
# app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/brPBPO.css"})


if __name__ == '__main__':
    app.run_server(debug=True, processes=8, threaded=False, host='localhost', port=9999)

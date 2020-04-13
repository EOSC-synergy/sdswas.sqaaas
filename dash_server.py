#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Dash Server """

import debug
import dash
# import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output
from dash.dependencies import Input
from dash.dependencies import State

from data_handler import FigureHandler
from data_handler import DEFAULT_VAR

from datetime import datetime as dt
import math
# import os

colors = {
    'background': '#ffffff',
    # 'text': '#7FDBFF'
}

start_date = "20190701"
end_date = "20190710"

F_PATH = './data/netcdf/{}12_3H_NMMB-BSC_OPER.nc4'


def get_figure(var, selected_date=end_date, tstep=0):
    """ Retrieve figure """
    # print(var, selected_date, tstep)
    try:
        selected_date = dt.strptime(
            selected_date, "%Y-%m-%d %H:%M:%S").strftime("%Y%m%d")
    except:
        pass
    print('SERVER: Figure init ... ')
    fh = FigureHandler(F_PATH.format(selected_date), selected_date)
    print('SERVER: Figure generation ... ')
    return fh.retrieve_var_tstep(var, tstep)


app = dash.Dash(__name__)
# server = app.server
# app.config.suppress_callback_exceptions = True

print('SERVER: start creating app layout')
app.layout = html.Div(
    style={
        'backgroundColor': colors['background'],
        # 'textAlign': 'center',
        # 'margin': 0,
        # 'padding': '10px',
    },
    children=[
        html.Div([
        html.Span(
            dcc.Dropdown(
                id='variable-dropdown',
                options=[
                    {
                        'label': 'Dust Optical Depth (550nm)',
                        'value': 'od550_dust'
                    },
                    {
                        'label': 'Dust Surface Concentration',
                        'value': 'sconc_dust'
                    },
                ],
                value='od550_dust'
            ),
            className="linetool",
            style={
                'display': 'table-cell',
                'width': '25%',
                'padding-left': '1em',
                'padding-right': '1em',
            }
        ),
        html.Span(
            dcc.DatePickerSingle(
                id='model-date-picker',
                min_date_allowed=dt.strptime(start_date, "%Y%m%d"),
                max_date_allowed=dt.strptime(end_date, "%Y%m%d"),
                initial_visible_month=dt.strptime(end_date, "%Y%m%d"),
                display_format='YYYY/MM/DD',
                date=end_date,
            ),
            className="linetool",
            style={
                'display': 'table-cell'
            }
        ),
        html.Span(
            html.Button('\u2023', title='Play/Stop', id='btn-play', n_clicks=0),
            className="linetool",
            style={
                'display': 'table-cell',
                'padding-left': '1em',
            }
        ),
        html.Span(
            dcc.Slider(
                id='slider-graph',
                min=0, max=72, step=3, value=0,
                marks={
                    tstep: '{:02d}'.format(tstep)
                    for tstep in range(0, 75, 3)
                },
                # updatemode='drag',
            ),
            className="linetool",
            style={
                'display': 'table-cell',
                'width': '60%',
                'vertical-align': 'bottom'
            }
        )],
        className="toolbar",
        style={
            'display': 'table-row',
            'width': '100%'
        }
        ),
        html.Div(
            dcc.Graph(
                id='graph-with-slider',
                figure=get_figure(DEFAULT_VAR, end_date, 0),
            ),
        ),
        dcc.Interval(id='slider-interval', interval=3000, n_intervals=0, disabled=True),
    ],
)
print('SERVER: stop creating app layout')


@app.callback([
    Output('slider-interval', 'disabled'),
    Output('slider-interval', 'n_intervals')],
    [Input('btn-play', 'n_clicks')],
    [State('slider-interval', 'disabled'),
     State('slider-graph', 'value')])
def start_stop_autoslider(n, disabled, value):
    if n:
        return not disabled, int(value/3)
    return disabled, int(value/3)


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
    print('SERVER: updating slider-graph ' + str(tstep*3))
    return tstep*3


@app.callback(
    Output('graph-with-slider', 'figure'),
    [Input('model-date-picker', 'date'),
     Input('variable-dropdown', 'value'),
     Input('slider-graph', 'value')])
def update_figure(date, variable, tstep):
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

    if variable is not None:
        variable = variable
    else:
        variable = DEFAULT_VAR

    if tstep is not None:
        tstep = int(tstep/3)
    else:
        tstep = 0

    print('SERVER: tstep calc ' + str(tstep))
    return get_figure(variable, date, tstep)


# Dash CSS
# app.css.append_css({"external_url": '{}/css/bWLwgP.css'.format(os.getcwd())})

# Loading screen CSS
# app.css.append_css({"external_url": "https://codepen.io/chriddyp/pen/brPBPO.css"})


if __name__ == '__main__':
    app.run_server(debug=True, processes=8, threaded=False, port=9999)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Dash Server """

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from datetime import datetime as dt
from data_handler import FigureHandler
from data_handler import VARS
from data_handler import DEFAULT_VAR


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}

start_date = "20190723"
end_date = "20190724"

F_PATH = \
    '/esarchive/scratch/Earth/fbeninca/plotly_test/encomienda/{}12_3H_NMMB-BSC_OPER.nc'.format(end_date)

FH = FigureHandler(F_PATH)
#VARLIST = FH.varlist

def get_figure(var, tstep=0):
    figure = FH.retrieve_var_tstep(var, tstep)
    figure['layout']['plot_bgcolor'] = colors['background']
    figure['layout']['paper_bgcolor'] = colors['background']
    figure['layout']['font'] = {'color': colors['text']}
    return figure


app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(
    style={
        'backgroundColor': colors['background'],
        'textAlign': 'center',
        'margin': 0,
        'padding': '10px',
        },
    children=[

#        html.H2(children='Dust Forecast Dashboard',
#            style={
#                'textAlign': 'center',
#                'color': colors['text']
#            }
#        ),

        html.Div(
            dcc.Graph(
                id='graph-with-slider',
                figure=get_figure(DEFAULT_VAR, tstep=0),
#                animate=True,
            ),
        ),
#        html.Div(
#            dcc.Slider(
#                id='timestep-slider',
#                min=0,
#                max=72,
#                marks={str(i): 'H+{}'.format(i) for i in range(0,75,3)},
#                value=0,
#            ),
#            style={'width': '50%',
#                   'padding': '20px',
#                   'margin-bottom': '0px',
#                   'margin-left': '50px'},
#        ),
#    html.Div(
#        dcc.Interval(
#            id='interval-component',
#            interval=.5*1000,
#            n_intervals=0,
#        ),
#    ),
        html.Div(
#            dcc.Input(id='input-variable', type='text', value=DEFAULT_VAR)),
            #[html.Button(VARS[varname]['name'], id='button_'+varname) for varname in VARS],
#        html.Div(
#            dcc.DatePickerSingle(
#                id='model-date-picker',
#                min_date_allowed=dt.strptime(start_date, "%Y%m%d"),
#                max_date_allowed=dt.strptime(end_date, "%Y%m%d"),
#                initial_visible_month=dt.strptime(end_date, "%Y%m%d"),
#                date=str(dt.strptime(end_date, "%Y%m%d")),
#            ),
        ),
    ],
)

#@app.callback(
#    Output('graph-with-slider', 'figure'),
#    [Input('button_'+varname, 'value') for varname in VARS]
#)
#
#@app.callback(
#    Output('graph-with-slider', 'figure'),
#    [Input('timestep-slider', 'value'),]
#)
#def update_figure(tvalue):
#    print("UPDATE", tvalue)
##    return get_figure(DEFAULT_VAR, int(tvalue)/3)

#@app.callback(
##    Output('graph-with-slider', 'figure'),
#    [Input('interval-component', 'n_intervals'),]
#)
#def auto_update_figure(tstep):
#    return get_figure(int(tstep)%25)

if __name__ == '__main__':
    app.run_server(debug=True)

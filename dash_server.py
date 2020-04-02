#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Dash Server """

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Output
from dash.dependencies import Input

# from dash.dependencies import Input, Output
from data_handler import FigureHandler
from data_handler import DEFAULT_VAR

from datetime import datetime as dt
# import os

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
# external_stylesheets = ['{}/css/dZVMbK.css'.format(os.getcwd())]
print(external_stylesheets)

# colors = {
#     'background': '#111111',
#     'text': '#7FDBFF'
# }

start_date = "20190701"
end_date = "20190710"

F_PATH = './data/netcdf/{}12_3H_NMMB-BSC_OPER.nc4'


def get_figure(var, selected_date=end_date, tstep=0):
    """ Retrieve figure """
    try:
        selected_date = dt.strptime(
            selected_date, "%Y-%m-%d").strftime("%Y%m%d")
    except:
        pass
    fh = FigureHandler(F_PATH.format(selected_date), selected_date)
    return fh.retrieve_var_tstep(var, tstep)


app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
# server = app.server
app.config.suppress_callback_exceptions = True

app.layout = html.Div(
    style={
        # 'backgroundColor': colors['background'],
        'textAlign': 'center',
        'margin': 0,
        'padding': '10px',
    },
    children=[
        html.Div(
            dcc.DatePickerSingle(
                id='model-date-picker',
                min_date_allowed=dt.strptime(start_date, "%Y%m%d"),
                max_date_allowed=dt.strptime(end_date, "%Y%m%d"),
                initial_visible_month=dt.strptime(end_date, "%Y%m%d"),
                date=str(dt.strptime(end_date, "%Y%m%d"))
            ),

            dcc.Graph(
                id='graph-with-slider',
                figure=get_figure(DEFAULT_VAR, end_date, tstep=0),
            ),
        ),
    ],
)


@app.callback(
    Output('graph-with-slider', 'figure'),
    [Input('model-date-picker', 'date')])
def update_figure(date):
    if date is not None:
        date = dt.strptime(date.split(' ')[0], '%Y-%m-%d')
        return get_figure(DEFAULT_VAR, date, tstep=0)


if __name__ == '__main__':
    app.run_server(debug=False, processes=8, threaded=False, port=9999)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Dash Server """

import dash
import dash_core_components as dcc
import dash_html_components as html
# from dash.dependencies import Input, Output
from data_handler import FigureHandler
from data_handler import DEFAULT_VAR

import os

# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
external_stylesheets = ['{}/css/dZVMbK.css'.format(os.getcwd())]
print(external_stylesheets)

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}

start_date = "20190701"
end_date = "20190710"

F_PATH = './data/netcdf/{}12_3H_NMMB-BSC_OPER.nc4'.format(end_date)

FH = FigureHandler(F_PATH)


def get_figure(var, tstep=0):
    """ Retrieve figure """
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
        html.Div(
            dcc.Graph(
                id='graph-with-slider',
                figure=get_figure(DEFAULT_VAR, tstep=0),
            ),
        ),
    ],
)


if __name__ == '__main__':
    app.run_server(debug=True, processes=8, threaded=False, port=9999)

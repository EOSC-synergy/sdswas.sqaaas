# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from test_code import FigureHandler

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}

F_PATH = \
    '/esarchive/scratch/Earth/fbeninca/plotly_test/encomienda/2019040712_3H_NMMB-BSC.nc'

FH = FigureHandler(F_PATH)
#VARLIST = FH.varlist

def get_figure(tstep=0):
    figure = FH.run_plot(tstep)
    figure['layout']['plot_bgcolor'] = colors['background']
    figure['layout']['paper_bgcolor'] = colors['background']
    figure['layout']['font'] = {'color': colors['text']}
    return figure

app = dash.Dash()

app.layout = html.Div(
    style={
        'backgroundColor': colors['background'],
        'textAlign': 'center',
        'margin': 0,
        'padding': '10px',
        },
    children=[

        html.H1(children='Dust Forecast Dashboard',
            style={
                'textAlign': 'center',
                'color': colors['text']
              }
           ),

        html.Div(
            dcc.Graph(
                id='graph-with-slider',
                figure=get_figure(tstep=0),
                animate=True,
            ),
        ),
        html.Div(
            dcc.Slider(
                id='timestep-slider',
                min=0,
                max=72,
                marks={str(i): 'H+{}'.format(i) for i in range(0,75,3)},
                value=0,
            ),
            style={'width': '55%',
                   'padding': '0px 20px 20px 20px',
                   'margin-bottom': '0px' },
        ),
#    html.Div(
#        dcc.Interval(
#            id='interval-component',
#            interval=.5*1000,
#            n_intervals=0,
#        ),
#    ),
    ],
)

@app.callback(
    Output('graph-with-slider', 'figure'),
    [Input('timestep-slider', 'value'),]
)
def update_figure(tvalue):
    return get_figure(int(tvalue)/3)

#@app.callback(
#    Output('graph-with-slider', 'figure'),
#    [Input('interval-component', 'n_intervals'),]
#)
#def auto_update_figure(tstep):
#    return get_figure(int(tstep)%25)

if __name__ == '__main__':
    app.run_server(debug=True)

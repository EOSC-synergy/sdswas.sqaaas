""" TAB FORECAST """
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
from data_handler import DEFAULT_VAR
from data_handler import DEFAULT_MODEL
from data_handler import VARS 
from data_handler import MODELS
from data_handler import STYLES
from data_handler import FREQ
from data_handler import DEBUG
from data_handler import PROB 

from tools import get_eval_timeseries
from tools import get_timeseries
from tools import get_was_figure
from tools import get_prob_figure
from tools import get_figure
from tools import get_obs1d
from tools import start_date
from tools import end_date
from utils import calc_matrix
from utils import get_graph

from tabs.forecast import tab_forecast

from datetime import datetime as dt
import math


def register_callbacks(app):
    """ Registering callbacks """

    @app.callback(
        [Output('variable-dropdown-forecast', 'value'),
         Output('forecast-tab', 'children'),
         Output('collapse-1', 'is_open'),
         Output('collapse-2', 'is_open'),
         Output('collapse-3', 'is_open')],
        [Input('group-1-toggle', 'n_clicks'),
         Input('group-2-toggle', 'n_clicks'),
         Input('group-3-toggle', 'n_clicks')],
        [State('collapse-1', 'is_open'),
         State('collapse-2', 'is_open'),
         State('collapse-3', 'is_open'),
         State('variable-dropdown-forecast', 'value'),]
    )
    def render_forecast_tab(modbutton, probbutton, wasbutton, modopen, probopen, wasopen, var):
        """ Function rendering requested tab """
        ctx = dash.callback_context

        if not ctx.triggered:
            return False, False, False
        else:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if button_id == "group-1-toggle" and modbutton:
            return var, tab_forecast('models'), not modopen, False, False
        elif button_id == "group-2-toggle" and probbutton:
            return var, tab_forecast('prob'), False, not probopen, False
        elif button_id == "group-3-toggle" and wasbutton:
            return 'SCONC_DUST', tab_forecast('was'), False, False, not wasopen

        raise PreventUpdate


    @app.callback(
        Output('was-graph', 'children'),
        [Input('was-date-picker', 'date'),
         Input('was-slider-graph', 'value'),
         Input('was-dropdown', 'value'),],
    )
    def update_was_figure(date, day, was):
        """ Update Warning Advisory Systems maps """
        print('WAS', was)
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

        if was:
            was = was[0]
            return get_graph(index=was, figure=get_was_figure(was, day, selected_date=date))
        print("WAS figure " + date, was, day)
        return get_graph(index='none', figure=get_was_figure(selected_date=date))


    @app.callback(
        Output('prob-graph', 'children'),
        [Input('prob-date-picker', 'date'),
         Input('prob-slider-graph', 'value'),
         Input('variable-dropdown-forecast', 'value'),
         Input('prob-dropdown', 'value'),],
    )
    def update_prob_figure(date, day, var, prob):
        """ Update Warning Advisory Systems maps """
        print('PROB', date, day, var, prob)
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

        if prob:
            prob = prob.replace('prob_', '')
            return get_graph(index=prob, figure=get_prob_figure(var, prob, day, selected_date=date))
        print("PROB figure " + date, prob, day)
        return get_graph(index='none', figure=get_prob_figure(var, selected_date=date))


    @app.callback(
        [Output('prob-dropdown', 'options'),
         Output('prob-dropdown', 'value')],
        [Input('variable-dropdown-forecast', 'value')],
    )
    def update_prob_dropdown(var):
        """ Update Prob maps dropdown """
        opt_list = PROB[var]['prob_thresh']
        units = PROB[var]['units']
        return [{'label': '{} {}'.format(prob, units), 'value': 'prob_{}'.format(prob)} for prob in opt_list], 'prob_{}'.format(opt_list[0])


    @app.callback(
        Output({'type': 'graph-with-slider', 'index': MATCH}, 'figure'),
        [Input(style, 'n_clicks') for style in STYLES],
        [State({'type': 'graph-with-slider', 'index': MATCH}, 'figure')]
    )
    def update_layout(*args):
        """ Function updating map layout cartography """
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
        [Input('model-date-picker', 'date'),
         Input({'type': 'graph-with-slider', 'index': ALL}, 'clickData'),
         Input({'type': 'graph-with-slider', 'index': ALL}, 'id')],
        [State('model-dropdown', 'value'),
         State('variable-dropdown-forecast', 'value')],
    )
    def show_timeseries(date, cdata, element, model, variable):
        """ Renders model comparison timeseries """
        lat = lon = None
        for click, elem in zip(cdata, element):
            if elem['index'] in model and click:
                lat = click['points'][0]['lat']
                lon = click['points'][0]['lon']
                break

        if DEBUG: print('SHOW TS """""', model, lat, lon)
        if lat and lon:
            return dbc.ModalBody(
                dcc.Graph(
                    id='timeseries-modal',
                    figure=get_timeseries(model, date, variable, lat, lon),
                )
            ), True

        raise PreventUpdate


    # start/stop animation
    @app.callback(
        [Output('slider-interval', 'disabled'),
         Output('slider-interval', 'n_intervals')],
        [Input('btn-play', 'n_clicks')],
        [State('slider-interval', 'disabled'),
         State('slider-graph', 'value')])
    def start_stop_autoslider(n, disabled, value):
        """ Play/Pause map animation """
        if DEBUG: print("VALUE", value)
        if not value:
            value = 0
        if n:
            return not disabled, int(value/FREQ)
        return disabled, int(value/FREQ)


    @app.callback(
        Output('slider-graph', 'value'),
        [Input('slider-interval', 'n_intervals')])
    def update_slider(n):
        """ Update slider value according to the number of intervals """
        if DEBUG: print('SERVER: updating slider-graph ' + str(n))
        if not n:
            return
        if n >= 24:
            tstep = int(round(24*math.modf(n/24)[0], 0))
        else:
            tstep = int(n)
        if DEBUG: print('SERVER: updating slider-graph ' + str(tstep*FREQ))
        return tstep*FREQ


    @app.callback(
        Output('graph-collection', 'children'),
        [Input('model-date-picker', 'date'),
         Input('model-dropdown', 'value'),
         Input('variable-dropdown-forecast', 'value'),
         Input('slider-graph', 'value')],
        [State('graph-collection', 'children'),
         State('slider-interval', 'disabled')])
    def update_models_figure(date, model, variable, tstep, graphs, static):
        """ Update mosaic of maps figures according to all parameters """
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

        #if DEBUG and len(graphs) > 0: print('SERVER: graphs ' + str(graphs[0]['props']['children'][-1]['props']['children']['props'].keys()))

        figures = []
        if not model:
            fig = get_figure(model, variable, date, tstep, static)
            figures.append(
                dbc.Row([
                    dbc.Col([dbc.Spinner(
                        get_graph(index='none', figure=fig,
                            style={'height': '90vh'}
                            ))
                    ])
                ])
            )
            return figures

        ncols, nrows = calc_matrix(len(model))
        for idx, mod in enumerate(model):
            figures.append(
              dbc.Spinner(
                get_graph(
                    index=mod,
                    figure=get_figure(mod, variable, date, tstep,
                                      static, (nrows, ncols)),
                    style={'height': '{}vh'.format(int(90/nrows))}
                ))
            )

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

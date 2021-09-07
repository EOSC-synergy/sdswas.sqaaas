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
from data_handler import DATES
from data_handler import PROB 
from data_handler import MODEBAR_CONFIG_TS
from data_handler import MODEBAR_LAYOUT_TS
from utils import calc_matrix
from utils import get_graph
from tabs.forecast import tab_forecast

import pandas as pd
from datetime import datetime as dt
from io import BytesIO
from PIL import Image
import zipfile
import tempfile
import os.path
import math

start_date = DATES['start_date']
end_date = DATES['end_date']


def register_callbacks(app):
    """ Registering callbacks """

    @app.callback(
        [#Output('forecast-tab', 'children'),
         Output('collapse-1', 'is_open'),
         Output('collapse-2', 'is_open'),
         Output('collapse-3', 'is_open'),
         Output('group-2-toggle', 'disabled'),
         Output('group-3-toggle', 'disabled')],
        [Input('group-1-toggle', 'n_clicks'),
         Input('group-2-toggle', 'n_clicks'),
         Input('group-3-toggle', 'n_clicks'),
         Input('variable-dropdown-forecast', 'value')],
        [State('collapse-1', 'is_open'),
         State('collapse-2', 'is_open'),
         State('collapse-3', 'is_open'),]
    )
    def render_forecast_tab(modbutton, probbutton, wasbutton, var, modopen, probopen, wasopen):
        """ Function rendering requested tab """
        ctx = dash.callback_context

        if ctx.triggered:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]

            if button_id == "group-1-toggle" and modbutton:
                if modopen is True:
                    # return dash.no_update, not modopen, False, False, dash.no_update, dash.no_update
                    return not modopen, False, False, dash.no_update, dash.no_update
                # return tab_forecast('models'), not modopen, False, False, dash.no_update, dash.no_update
                return not modopen, False, False, dash.no_update, dash.no_update
            elif button_id == "group-2-toggle" and probbutton:
                if probopen is True:
                    # return dash.no_update, False, not probopen, False, dash.no_update, dash.no_update
                    return False, not probopen, False, dash.no_update, dash.no_update
                # return tab_forecast('prob'), False, not probopen, False, dash.no_update, dash.no_update
                return False, not probopen, False, dash.no_update, dash.no_update
            elif button_id == "group-3-toggle" and wasbutton:
                if wasopen is True:
                    # return dash.no_update, False, False, not wasopen, dash.no_update, dash.no_update
                    return False, False, not wasopen, dash.no_update, dash.no_update
                # return tab_forecast('was'), False, False, not wasopen, dash.no_update, dash.no_update
                return False, False, not wasopen, dash.no_update, dash.no_update

        if var == 'SCONC_DUST':
            # raise PreventUpdate
            # return dash.no_update, modopen, probopen, wasopen, False, False
            return modopen, probopen, wasopen, False, False
        elif var == 'OD550_DUST':
            # only models and prob can be opened
            if wasopen:
                # return tab_forecast('models'), True, False, False, False, True
                return True, False, False, False, True
            # return dash.no_update, modopen, probopen, wasopen, False, True
            return modopen, probopen, wasopen, False, True
        else:
            if modopen:
                # return dash.no_update, True, False, False, True, True
                return True, False, False, True, True
            # return tab_forecast('models'), True, False, False, True, True
            return True, False, False, True, True

        raise PreventUpdate


    @app.callback(
        [Output('prob-dropdown', 'options'),
         Output('prob-dropdown', 'value')],
        [Input('variable-dropdown-forecast', 'value')],
    )
    def update_prob_dropdown(var):
        """ Update Prob maps dropdown """
        if var in ['OD550_DUST','SCONC_DUST']:
            opt_list = PROB[var]['prob_thresh']
            units = PROB[var]['units']
            return [{'label': '> {} {}'.format(prob, units), 'value': 'prob_{}'.format(prob)} for prob in opt_list], 'prob_{}'.format(opt_list[0])

        raise PreventUpdate


    @app.callback(
        [Output('alert-models-auto', 'is_open'),
         Output('model-dropdown', 'options'),
         Output('model-dropdown', 'value')],
        [Input('variable-dropdown-forecast', 'value')],
        [Input('model-dropdown', 'value'),],
        prevent_initial_call=True
        )
    def update_models_dropdown(variable, checked):

        models = VARS[variable]['models']
        if models == 'all':
            models = list(MODELS.keys())
        else:
            models = eval(models)

        options = [{
            'label': MODELS[model]['name'],
            'value': model,
            'disabled': model not in models,
            } for model in MODELS]

        checked = [c for c in models if c in checked or len(models)==1]
        print('MODELS', models, 'OPTS', type(options), options)
        if len(checked) >= 4:
            options = [{
                'label': MODELS[model]['name'],
                'value': model,
                'disabled': model not in checked,
                } for model in MODELS]

            return True, options, checked

        return False, options, checked


    @app.callback(
        [Output('info-collapse', 'is_open'),
         Output('download-collapse', 'is_open')],
        [Input('info-button', 'n_clicks'),
         Input('download-button', 'n_clicks')],
        [State('info-collapse', 'is_open'),
         State('download-collapse', 'is_open')],
        prevent_initial_call=True
    )
    def sidebar_bottom(n_info, n_download, open_info, open_download):
        ctx = dash.callback_context
        if ctx.triggered:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if button_id == 'info-button':
            if DEBUG: print('clicked INFO', not open_info, False)
            return not open_info, False
        elif button_id == 'download-button':
            if DEBUG: print('clicked DOWN', False, not open_download)
            return False, not open_download

        if DEBUG: print('clicked NONE', False, False)
        raise PreventUdate

    @app.callback(
        Output('netcdf-download', 'data'),
        [Input('btn-netcdf-download', 'n_clicks')],
        [State('model-dropdown', 'value'),
         State('model-date-picker', 'date')],
         prevent_initial_call=True,
    )
    def download_netcdf(btn, models, date):
        ctx = dash.callback_context

        if ctx.triggered:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id == 'btn-netcdf-download':
                if DEBUG: print('NC', btn, models, date)
                try:
                    curdate = dt.strptime(date, '%Y-%m-%d').strftime('%Y%m%d')
                except:
                    curdate = date

                if len(models) == 1:
                    model = models[0]
                    tpl = MODELS[model]['template']
                    mod_path = MODELS[model]['path']
                    final_path = os.path.join(mod_path, 'netcdf', '{date}{tpl}.nc'.format(date=curdate, tpl=tpl))
                    if DEBUG: print('DOWNLOAD', final_path)
                    return dcc.send_file(
                            final_path,
                            filename=os.path.basename(final_path),
                            type='application/x-netcdf')

                with tempfile.NamedTemporaryFile() as fp:
                    with zipfile.ZipFile(
                            fp, mode="w",
                            compression=zipfile.ZIP_DEFLATED) as zf:

                        for model in models:
                            tpl = MODELS[model]['template']
                            mod_path = MODELS[model]['path']
                            final_path = os.path.join(
                                    mod_path,
                                    'netcdf',
                                    '{date}{tpl}.nc'.format(date=curdate, tpl=tpl))
                            if DEBUG: print('ZIPPING', final_path)
                            fname = os.path.basename(final_path)
                            zf.write(final_path, fname)
                    if DEBUG: print('DOWNLOAD', fp.name)
                    return dcc.send_file(
                            fp.name,
                            filename='{}_DUST_MODELS.zip'.format(date),
                            type='application/zip')

    @app.callback(
        Output('anim-download', 'data'),
        [Input('btn-anim-download', 'n_clicks')],
        [State('model-dropdown', 'value'),
         State('variable-dropdown-forecast', 'value'),
         State('model-date-picker', 'date')],
         prevent_initial_call=True,
    )
    def download_anim(btn, models, variable, date):
        """ Download PNG frame """
        from tools import get_figure
        from tools import download_image

        ctx = dash.callback_context

        if ctx.triggered:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id == 'btn-anim-download':
                if DEBUG: print('GIF', btn, models, variable, date)
                try:
                    curdate = dt.strptime(date, '%Y-%m-%d').strftime('%Y%m%d')
                except:
                    curdate = date

                return download_image(models, variable, curdate, anim=True)

    @app.callback(
        Output('frame-download', 'data'),
        [Input('btn-frame-download', 'n_clicks')],
        [State('model-dropdown', 'value'),
         State('variable-dropdown-forecast', 'value'),
         State('model-date-picker', 'date'),
         State('slider-graph', 'value')],
         prevent_initial_call=True,
    )
    def download_frame(btn, models, variable, date, tstep):
        """ Download PNG frame """
        from tools import get_figure
        from tools import download_image

        ctx = dash.callback_context

        if ctx.triggered:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id == 'btn-frame-download':
                if tstep is None:
                    tstep = 0
                if DEBUG: print('PNG', btn, models, variable, date, tstep)
                try:
                    curdate = dt.strptime(date, '%Y-%m-%d').strftime('%Y%m%d')
                except:
                    curdate = date

                return download_image(models, variable, curdate, tstep=int(tstep/FREQ))

    @app.callback(
        Output('was-graph', 'children'),
        [Input('was-date-picker', 'date'),
         Input('was-slider-graph', 'value'),
         Input('was-dropdown', 'value'),],
    )
    def update_was_figure(date, day, was):
        """ Update Warning Advisory Systems maps """
        from tools import get_was_figure
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
        [Input('prob-apply', 'n_clicks'),
         Input('prob-date-picker', 'date'),
         Input('prob-slider-graph', 'value')],
        [State('prob-dropdown', 'value'),
         State('variable-dropdown-forecast', 'value'),
         ],
    )
    def update_prob_figure(n_clicks, date, day, prob, var):
        """ Update Warning Advisory Systems maps """
        from tools import get_prob_figure
        print('PROB', date, day, var, prob)
        ctx = dash.callback_context
        if ctx.triggered:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id != 'prob-apply' and var is None and day is None:
                raise PreventUpdate

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
        Output({'type': 'graph-with-slider', 'index': MATCH}, 'figure'),
        [Input(style, 'n_clicks') for style in STYLES] +
        [Input('airports', 'n_clicks')],
        [State({'type': 'graph-with-slider', 'index': MATCH}, 'figure')]
    )
    def update_styles(*args):
        """ Function updating map layout cartography """
        ctx = dash.callback_context
        figures = args[-1]

        if ctx.triggered:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id in STYLES:
                figures['layout']['mapbox']['style'] = button_id
                return figures
            elif button_id == 'airports':
                traces_list = [trace for trace in figures['data']]
                for trace in figures['data']:
                    if trace['name'] == 'Airports':
                        figures['data'].remove(trace)
                        return figures

                fname = "/data/interactive_test/obs/airports/airports.dat"
                df = pd.read_csv(fname)
                clon = df['Longitude']
                clat = df['Latitude']
                calt = df['Altitude']
                cname = df['Name']
                cicao = df['ICAO']
                ccity = df['City']
                ccountry = df['Country']
                figures['data'].append(
                    dict(
                        type='scattermapbox',
                        name='Airports',
                        below='',
                        lon=clon,
                        lat=clat,
                        text=cname,
                        customdata=cicao,
                        #name='{} ({})'.format(cname, cicao),
                        mode='markers',
                        hovertemplate="lon: %{lon:.2f}<br>" +
                                      "lat: %{lat:.2f}<br>" +
                                      "name: %{text} (%{customdata})",
                        opacity=0.6,
                        showlegend=False,
                        marker=dict(
                            # autocolorscale=True,
                            # symbol='square',
                            color='#2B383E',
                            opacity=0.6,
                            size=10,
                            showscale=False,
                        )
                    ),
                )
                return figures

        raise PreventUpdate


    # retrieve timeseries according to coordinates selected
    @app.callback(
        [ # Output('progress-modal', 'is_open'),
         Output('ts-modal', 'children'),
         Output('ts-modal', 'is_open')],
        [Input({'type': 'graph-with-slider', 'index': ALL}, 'clickData'),
         Input({'type': 'graph-with-slider', 'index': ALL}, 'id')],
        [State('model-date-picker', 'date'),
         State('model-dropdown', 'value'),
         State('variable-dropdown-forecast', 'value')],
        prevent_initial_call=True
    )
    def show_timeseries(cdata, element, date, model, variable):
        """ Renders model comparison timeseries """
        from tools import get_timeseries
        if cdata is None:
            raise PreventUpdate

        lat = lon = None
        for click, elem in zip(cdata, element):
            if elem['index'] in model and click:
                lat = click['points'][0]['lat']
                lon = click['points'][0]['lon']
                break

        if lat is None or lon is None:
            raise PreventUpdate

        if DEBUG: print('SHOW TS """""', model, lat, lon)
        figure = get_timeseries(model, date, variable, lat, lon, forecast=True)
        figure.update_layout(MODEBAR_LAYOUT_TS)
        return dbc.ModalBody(
            dcc.Graph(
                id='timeseries-modal',
                figure=figure,
                config=MODEBAR_CONFIG_TS
            )
        ), True


    # start/stop animation
    @app.callback(
        [Output('slider-interval', 'disabled'),
         Output('slider-interval', 'n_intervals'),
         Output('open-timeseries', 'style'),
         Output('div-collection', 'children'),
         ],
        [Input('btn-play', 'n_clicks'),
         Input('btn-stop', 'n_clicks')],
        [State('slider-interval', 'disabled'),
         State('slider-graph', 'value')],
        prevent_initial_call=True
        )
    def start_stop_autoslider(n_play, n_stop, disabled, value):
        """ Play/Pause map animation """
        ctx = dash.callback_context
        if DEBUG: print("VALUE", value)
        if not value:
            value = 0

        div_noanim = dbc.Spinner(
            id='loading-graph-collection',
            debounce=10,
            show_initially=False,
            children=[
                dbc.Container(
                    id='graph-collection',
                    children=[],
                    fluid=True,
                    )]
        )

        div_anim = dbc.Container(
            id='graph-collection',
            children=[],
            fluid=True,
        )

        if ctx.triggered:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id == 'btn-play' and disabled:
                ts_style = { 'display': 'none' }
                return not disabled, int(value/FREQ), ts_style, div_anim
            elif button_id == 'btn-stop' and not disabled:
                ts_style = { 'display': 'block' }
                return not disabled, int(value/FREQ), ts_style, div_noanim

        raise PreventUpdate


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
        Output('forecast-tab', 'children'),
        [Input('models-apply', 'n_clicks'),
         Input('prob-apply', 'n_clicks'),
         Input('was-apply', 'n_clicks')],
        [State('forecast-tab', 'children')],
        prevent_initial_call=True
        )
    def update_tab_content(models_clicks, prob_clicks, was_clicks, curtab):
        ctx = dash.callback_context

        if ctx.triggered:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id not in ('models-apply', 'prob-apply', 'was-apply'):
                raise PreventUpdate

            print("::::::::::::", len(curtab))
            out_tab = dash.no_update
            if len(curtab) > 3:
                curtab_name = 'models'
            elif curtab[1]['props']['children']['props']['id'] == 'prob-graph':
                curtab_name = 'prob'
            elif curtab[1]['props']['children']['props']['id'] == 'was-graph':
                curtab_name = 'was'

            nexttab_name = button_id.replace('-apply', '')
            if curtab_name != nexttab_name:
                out_tab = tab_forecast(nexttab_name)

            print("::::::::::::", curtab_name, nexttab_name)

            return out_tab

        raise PreventUpdate


    @app.callback(
        [
         Output('btn-play', 'style'),
         Output('btn-stop', 'style'),
         Output('graph-collection', 'children')],
        [Input('models-apply', 'n_clicks'),
         Input('slider-graph', 'value'),
         Input('model-date-picker', 'date')],
        [State('model-dropdown', 'value'),
         State('variable-dropdown-forecast', 'value'),
         State({'type': 'graph-with-slider', 'index': ALL}, 'figure'),
         State({'type': 'graph-with-slider', 'index': ALL}, 'id'),
         State('slider-interval', 'disabled'),
         ],
        prevent_initial_call=True
        )
    def update_models_figure(n_clicks, tstep, date, model, variable, graphs, ids, static):
        """ Update mosaic of maps figures according to all parameters """
        from tools import get_figure
        if DEBUG: print('SERVER: calling figure from picker callback')
        ctx = dash.callback_context

        if ctx.triggered:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id != 'models-apply' and tstep is None and date is None:
                raise PreventUpdate

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

        # if DEBUG and len(ids) > 0: print('SERVER: graphs ' + str(graphs), 'ids' + str(ids))

        figures = []
        if not model:
            fig = get_figure(model, variable, date, tstep, static=static)
            if not static:
                figures.append(
                    dbc.Row([
                        dbc.Col([
                            get_graph(index='none', figure=fig,
                                style={'height': '91vh'}
                                )
                        ])
                    ])
                )
            else:
                figures.append(
                    dbc.Row([
                        dbc.Col([
                            get_graph(index='none', figure=fig,
                                style={'height': '91vh'}
                                )
                        ])
                    ])
                )
            if len(figures) > 1:
                btn_style = { 'display': 'none' }
            else:
                btn_style = { 'display': 'inline-block' }
            return btn_style, btn_style, figures

        ncols, nrows = calc_matrix(len(model))
        past_models = {mod['index']: figure for mod, figure in zip(ids, graphs)}

        for idx, mod in enumerate(model):
            if mod in past_models:
                figure = past_models[mod]
                figure['layout']['mapbox']['zoom'] = 2.8 -(0.5*nrows)
            else:
                figure = get_figure(mod, variable, date, tstep,
                    static=static, aspect=(nrows, ncols))
            if DEBUG: print('STATIC', static)
            if not static:
                figures.append(
                    get_graph(
                        index=mod,
                        figure=get_figure(mod, variable, date, tstep,
                            static=static, aspect=(nrows, ncols)),
                        style={'height': '{}vh'.format(int(91/nrows))}
                    )
                )
            else:
                figures.append(
                    get_graph(
                        index=mod,
                        figure=get_figure(mod, variable, date, tstep,
                            static=static, aspect=(nrows, ncols)),
                        style={'height': '{}vh'.format(int(91/nrows))}
                    )
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
        if len(figures) > 1:
            btn_style = { 'display': 'none' }
        else:
            btn_style = { 'display': 'inline-block' }
        return btn_style, btn_style, res

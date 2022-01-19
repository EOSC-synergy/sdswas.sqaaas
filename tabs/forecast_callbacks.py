""" TAB FORECAST """
import dash
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
from dash.dependencies import Output
from dash.dependencies import Input
from dash.dependencies import State
from dash.dependencies import ALL
from dash.dependencies import MATCH
from dash.dependencies import ClientsideFunction
from dash.exceptions import PreventUpdate
import dash_leaflet as dl

from data_handler import DEFAULT_VAR
from data_handler import DEFAULT_MODEL
from data_handler import VARS 
from data_handler import MODELS
from data_handler import STYLES
from data_handler import FREQ
from data_handler import DEBUG
from data_handler import DATES
from data_handler import PROB 
from data_handler import GRAPH_HEIGHT 
from data_handler import MODEBAR_CONFIG_TS
from data_handler import MODEBAR_LAYOUT_TS
from utils import calc_matrix
from utils import get_graph
from tabs.forecast import tab_forecast

import requests
import pandas as pd
from datetime import datetime as dt
from datetime import timedelta
import time
from io import BytesIO
from PIL import Image
import zipfile
import tempfile
import os.path
import orjson
import math

start_date = DATES['start_date']
end_date = DATES['end_date'] or (dt.now() - timedelta(days=1)).strftime("%Y%m%d")


def register_callbacks(app, cache, cache_timeout):
    """ Registering callbacks """


    @app.callback(
        [Output('collapse-1', 'is_open'),
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
         State('collapse-3', 'is_open'),],
        prevent_initial_call=False
    )
    def render_forecast_tab(modbutton, probbutton, wasbutton, var, modopen, probopen, wasopen):
        """ Function rendering requested tab """
        ctx = dash.callback_context

        if ctx.triggered:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]

            if button_id == "group-1-toggle" and modbutton:
                if modopen is True:
                    return not modopen, False, False, dash.no_update, dash.no_update
                return not modopen, False, False, dash.no_update, dash.no_update
            elif button_id == "group-2-toggle" and probbutton:
                if probopen is True:
                    return False, not probopen, False, dash.no_update, dash.no_update
                return False, not probopen, False, dash.no_update, dash.no_update
            elif button_id == "group-3-toggle" and wasbutton:
                if wasopen is True:
                    return False, False, not wasopen, dash.no_update, dash.no_update
                return False, False, not wasopen, dash.no_update, dash.no_update

        if var == 'SCONC_DUST':
            # raise PreventUpdate
            return modopen, probopen, wasopen, False, False
        elif var == 'OD550_DUST':
            # only models and prob can be opened
            if wasopen:
                return True, False, False, False, True
            return modopen, probopen, wasopen, False, True
        else:
            if modopen:
                return True, False, False, True, True
            return True, False, False, True, True

        raise PreventUpdate


    @app.callback(
        [Output('prob-dropdown', 'options'),
         Output('prob-dropdown', 'value')],
        [Input('variable-dropdown-forecast', 'value')],
        prevent_initial_call=False
    )
    def update_prob_dropdown(var):
        """ Update Prob maps dropdown """
        if var in ['OD550_DUST','SCONC_DUST']:
            opt_list = PROB[var]['prob_thresh']
            units = PROB[var]['units']
            return [{'label': '> {} {}'.format(prob, units), 'value': 'prob_{}'.format(prob)} for prob in opt_list], 'prob_{}'.format(opt_list[0])

        raise PreventUpdate


    @app.callback(
        [  # Output('alert-models-auto', 'is_open'),
         Output('model-dropdown', 'options'),
         Output('model-dropdown', 'value'),
         Output('btn-anim-download', 'style')],
        [Input('variable-dropdown-forecast', 'value')],
        [Input('model-dropdown', 'value'),],
        prevent_initial_call=True
        )
    def update_models_dropdown(variable, checked):

        btn_style = { 'display' : 'block' }
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
        if len(checked) > 1:
            btn_style = { 'display' : 'none' }
        if DEBUG: print('MODELS', models, 'OPTS', type(options), options)
#        if len(checked) >= 16:
#            options = [{
#                'label': MODELS[model]['name'],
#                'value': model,
#                'disabled': model not in checked,
#                } for model in MODELS]
#
#            return True, options, checked

        return options, checked, btn_style


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


#    @app.callback(
#        [Output('login-modal', 'is_open'),
#         Output('alert-login-error', 'is_open'),
#         Output('alert-login-wrong', 'is_open'),
#         Output('netcdf-download', 'data')],
#        [Input('btn-netcdf-download', 'n_clicks'),
#         Input('submit-login', 'n_clicks')],
#        [State('input_username', 'value'),
#         State('input_password', 'value'),
#         State('model-dropdown', 'value'),
#         State('model-date-picker', 'date')],
#        prevent_initial_call=True,
#    )
#    def download_netcdf(btn_download, btn_login, username, password, models, date):
#        ctx = dash.callback_context
#
#        if ctx.triggered:
#            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
#            if DEBUG: print(':::::', ctx.triggered)
#            if DEBUG: print(':::::', button_id)
#            if button_id == 'btn-netcdf-download' and btn_download > 0:
#                return True, False, False, dash.no_update
#
#            if button_id == 'submit-login':
#                res = requests.get('http://bscesdust03.bsc.es/@users/{}'.format(username),
#                        headers={'Accept': 'application/json'},
#                        auth=(username, password))
#                if res.status_code != 200:
#                    return True, True, False, dash.no_update
#
#                user_data = res.json()
#                if DEBUG: print('USER_DATA', user_data)
#                roles = user_data['roles']
#
#                if DEBUG: print('NC', btn_login, models, date)
#                try:
#                    curdate = dt.strptime(date, '%Y-%m-%d').strftime('%Y%m%d')
#                except:
#                    curdate = date
#
#                if curdate == (dt.today() - timedelta(days=1)).strftime('%Y%m%d') and not any(r in roles for r in ('Restricted data user', 'Manager')):
#                    return True, False, True, dash.no_update
#                    
#                if len(models) == 1:
#                    model = models[0]
#                    tpl = MODELS[model]['template']
#                    mod_path = MODELS[model]['path']
#                    final_path = os.path.join(mod_path, 'netcdf', '{date}{tpl}.nc'.format(date=curdate, tpl=tpl))
#                    if DEBUG: print('DOWNLOAD', final_path)
#                    return False, False, False, dcc.send_file(
#                            final_path,
#                            filename=os.path.basename(final_path),
#                            type='application/x-netcdf')
#
#                with tempfile.NamedTemporaryFile() as fp:
#                    with zipfile.ZipFile(
#                            fp, mode="w",
#                            compression=zipfile.ZIP_DEFLATED) as zf:
#
#                        for model in models:
#                            tpl = MODELS[model]['template']
#                            mod_path = MODELS[model]['path']
#                            final_path = os.path.join(
#                                    mod_path,
#                                    'netcdf',
#                                    '{date}{tpl}.nc'.format(date=curdate, tpl=tpl))
#                            if DEBUG: print('ZIPPING', final_path)
#                            fname = os.path.basename(final_path)
#                            zf.write(final_path, fname)
#                    if DEBUG: print('DOWNLOAD', fp.name)
#                    return False, False, False, dcc.send_file(
#                            fp.name,
#                            filename='{}_DUST_MODELS.zip'.format(date),
#                            type='application/zip')
#
#        raise PreventUpdate

    @app.callback(
        Output('btn-anim-download', 'href'),
#         Output('btn-all-frame-download', 'href'),
#         Output('btn-all-anim-download', 'href')],
        [#Input('btn-anim-download', 'n_clicks'),
         Input('model-dropdown', 'value'),
         Input('variable-dropdown-forecast', 'value'),
         Input('model-date-picker', 'date'),
         Input('slider-graph', 'value')],
         prevent_initial_call=False,
    )
    def download_anim_link(models, variable, date, tstep):
        """ Download PNG frame """
        # from tools import get_figure
        from tools import download_image_link

#        ctx = dash.callback_context
#
#        if ctx.triggered:
#            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
#            if button_id == 'btn-anim-download':
        if DEBUG: print('GIF', models, variable, date)
        try:
            curdate = dt.strptime(date, '%Y-%m-%d').strftime('%Y%m%d')
        except:
            curdate = date
        anim = download_image_link(models, variable, curdate, anim=True)
        #all_frame = download_image_link(['all',], variable, curdate, tstep=int(tstep/3), anim=False)
        #all_anim = download_image_link(['all',], variable, curdate, anim=True)
        if DEBUG: print('DOWNLOAD LINK', anim)
        return anim  #, all_frame, all_anim


#    @app.callback(
#        Output('anim-download', 'data'),
#        [Input('btn-anim-download', 'n_clicks')],
#        [State('model-dropdown', 'value'),
#         State('variable-dropdown-forecast', 'value'),
#         State('model-date-picker', 'date')],
#         prevent_initial_call=True,
#    )
#    def download_anim(btn, models, variable, date):
#        """ Download PNG frame """
#        # from tools import get_figure
#        from tools import download_image
#
#        ctx = dash.callback_context
#
#        if ctx.triggered:
#            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
#            if button_id == 'btn-anim-download':
#                if DEBUG: print('GIF', btn, models, variable, date)
#                try:
#                    curdate = dt.strptime(date, '%Y-%m-%d').strftime('%Y%m%d')
#                except:
#                    curdate = date
#                data = download_image(models, variable, curdate, anim=True)
#                if DEBUG: print('DATA', type(data), data.keys(), [data[k] for k in data if k != 'content'])
#                return data
#
#        raise PreventUpdate
#

    @app.callback(
        Output('all-frame-download', 'data'),
        [Input('btn-all-frame-download', 'n_clicks')],
        [State('variable-dropdown-forecast', 'value'),
         State('model-date-picker', 'date'),
         State('slider-graph', 'value')
         ],
         prevent_initial_call=True,
    )
    def download_all_frame(btn, models, variable, date, tstep):
        """ Download PNG frame """
        # from tools import get_figure
        from tools import download_image

        ctx = dash.callback_context

        if ctx.triggered:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id == 'btn-all-frame-download':
                if DEBUG: print('GIF', btn, models, variable, date)
                try:
                    curdate = dt.strptime(date, '%Y-%m-%d').strftime('%Y%m%d')
                except:
                    curdate = date
                data = download_image(models, variable, curdate, tstep=tstep, anim=False)
                if DEBUG: print('DATA', type(data), data.keys(), [data[k] for k in data if k != 'content'])
                return data

        raise PreventUpdate

    @app.callback(
        Output('all-anim-download', 'data'),
        [Input('btn-all-anim-download', 'n_clicks')],
        [State('variable-dropdown-forecast', 'value'),
         State('model-date-picker', 'date')],
         prevent_initial_call=True,
    )
    def download_all_anim(btn, variable, date):
        """ Download PNG frame """
        # from tools import get_figure
        from tools import download_image

        ctx = dash.callback_context

        if ctx.triggered:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id == 'btn-all-anim-download':
                if DEBUG: print('GIF', btn, variable, date)
                try:
                    curdate = dt.strptime(date, '%Y-%m-%d').strftime('%Y%m%d')
                except:
                    curdate = date
                data = download_image(['all'], variable, curdate, anim=True)
                if DEBUG: print('DATA', type(data), data.keys(), [data[k] for k in data if k != 'content'])
                return data

        raise PreventUpdate


    
#    app.clientside_callback(
#        ClientsideFunction(
#            namespace='clientside',
#            function_name='download_png_frame'
#        ),
#        Output('frame-download', 'data'),
#        Input('btn-frame-download', 'n_clicks'),
#        prevent_initial_call=True,
#    )

#    @app.callback(
#        Output('frame-download', 'data'),
#        [Input('btn-frame-download', 'n_clicks')],
#        [State('model-dropdown', 'value'),
#         State('variable-dropdown-forecast', 'value'),
#         State('model-date-picker', 'date'),
#         State('slider-graph', 'value')],
#         prevent_initial_call=True,
#    )
#    def download_frame(btn, models, variable, date, tstep):
#        """ Download PNG frame """
#        from tools import get_figure
#        from tools import download_image
#
#        ctx = dash.callback_context
#
#        if ctx.triggered:
#            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
#            if button_id == 'btn-frame-download':
#                if tstep is None:
#                    tstep = 0
#                if DEBUG: print('PNG', btn, models, variable, date, tstep)
#                try:
#                    curdate = dt.strptime(date, '%Y-%m-%d').strftime('%Y%m%d')
#                except:
#                    curdate = date
#
#                return download_image(models, variable, curdate, tstep=int(tstep/FREQ))

    @app.callback(
        Output('was-graph', 'children'),
        [Input('was-date-picker', 'date'),
         Input('was-slider-graph', 'value'),
         Input('was-dropdown', 'value')],
        [State('variable-dropdown-forecast', 'value'),
         State({'tag': 'view-style', 'index': ALL}, 'active')],
#         State('was-graph', 'zoom'),
#         State('was-graph', 'center')],
        prevent_initial_call=False
        )
    @cache.memoize(timeout=cache_timeout)
    def update_was_figure(date, day, was, var, view):  # zoom, center):
        """ Update Warning Advisory Systems maps """
        from tools import get_was_figure
        from tools import get_figure
        if DEBUG: print('WAS', date, day, was)
        ctx = dash.callback_context
        if ctx.triggered:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id != 'was-apply' and date is None and day is None:
                raise PreventUpdate

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

        if DEBUG: print("WAS figure " + date, was, day)
        if was:
            view = list(STYLES.keys())[view.index(True)]
            was = was[0]
            geojson, legend, info = get_was_figure(was, day, selected_date=date)
            fig = get_figure(model=None, var=var, layer=[geojson, legend, info], view=view, zoom=6.5, center=[12.30, -1.20])
            # fig = get_figure(model=None, var=var, layer=[geojson, legend, info], zoom=zoom, center=center)
            return fig

        raise PreventUpdate 


    @app.callback(
        Output('prob-graph', 'children'),
        [Input('prob-apply', 'n_clicks'),
         Input('prob-date-picker', 'date'),
         Input('prob-slider-graph', 'value')],
        [State('prob-dropdown', 'value'),
         State('variable-dropdown-forecast', 'value'),
         State({'tag': 'view-style', 'index': ALL}, 'active'),
         State('prob-graph', 'zoom'),
         State('prob-graph', 'center')],
        prevent_initial_call=False
    )
    @cache.memoize(timeout=cache_timeout)
    def update_prob_figure(n_clicks, date, day, prob, var, view, zoom, center):
        """ Update Warning Advisory Systems maps """
        from tools import get_prob_figure
        from tools import get_figure
        if DEBUG: print('PROB', date, day, var, prob, var, view, zoom, center)
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
            view = list(STYLES.keys())[view.index(True)]
            # return get_graph(index=prob, figure=get_prob_figure(var, prob, day, selected_date=date))
            geojson, colorbar, info = get_prob_figure(var, prob, day, selected_date=date)
            fig = get_figure(model=None, var=var, layer=[geojson, colorbar, info], view=view, zoom=zoom, center=center)
            if DEBUG: print("FIG", fig)
            return fig
#            return html.Div(
#                fig,
#                id='prob-graph',
#                className='graph-with-slider'
#                )
        raise PreventUpdate
        #return get_graph(index='none', figure=get_prob_figure(var, selected_date=date))


    @app.callback(
        [Output({'tag': 'empty-tile-layer', 'index': ALL}, 'url'),
         Output({'tag': 'empty-tile-layer', 'index': ALL}, 'attribution')],
        [Input({'tag': 'view-style', 'index': ALL}, 'n_clicks')],
        [State({'tag': 'view-style', 'index': ALL}, 'active'),
         State({'tag': 'empty-tile-layer', 'index': ALL}, 'url')],
        prevent_initial_call=True
    )
    # @cache.memoize(timeout=cache_timeout)
    def update_styles_button(*args):
        """ Function updating styles button """
        ctx = dash.callback_context
        if ctx.triggered:
            button_id = orjson.loads(ctx.triggered[0]["prop_id"].split(".")[0])
            if DEBUG: print("BUTTON ID", str(button_id), type(button_id))
            if button_id['index'] in STYLES:
                active = args[-2]
                graphs = args[-1]
                num_graphs = len(graphs)
                # if DEBUG: print("CURRENT ARGS", str(args))
                # if DEBUG: print("NUM GRAPHS", num_graphs)

                res = [False for i in active]
                st_idx = list(STYLES.keys()).index(button_id['index'])
                if active[st_idx] is False:
                    res[st_idx] = True
                url = [STYLES[button_id['index']]['url'] for x in range(num_graphs)]
                attr = [STYLES[button_id['index']]['attribution'] for x in range(num_graphs)]
                if DEBUG:
                    print(res, url, attr)
                return url, attr
                # return [True if i == button_id['index'] else False for i in active]

        if DEBUG: print('NOTHING TO DO')
        raise PreventUpdate


    @app.callback(
        [Output({'tag': 'model-tile-layer', 'index': ALL}, 'url'),
         Output({'tag': 'model-tile-layer', 'index': ALL}, 'attribution'),
         Output({'tag': 'view-style', 'index': ALL}, 'active')],
        [Input({'tag': 'view-style', 'index': ALL}, 'n_clicks')],
        [State({'tag': 'view-style', 'index': ALL}, 'active'),
         State({'tag': 'model-tile-layer', 'index': ALL}, 'url')],
        prevent_initial_call=True
    )
    @cache.memoize(timeout=cache_timeout)
    def update_models_styles_button(*args):
        """ Function updating styles button """
        ctx = dash.callback_context
        if ctx.triggered:
            button_id = orjson.loads(ctx.triggered[0]["prop_id"].split(".")[0])
            if DEBUG: print("BUTTON ID", str(button_id), type(button_id))
            if button_id['index'] in STYLES:
                active = args[-2]
                graphs = args[-1]
                num_graphs = len(graphs)
                # if DEBUG: print("CURRENT ARGS", str(args))
                # if DEBUG: print("NUM GRAPHS", num_graphs)

                res = [False for i in active]
                st_idx = list(STYLES.keys()).index(button_id['index'])
                if active[st_idx] is False:
                    res[st_idx] = True
                url = [STYLES[button_id['index']]['url'] for x in range(num_graphs)]
                attr = [STYLES[button_id['index']]['attribution'] for x in range(num_graphs)]
                if DEBUG:
                    print(res, url, attr)
                return url, attr, res
                # return [True if i == button_id['index'] else False for i in active]

        if DEBUG: print('NOTHING TO DO')
        raise PreventUpdate


#    @app.callback(
#        [Output({'tag': 'model-tile-layer', 'index': MATCH}, 'url'),
#         Output({'tag': 'model-tile-layer', 'index': MATCH}, 'attribution')],
#        [Input('airports', 'n_clicks')] +
#        [Input({'tag': 'view-style', 'index': MATCH}, 'n_clicks')],
#        [State({'tag': 'view-style', 'index': MATCH}, 'active')],
#        prevent_initial_call=True
#    )
#    # @cache.memoize(timeout=cache_timeout)
#    def update_styles(*args):
#        """ Function updating map layout cartography """
#        ctx = dash.callback_context
#        active = args[-1]
#        # urls, attributions = args[-2], args[-1]
#        if DEBUG: print("CURRENT STYLES 2", str(active))
#
#        if ctx.triggered:
#            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
#            if button_id in STYLES:
#                if DEBUG:
#                    print("STYLE", button_id)
#                url = STYLES[button_id]['url']
#                attr = STYLES[button_id]['attribution']
#                return url, attr
#            elif button_id == 'airports':
#                traces_list = [trace for trace in figures['data']]
#                for trace in figures['data']:
#                    if trace['name'] == 'Airports':
#                        figures['data'].remove(trace)
#                        return figures
#
#                fname = "/data/daily_dashboard/obs/airports/airports.dat"
#                df = pd.read_csv(fname)
#                clon = df['Longitude']
#                clat = df['Latitude']
#                calt = df['Altitude']
#                cname = df['Name']
#                cicao = df['ICAO']
#                ccity = df['City']
#                ccountry = df['Country']
#                figures['data'].append(
#                    dict(
#                        type='scattermapbox',
#                        name='Airports',
#                        below='',
#                        lon=clon,
#                        lat=clat,
#                        text=cname,
#                        customdata=cicao,
#                        #name='{} ({})'.format(cname, cicao),
#                        mode='markers',
#                        hovertemplate="lon: %{lon:.2f}<br>" +
#                                      "lat: %{lat:.2f}<br>" +
#                                      "name: %{text} (%{customdata})",
#                        opacity=0.6,
#                        showlegend=False,
#                        marker=dict(
#                            # autocolorscale=True,
#                            # symbol='square',
#                            color='#2B383E',
#                            opacity=0.6,
#                            size=10,
#                            showscale=False,
#                        )
#                    ),
#                )
#                return figures
#
#        raise PreventUpdate


    @app.callback(
        [Output('model-clicked-coords', 'data'),
         Output(dict(tag='model-map-layer', index=ALL), 'children')],
        [Input(dict(tag='model-map', index=ALL), 'click_lat_lng'),
         Input(dict(tag='model-map', index=ALL), 'id')],
        [State(dict(tag='model-map-layer', index=ALL), 'children'),
         State('model-date-picker', 'date'),
         State('slider-graph', 'value'),
         State('variable-dropdown-forecast', 'value')],
    )
    def models_popup(click_data, map_ids, res_list, date, tstep, var):
        from tools import get_single_point
        if DEBUG: print("CLICK:", str(click_data))
        if click_data.count(None) == len(click_data):
            raise PreventUpdate

        if DEBUG: print("MAPID:", str(map_ids), type(map_ids))
        if DEBUG: print("RESLIST:", str(res_list), type(res_list))

        ctxt = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
        if DEBUG: print("CTXT", ctxt, type(ctxt))
        if not ctxt or ctxt is None:
            raise PreventUpdate

        trigger = orjson.loads(ctxt)
        if DEBUG: print('TRIGGER', trigger, type(trigger))

        res = res_list
        if trigger in map_ids:
            model = trigger['index']
            mod_idx = map_ids.index(trigger)
            click = click_data[mod_idx]
            if tstep is None:
                tstep = 0
            else:
                tstep = int(tstep/FREQ)

            if DEBUG: print("MODEL", model, "CLICK", click, "DATE", date, "STEP", tstep, "MODIDX", mod_idx)

            if click is not None and model is not None:
                lat, lon = click
                try:
                    selected_date = dt.strptime(date, '%Y%m%d')
                except:
                    selected_date = dt.strptime(date, '%Y-%m-%d')

                if model in MODELS and MODELS[model]['start'] == 12:
                    if tstep < 4:
                        date = (selected_date - timedelta(days=1)).strftime("%Y%m%d")
                        tstep = 4 + int(tstep)
                    else:
                        date = selected_date.strftime("%Y%m%d")
                        tstep = int(tstep) - 4
                    valid_dt = dt.strptime(date, '%Y%m%d') + timedelta(hours=(tstep+4)*FREQ)
                else:
                    date = selected_date.strftime("%Y%m%d")
                    valid_dt = dt.strptime(date, '%Y%m%d') + timedelta(hours=tstep*FREQ)

                if DEBUG: print("MODEL", model, "CLICK", click, "DATE", date, "STEP", tstep)
                value = get_single_point(model, date, int(tstep), var, lat, lon)
                if DEBUG: print("VALUE:", str(value))

                marker = dl.Popup(
                    children=[
                        html.Div([
                            html.Span(html.P(
                                '{:.2f}'.format(value*VARS[var]['mul'])),
                                className='popup-map-value',
                            ),
                            html.Span([
                                html.B("Lat {:.2f}, Lon {:.2f}".format(lat, lon)), html.Br(),
                                "DATE {:02d} {} {} {:02d}UTC".format(valid_dt.day, dt.strftime(valid_dt, '%b'), valid_dt.year, valid_dt.hour),
                                html.Br(),
                                html.Button("EXPLORE TIMESERIES",
                                    id=dict(
                                        tag='ts-button',
                                        index=model,
                                    ),
                                    n_clicks=0,
                                    className='popup-ts-button'
                                )],
                                className='popup-map-body',
                            )],
                        )
                    ],
                    id='{}-map-point'.format(model),
                    position=[lat, lon],
                    #autoClose=False, 
                    #closeOnEscapeKey=False,
                    #closeOnClick=False,
                    closeButton=True,
                    className='popup-map-point'
                )

                if DEBUG: print("||||", res, "\n", res[mod_idx], type(res[mod_idx]))
                if res[mod_idx]:
                    if DEBUG: print("||||", res[mod_idx], type(res[mod_idx]))
                res[mod_idx] = marker
                coords = [lat, lon]
                if DEBUG: print("COORDS:", str(coords))
                if DEBUG: print("RES:", str(res))
                return coords, res

        raise PreventUpdate


    # retrieve timeseries according to coordinates selected
    @app.callback(
        [Output('ts-modal', 'children'),
         Output('ts-modal', 'is_open'),
         Output({ 'tag': 'ts-button', 'index': ALL }, 'n_clicks')],
        [Input({ 'tag': 'ts-button', 'index': ALL }, 'n_clicks')],
        [State('model-dropdown', 'value'),
         State('model-date-picker', 'date'),
         State('variable-dropdown-forecast', 'value'),
         State('model-clicked-coords', 'data')],
        prevent_initial_call=True
    )
    @cache.memoize(timeout=cache_timeout)
    def show_timeseries(ts_button, mod, date, variable, coords):
        """ Renders model comparison timeseries """
        from tools import get_timeseries

        ctx = dash.callback_context
        if ctx.triggered:
            button_id = orjson.loads(ctx.triggered[0]["prop_id"].split(".")[0])
            if DEBUG: print("BUTTONID:", str(button_id), str(ts_button))
            if button_id['tag'] == 'ts-button' and 1 in ts_button:
                if DEBUG: print('COORDS', coords, type(coords), mod)
                lat, lon = coords

                if lat is None or lon is None:
                    raise PreventUpdate

                if DEBUG: print('SHOW TS """""', mod, lat, lon)
                figure = get_timeseries(mod, date, variable, lat, lon, forecast=True)
                figure.update_layout(MODEBAR_LAYOUT_TS)
                ts_body = dbc.ModalBody(
                    dcc.Graph(
                        id='timeseries-modal',
                        figure=figure,
                        config=MODEBAR_CONFIG_TS
                    )
                )

                return ts_body, True, [0 for i in ts_button]

        raise PreventUpdate


    # start/stop animation
    @app.callback(
        [Output('slider-interval', 'disabled'),
         Output('slider-interval', 'n_intervals'),
         Output('open-timeseries', 'style'),
         #Output('div-collection', 'children'),
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

        if ctx.triggered:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id == 'btn-play' and disabled:
                ts_style = { 'display': 'none' }
                return not disabled, int(value/FREQ), ts_style
            elif button_id == 'btn-stop' and not disabled:
                ts_style = { 'display': 'block' }
                return not disabled, int(value/FREQ), ts_style

        raise PreventUpdate


    @app.callback(
        Output('slider-graph', 'value'),
        [Input('slider-interval', 'n_intervals')],
        prevent_initial_call=True
    )
    @cache.memoize(timeout=cache_timeout)
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
        [State({'tag': 'tab-name', 'index': ALL}, 'id')],
        prevent_initial_call=True
        )
    @cache.memoize(timeout=cache_timeout)
    def update_tab_content(models_clicks, prob_clicks, was_clicks, curtab):
        ctx = dash.callback_context

        if ctx.triggered:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id not in ('models-apply', 'prob-apply', 'was-apply'):
                raise PreventUpdate

            if DEBUG: print("::::::::::::", len(curtab), curtab[0]['index'])
            curtab_name = curtab[0]['index']

            nexttab_name = button_id.replace('-apply', '')
            if DEBUG: print("::::::::::::", curtab_name, nexttab_name)
            if curtab_name != nexttab_name:
                return tab_forecast(nexttab_name)

            raise PreventUpdate

        raise PreventUpdate


#    app.clientside_callback(
#        """
#        function((figures, models, variable, date, tstep)) {
#            return figures;
#        }
#        """,
#
#         Output('graph-collection', 'children'),
#         Input('clientside-graph-collection', 'data'),
#    )

    @app.callback(
         # Output('btn-play', 'style'),
           # Output('btn-stop', 'style'),
         Output('graph-collection', 'children'),
        [Input('models-apply', 'n_clicks'),
         Input('slider-graph', 'value'),
         Input('model-date-picker', 'date')],
        [State('model-dropdown', 'value'),
         State('variable-dropdown-forecast', 'value'),
         # State({'type': 'graph-with-slider', 'index': ALL}, 'figure'),
         # State({'type': 'graph-with-slider', 'index': ALL}, 'id'),
         State('slider-interval', 'disabled'),
         State({'tag': 'view-style', 'index': ALL}, 'active'),
         State({'tag': 'model-map', 'index': ALL}, 'zoom'),
         State({'tag': 'model-map', 'index': ALL}, 'center'),
         State({'tag': 'model-map', 'index': ALL}, 'id'),
         # State('clientside-graph-collection', 'data'),
         ],
        prevent_initial_call=False
        )
    @cache.memoize(timeout=cache_timeout)
    def update_models_figure(n_clicks, tstep, date, model, variable, static, view, zoom, center, ids):  # graphs, ids, static):
        """ Update mosaic of maps figures according to all parameters """
        from tools import get_figure
        if DEBUG: print('SERVER: calling figure from picker callback')

        st_time = time.time()

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
        if DEBUG: print('#### IDS, ZOOM, CENTER:', ids, zoom, center)

        figures = []

        ncols, nrows = calc_matrix(len(model))

#        if len(model) == 1:
#            if zoom and len(zoom) == 1:
#                zoom = zoom[0]
#            else:
#                zoom = None
#            if center and len(center) == 1:
#                center = center[0]
#            else:
#                center = None
#        else:

        if not zoom:
            zoom = [None]
        if not center:
            center = [None]
        if len(model) > 1 or len(model) < len(zoom):
            zoom = [None for item in model]
            center = [None for item in model]
        if DEBUG: print('#### ZOOM, CENTER:', zoom, center, model)
        view = list(STYLES.keys())[view.index(True)]
        for idx, (mod, mod_zoom, mod_center) in enumerate(zip(model, zoom, center)):
            if DEBUG: print("IDX", idx, "MOD", mod, "ZOOM", mod_zoom, "CENTER", mod_center)
            figure = get_figure(mod, variable, date, tstep,
                    static=static, aspect=(nrows, ncols), view=view,
                    center=mod_center, zoom=mod_zoom)
            # if DEBUG: print('FIGURE', figure)
            if DEBUG: print('STATIC', static)
            figures.append(
                    html.Div(
                        figure,
                        id='{}-map-container'.format(mod),
                        className="graph-with-slider",
                        style={'height': '{}vh'.format(int(GRAPH_HEIGHT)/nrows)}
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
        if DEBUG: print("**** REQUEST TIME", str(time.time() - st_time))
        return res

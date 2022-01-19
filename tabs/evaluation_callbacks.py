""" TAB EVALUATION """
import dash
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
from dash.dependencies import Output
from dash.dependencies import Input
from dash.dependencies import State
from dash.dependencies import ALL
from dash.dependencies import MATCH
from dash.exceptions import PreventUpdate
import dash_leaflet as dl
from data_handler import DEFAULT_VAR
from data_handler import DEFAULT_MODEL
from data_handler import VARS 
from data_handler import MODELS
from data_handler import OBS
from data_handler import DEBUG
from data_handler import DATES
from data_handler import MODEBAR_CONFIG
from data_handler import MODEBAR_CONFIG_TS
from data_handler import MODEBAR_LAYOUT
from data_handler import MODEBAR_LAYOUT_TS
from data_handler import DISCLAIMER_MODELS
from data_handler import DISCLAIMER_OBS

from utils import calc_matrix
from utils import get_graph

from tabs.evaluation import tab_evaluation
from tabs.evaluation import STATS

from datetime import datetime as dt
from datetime import timedelta
from dateutil.relativedelta import relativedelta
import pandas as pd
import orjson
import os.path


SCORES = list(STATS.keys())
start_date = DATES['start_date']
end_date = DATES['end_date'] or (dt.now() - timedelta(days=1)).strftime("%Y%m%d")


def extend_l(l):
    """ Estend list of lists to a flat list """
    res = []
    for x in l:
        res.extend(x)
    if not isinstance(res, list):
        res = [res]
    return res


def register_callbacks(app, cache, cache_timeout):
    """ Registering callbacks """

    @app.callback(
        [Output('evaluation-tab', 'children'),
         Output('nrt-evaluation', 'style'),
         Output('scores-evaluation', 'style')],
        [Input('nrt-evaluation', 'n_clicks'),
         Input('scores-evaluation', 'n_clicks')],
    )
    def render_evaluation_tab(nrtbutton, scoresbutton):
        """ Function rendering requested tab """
        bold = { 'fontWeight': 'bold' }
        norm = { 'fontWeight': 'normal' }
        ctx = dash.callback_context

        if ctx.triggered:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]

            if button_id == "nrt-evaluation" and nrtbutton:
                return tab_evaluation('nrt'), bold, norm
            elif button_id == "scores-evaluation" and scoresbutton:
                return tab_evaluation('scores'), norm, bold

        return dash.no_update, bold, norm
        #raise PreventUpdate

    @app.callback(
        [Output('obs-selection-dropdown','options'),
         Output('obs-selection-dropdown','placeholder')],
        [Input('obs-timescale-dropdown', 'value')],
        [State('obs-network-dropdown', 'value')],
        prevent_initial_call=True
    )
    def update_time_selection(timescale, network):

        if timescale is None:
            raise PreventUpdate

        if network == 'modis':
            start_date = '20180101'
        elif network == 'aeronet':
            start_date = '20210101'

        seasons = {
               '03': 'Spring',
               '06': 'Summer',
               '09': 'Autumn',
               '12': 'Winter'
                }

        if timescale == 'seasonal':
            ret = [{
                'label' : '{} {}'.format(seasons[mon.strftime('%m')],
                    mon.strftime('%Y')),
                'value' : '{}-{}'.format(
                    mon.strftime('%Y%m'), (mon + relativedelta(months=2)).strftime('%Y%m'))
                }
                for mon in pd.date_range(start_date, end_date, freq='Q')[::-1]][1:]
            placeholder = 'Select season'
        elif timescale == 'annual':
            ret = [{
                'label': mon.strftime('%Y'),
                'value': mon.strftime('%Y'),
                } for mon in 
                pd.date_range(start_date, end_date, freq='A')[::-1]]
            placeholder = 'Select year'
        else:   # timescale == 'monthly':
            ret = [{
                'label': mon.strftime('%B %Y'),
                'value': mon.strftime('%Y%m'),
                } for mon in 
                pd.date_range(start_date, end_date, freq='M')[::-1]]
            placeholder = 'Select month'
    
        return ret, placeholder

    @app.callback(
        [Output('modis-scores-table', 'columns'),
         Output('modis-scores-table', 'data'),
         Output('modis-scores-table', 'style_table')],
        [Input('scores-apply', 'n_clicks')],
        [State('obs-models-dropdown', 'value'),
         State('obs-statistics-dropdown', 'value'),
         State('obs-network-dropdown', 'value'),
         State('obs-timescale-dropdown', 'value'),
         State('obs-selection-dropdown', 'value')],
        prevent_initial_call=True
    )
    def modis_scores_tables_retrieve(n, models, stat, network, timescale, selection):
        """ Read scores tables and show data """

        if not n or network != 'modis':
            return dash.no_update, dash.no_update, { 'display': 'none' }

        if isinstance(models, str):
            models = [models]

        if isinstance(stat, str):
            stat = [stat]

        stat = ['model'] + stat

        if DEBUG: print("###########", models, stat, network, timescale, selection, n)
        filedir = OBS[network]['path']
        filename = "{}_scores.h5".format(selection)
        tab_name = "total_{}".format(selection)
        filepath = os.path.join(filedir, "h5", filename)
        df = pd.read_hdf(filepath, tab_name)
        ret = df.loc[df['model'].isin(models), stat]
        ret['model'] = ret['model'].map({k:MODELS[k]['name'] for k in MODELS})
        if DEBUG: print('---', ret.columns)
        if DEBUG: print('---', ret.to_dict('records'))
        columns = [{'name': i in SCORES and
            STATS[i] or '', 'id': i} for
            i in stat]
        return columns, ret.replace('_', ' ', regex=True).to_dict('records'), { 'display': 'block' }


    @app.callback(
        [Output('scores-map-modalbody', 'figure'),
         Output('scores-map-modal', 'is_open')],
        [Input('scores-map-apply', 'n_clicks'),
         Input('obs-models-dropdown-modal', 'value'),
         Input('obs-statistics-dropdown-modal', 'value'),],
        [State('obs-network-dropdown', 'value'),
         State('obs-selection-dropdown', 'value')],
        prevent_initial_call=True
    )
    @cache.memoize(timeout=cache_timeout)
    def scores_maps_retrieve(n_clicks, model, score, network, selection):
        """ Read scores tables and plot maps """
        from tools import get_scores_figure
        mb = MODEBAR_LAYOUT_TS

        ctx = dash.callback_context

        print(':::', n_clicks, model, score, network, selection)
        if ctx.triggered:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if button_id != "scores-map-apply":
                if model is not None and score is not None:
                    figure = get_scores_figure(network, model, score, selection)
                    figure.update_layout(mb)
                    return figure, True

                raise PreventUpdate

            figure = get_scores_figure(network, DEFAULT_MODEL, 'bias', selection)
            figure.update_layout(mb)
            return figure, True

        return dash.no_update, False  # PreventUpdate


    @app.callback(
        extend_l([
          [Output('aeronet-scores-table-{}'.format(score), 'columns'),
           Output('aeronet-scores-table-{}'.format(score), 'data'),
           Output('aeronet-scores-table-{}'.format(score), 'style_table'),
           Output('aeronet-scores-table-{}'.format(score), 'selected_cells'),
           Output('aeronet-scores-table-{}'.format(score), 'active_cell')]
            for score in SCORES]),
        [Input('scores-apply', 'n_clicks'),
        *[Input('aeronet-scores-table-{}'.format(score), 'active_cell')
            for score in SCORES]],
        [State('obs-models-dropdown', 'value'),
         State('obs-statistics-dropdown', 'value'),
         State('obs-network-dropdown', 'value'),
         State('obs-timescale-dropdown', 'value'),
         State('obs-selection-dropdown', 'value')] +
        extend_l([[State('aeronet-scores-table-{}'.format(score), 'columns'),
           State('aeronet-scores-table-{}'.format(score), 'data'),
           State('aeronet-scores-table-{}'.format(score), 'style_table')]
            for score in SCORES]),
        prevent_initial_call=True
    )
    def aeronet_scores_tables_retrieve(n, *args):  # *activel_cells, models, stat, network, timescale, selection, *tables):
        """ Read scores tables and show data """

        ctx = dash.callback_context
        active_cells = list(args[:len(SCORES)])
        tables = list(args[-len(SCORES)*3:])
        if DEBUG: print("ACTIVES", active_cells)

        if DEBUG: print("###########", args[len(SCORES):-len(SCORES)*3])
        models, stat, network, timescale, selection = args[len(SCORES):-len(SCORES)*3]

        if ctx.triggered:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            if DEBUG: print("BUTTON", button_id)
            if button_id not in ['scores-apply'] + ['aeronet-scores-table-{}'.format(score) for score in SCORES]:
                raise PreventUpdate

        if not n or network != 'aeronet':
            return extend_l([[dash.no_update, dash.no_update, { 'display': 'none' }, dash.no_update, dash.no_update] for score in SCORES])

        areas = ['Mediterranean', 'Middle East', 'Sahel/Sahara', 'Total']

        if isinstance(models, str):
            models = [models]

        if isinstance(stat, str):
            stat = [stat]

        models = ['station'] + models

        if DEBUG: print("@@@@@@@@@@@", models, stat, network, timescale, selection, n, len(tables))
        filedir = OBS[network]['path']

        stat_idxs = [SCORES.index(st) for st in stat]

        ret_tables = [None for _ in range(len(SCORES)*5)]
        for table_idx in range(int(len(tables)/3)):
            obj_idx = table_idx * 3
            ret_idx = table_idx * 5
            ret_tables[ret_idx] = tables[obj_idx]
            ret_tables[ret_idx+1] = tables[obj_idx+1]
            ret_tables[ret_idx+2] = tables[obj_idx+2]
            curr_columns = tables[obj_idx]
            curr_data = tables[obj_idx+1]
            if active_cells[table_idx] is not None and \
                  active_cells[table_idx]['column_id'] == 'station':
                curr_active_cell = active_cells[table_idx]
            else:
                curr_active_cell = None
            if table_idx in stat_idxs:
                filename = "{}_{}.h5".format(selection, SCORES[table_idx])
                tab_name = "{}_{}".format(SCORES[table_idx], selection)
                filepath = os.path.join(filedir, "h5", filename)
                if not os.path.exists(filepath):
                    if DEBUG: print ("TABLES 0", tables)
                    for i, table in enumerate(tables):
                        if isinstance(table, dict):
                            tables[i] = { 'display': 'none' }
                            tables.insert(i+1, dash.no_update)
                            tables.insert(i+2, dash.no_update)
                    if DEBUG: print ("TABLES 1", tables)
                    return tables

                df = pd.read_hdf(filepath, tab_name).replace('_', ' ', regex=True)  # .round(decimals=2).fillna('-')
                # replace "tables" columns
                ret_tables[ret_idx] = [{'name': i in MODELS and
                    [STATS[SCORES[table_idx]], MODELS[i]['name']] or
                    [STATS[SCORES[table_idx]], ''], 'id': i} for
                    i in models]
                # replace "tables" data
                if curr_active_cell is not None:
                    if DEBUG: print("ACTIVE", curr_active_cell)
                    curr_data = tables[obj_idx+1]
                    if not curr_data:
                        continue
                    row_number = curr_active_cell['row']
                    # 1st case:
                    if DEBUG:
                        print('CURRDATA', curr_data)
                        print('ROWNUMBER', row_number)
                    value = curr_data[row_number]['station']
                    if value not in areas[:-1]:
                        raise PreventUpdate
                    val_idx = df.loc[df['station']==value].index[0]
                    # check following data
                    if row_number < len(curr_data)-1:
                        foll_val = curr_data[row_number+1]['station']
                        if foll_val in areas:
                            foll_idx = df.loc[df['station']==foll_val].index[0]
                            tables[obj_idx+1] = [table_row for table_row in curr_data if curr_data.index(table_row) < row_number] + df.iloc[val_idx:foll_idx-1][models].to_dict('rows') + [table_row for table_row in curr_data if curr_data.index(table_row) > row_number]
                        else:
                            foll_area = areas[areas.index(value)+1]
                            if DEBUG:
                                print("'''", curr_data)
                                print("---", foll_area)
                            foll_idx = curr_data.index([row for row in curr_data if row['station'] == foll_area][0])
                            tables[obj_idx+1] = [table_row for table_row in curr_data if curr_data.index(table_row) <= row_number] +  [table_row for table_row in curr_data if curr_data.index(table_row) >= foll_idx]
                    ret_tables[ret_idx+1] = tables[obj_idx+1]
                    ret_tables[ret_idx+2] = { 'display': 'block' }
                    ret_tables[ret_idx+3] = []
                    ret_tables[ret_idx+4] = None
                else:
                    ret_tables[ret_idx+1] = df.loc[df['station'].isin(areas), models].to_dict('records')
                    ret_tables[ret_idx+2] = { 'display': 'block' }
                    ret_tables[ret_idx+3] = dash.no_update
                    ret_tables[ret_idx+4] = dash.no_update

            else:
                ret_tables[ret_idx] = []
                ret_tables[ret_idx+1] = []
                ret_tables[ret_idx+2] = { 'display': 'block' }
                ret_tables[ret_idx+3] = dash.no_update
                ret_tables[ret_idx+4] = dash.no_update


        if DEBUG: print('LEN', len(ret_tables))
        if DEBUG: print ("TABLES RET", ret_tables)
        return ret_tables


    @app.callback(
        [Output('ts-eval-modis-modal', 'children'),
         Output('ts-eval-modis-modal', 'is_open')],
        [Input('ts-eval-modis-button', 'n_clicks')],
        [State('modis-clicked-coords', 'data'),
         State('eval-date-picker', 'date'),
         State('obs-dropdown', 'value'),
         State('obs-mod-dropdown', 'value')],
        prevent_initial_call=True
    )
    @cache.memoize(timeout=cache_timeout)
    def show_eval_modis_timeseries(nclicks, coords, date, obs, model):
        """ Retrieve MODIS evaluation timeseries according to station selected """
        from tools import get_timeseries
        if coords is None or nclicks == 0:
            raise PreventUpdate

        ctxt = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
        if DEBUG: print("CTXT", ctxt, type(ctxt))
        if not ctxt or ctxt is None or ctxt != 'ts-eval-modis-button':  #  or nclicks == 0:P:
            raise PreventUpdate

        if DEBUG: print('TRIGGER', ctxt, type(ctxt))
        lat, lon, val = coords
        print(coords, date)
        models = [obs, model]  # [model for model in MODELS]
        if DEBUG: print('SHOW MODIS EVAL TS"""""', coords)
        figure = get_timeseries(models, date, DEFAULT_VAR, lat, lon)
        mb = MODEBAR_LAYOUT_TS
        figure.update_layout(mb)
        return dbc.ModalBody(
            dcc.Graph(
                id='timeseries-eval-modal',
                figure=figure,
                config=MODEBAR_CONFIG_TS
            )
        ), True
 
        # return dash.no_update, False  # PreventUpdate

    @app.callback(
        [Output('modis-clicked-coords', 'data'),
         Output(dict(tag='modis-map-layer', index='modis'), 'children')],
        [Input(dict(tag='modis-map', index='modis'), 'click_lat_lng')],
        [State('eval-date-picker', 'date'),
         State('obs-dropdown', 'value'),
         State('obs-mod-dropdown', 'value')],
    )
    def modis_popup(click_data, date, obs, model):
        from tools import get_single_point
        if DEBUG: print("CLICK:", str(click_data))
        if not click_data:
            raise PreventUpdate
        ctxt = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
        ctxt = orjson.loads(dash.callback_context.triggered[0]["prop_id"].split(".")[0])
        if DEBUG: print("CTXT", ctxt, type(ctxt))
        if not ctxt or ctxt is None or ctxt != {'index': 'modis', 'tag': 'modis-map'}:
            raise PreventUpdate

        lat, lon = click_data
        value = get_single_point(model, date, 0, DEFAULT_VAR, lat, lon)
        if DEBUG: print("VALUE", value)
        
        if not value:
            raise PreventUpdate

        if DEBUG: print("VALUE", value)
        try:
            valid_dt = dt.strptime(date, '%Y%m%d') + timedelta(hours=12)
        except:
            valid_dt = dt.strptime(date, '%Y-%m-%d') + timedelta(hours=12)

        marker = dl.Popup(
            children=[
                html.Div([
                        html.Span(html.P(
                            '{:.2f}'.format(value*VARS[DEFAULT_VAR]['mul'])),
                            className='popup-map-value',
                        ),
                        html.Span([
                            html.B("Lat {:.2f}, Lon {:.2f}".format(lat, lon)), html.Br(),
                            "DATE {:02d} {} {} {:02d}UTC".format(valid_dt.day, dt.strftime(valid_dt, '%b'), valid_dt.year, valid_dt.hour),
                            html.Br(),
                            html.Button("EXPLORE TIMESERIES",
                                id='ts-eval-modis-button',
                                n_clicks=0,
                                className='popup-ts-button'
                            )],
                            className='popup-map-body',
                        )],
                    )
            ],
            id='modis-map-point',
            position=[lat, lon],
            autoClose=False, 
            closeOnEscapeKey=False,
            closeOnClick=False,
            closeButton=True,
            className='popup-map-point'
        )

        return [lat, lon, value], marker


    @app.callback(
        [Output('stations-clicked-coords', 'data'),
         Output(dict(tag='empty-map-layer', index='None'), 'children')],
        [Input(dict(tag='empty-map', index='None'), 'click_lat_lng')],
        [State('stations-dataframe', 'data')],
    )
    def stations_popup(click_data, stations):
        if not click_data:
            raise PreventUpdate

        if DEBUG: print("CLICK:", str(click_data))

        # figure = get_eval_timeseries(obs, start_date, end_date, DEFAULT_VAR, idx, name)
#
        ctxt = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
        if DEBUG: print("CTXT", ctxt, type(ctxt))
        if not ctxt or ctxt is None:
            raise PreventUpdate

        trigger = orjson.loads(ctxt)
        if DEBUG: print('TRIGGER', trigger, type(trigger))

        if trigger != {'index': 'None', 'tag': 'empty-map'}:
            raise PreventUpdate

        df_stations = pd.DataFrame(stations)
        lat, lon = click_data
        curr_station = df_stations[(df_stations['lon'].round(2) == round(lon, 2)) | \
            (df_stations['lat'] == round(lat, 2))]['stations'].values
        
        if not curr_station:
            raise PreventUpdate

        curr_station = curr_station[0]

        if DEBUG: print("CURR_STATION", curr_station)

        marker = dl.Popup(
            children=[
                html.Div([
                    html.Span([
                        html.B("Lat {:.2f}, Lon {:.2f}".format(lat, lon)), html.Br(),
                        "STATION: ", html.B("{}".format(curr_station)), html.Br(),
                        html.Button("EXPLORE TIMESERIES",
                            id='ts-eval-button',
                            n_clicks=0,
                            className='popup-ts-button'
                        )],
                        className='popup-map-eval-body',
                    )],
                )
            ],
            id='empty-map-point',
            position=[lat, lon],
            autoClose=False, 
            closeOnEscapeKey=False,
            closeOnClick=False,
            closeButton=True,
            className='popup-map-point'
        )

        curr_data = df_stations[(df_stations['lon'].round(2) == round(lon, 2)) | \
            (df_stations['lat'] == round(lat, 2))]
        return curr_data.to_dict(), marker


    @app.callback(
        [Output('ts-eval-modal', 'children'),
         Output('ts-eval-modal', 'is_open')],
        [Input('ts-eval-button', 'n_clicks')],
        [State('stations-clicked-coords', 'data'),
         State('eval-date-picker', 'start_date'),
         State('eval-date-picker', 'end_date'),
         State('obs-dropdown', 'value'),
         State('obs-mod-dropdown', 'value')],
        prevent_initial_call=True
    )
    @cache.memoize(timeout=cache_timeout)
    def show_eval_aeronet_timeseries(nclicks, cdata, start_date, end_date, obs, model):
        """ Retrieve AERONET evaluation timeseries according to station selected """
        from tools import get_eval_timeseries
        ctxt = dash.callback_context.triggered[0]["prop_id"].split(".")[0]
        if DEBUG: print("CTXT", ctxt, type(ctxt))
        if not ctxt or ctxt is None:
            raise PreventUpdate

        if ctxt != 'ts-eval-button' or nclicks == 0:
            raise PreventUpdate

        if not cdata:
            raise PreventUpdate

        print(start_date, end_date, obs, model, cdata)
        if DEBUG: print('EVAL AERONET CLICKDATA', cdata)
        cdata = pd.DataFrame(cdata)
        idx = int(cdata.index.values[0])
        lon = cdata.lon.round(2).values[0]
        lat = cdata.lat.round(2).values[0]
        stat = cdata.stations.values[0]
        if idx != 0:
            figure = get_eval_timeseries(obs, start_date, end_date, DEFAULT_VAR, idx, stat, model)
            mb = MODEBAR_LAYOUT_TS
            figure.update_layout(mb)
            if DEBUG: print('SHOW AERONET EVAL TS"""""', obs, idx, stat)
            return dbc.ModalBody(
                dcc.Graph(
                    id='timeseries-eval-modal',
                    figure=figure,
                    config=MODEBAR_CONFIG_TS
                )
            ), True

        raise PreventUpdate


    @app.callback(
        [Output('stations-dataframe', 'data'),
         Output('graph-eval-aeronet', 'children')],
        [Input('eval-date-picker', 'start_date'),
         Input('eval-date-picker', 'end_date')],
        [State('obs-dropdown', 'value')],
        prevent_initial_call=True)
    @cache.memoize(timeout=cache_timeout)
    def update_eval_aeronet(sdate, edate, obs):
        """ Update AERONET evaluation figure according to all parameters """
        from tools import get_figure
        from tools import get_obs1d
        if DEBUG: print('SERVER: calling figure from EVAL picker callback')
        if DEBUG: print('SERVER: SDATE', str(sdate))
        if sdate is None or edate is None or obs != 'aeronet':
            raise PreventUpdate

        sdate = sdate.split()[0]
        try:
            sdate = dt.strptime(
                sdate, "%Y-%m-%d").strftime("%Y%m%d")
        except:
            sdate = end_date
            pass
        if DEBUG: print('SERVER: callback start_date {}'.format(sdate))

        if edate is not None:
            edate = edate.split()[0]
            try:
                edate = dt.strptime(
                    edate, "%Y-%m-%d").strftime("%Y%m%d")
            except:
                pass
            if DEBUG: print('SERVER: callback end_date {}'.format(edate))
        else:
            edate = end_date

        stations, points_layer = get_obs1d(sdate, edate, obs, DEFAULT_VAR)
        fig = get_figure(model=None, var=DEFAULT_VAR, layer=points_layer)
        # if DEBUG: print("---", fig)
        return stations.to_dict(), fig


    @app.callback(
       [Output('graph-eval-modis-obs', 'children'),
        Output('graph-eval-modis-mod', 'children')],
       [Input('eval-date-picker', 'date'),
        Input('obs-mod-dropdown', 'value')],
       [State('obs-dropdown', 'value'),
        State('graph-eval-modis-mod', 'children')],
        prevent_initial_call=True)
    @cache.memoize(timeout=cache_timeout)
    def update_eval_modis(date, mod, obs, mod_div):
        """ Update MODIS evaluation figure according to all parameters """
        if date is None or mod is None or obs != 'modis':
            raise PreventUpdate

        from tools import get_figure
        if DEBUG: print('SERVER: calling figure from EVAL picker callback')
        if DEBUG: print(mod_div)
        mod_center = mod_div['props']['center']
        mod_zoom = mod_div['props']['zoom']

        if date is not None:
            date = date.split()[0]
            try:
                date = dt.strptime(
                    date, "%Y-%m-%d").strftime("%Y%m%d")
            except:
                pass
            if DEBUG: print('SERVER: callback date {}'.format(date))
        else:
            date = end_date

        if DEBUG: print("ZOOM", mod_zoom, "CENTER", mod_center)
        if MODELS[mod]['start'] == 12:
            tstep = 4
        else:
            tstep = 0
        fig_mod = get_figure(model=mod, var=DEFAULT_VAR, selected_date=date, tstep=tstep, hour=12, center=mod_center, zoom=mod_zoom)
        fig_obs = get_figure(model=obs, var=DEFAULT_VAR, selected_date=date, tstep=0, center=mod_center, zoom=mod_zoom)

        if DEBUG: print("MODIS", fig_obs)
        return fig_obs, fig_mod


    @app.callback(
        [Output('eval-date', 'children'),
         Output('eval-graph', 'children'),
         Output('obs-dropdown', 'value'),
         Output('obs-mod-dropdown-span', 'style')],
        [Input('obs-dropdown', 'value')],
         prevent_initial_call=True)
    @cache.memoize(timeout=cache_timeout)
    def update_eval(obs):
        """ Update evaluation figure according to all parameters """
        from tools import get_figure
        # from tools import get_obs1d
        if DEBUG: print('SERVER: calling figure from EVAL picker callback')
        # if DEBUG: print('SERVER: interval ' + str(n))

        if obs == 'aeronet':

            eval_date = [
              html.Label("Date range"),
              dcc.DatePickerRange(
                id='eval-date-picker',
                min_date_allowed=dt.strptime(start_date, "%Y%m%d"),
                max_date_allowed=dt.strptime(end_date, "%Y%m%d"),
                initial_visible_month=dt.strptime(end_date, "%Y%m%d"),
                display_format='DD MMM YYYY',
                # end_date=end_date,
                updatemode='bothdates',
            )]

            eval_graph = html.Div(
                        get_figure(),
                        id='graph-eval-aeronet',
                    )
#            eval_graph = [dbc.Spinner(
#                get_graph(
#                    gid='graph-eval-aeronet',
#                    figure=get_figure(),
#                    )),
#                ]

            style = { 'display': 'none' }

        elif obs == 'modis':

            eval_date = [
              html.Label("Date"),
              dcc.DatePickerSingle(
                id='eval-date-picker',
                min_date_allowed=dt.strptime(start_date, "%Y%m%d"),
                max_date_allowed=dt.strptime(end_date, "%Y%m%d"),
                initial_visible_month=dt.strptime(end_date, "%Y%m%d"),
                display_format='DD MMM YYYY',
                date=end_date,
                # with_portal=True,
            )]

            fig_mod = get_figure(model='median', var=DEFAULT_VAR,
                    selected_date=end_date, tstep=4)
            #center = fig_mod['layout']['mapbox']['center']
            fig_obs = get_figure(model=obs, var=DEFAULT_VAR,
                    selected_date=end_date, tstep=0)
            graph_obs = html.Div([
                html.Div(
                    fig_obs,
                    id='graph-eval-modis-obs',
                    ),
                html.Div(DISCLAIMER_OBS,
                    className='disclaimer')
                ],
                )
            graph_mod = html.Div([
                html.Div(
                    fig_mod,
                    id='graph-eval-modis-mod',
                    ),
                html.Div(DISCLAIMER_MODELS,
                    className='disclaimer')
                ],
                )
            eval_graph = [dbc.Row([
                    dbc.Col(graph_obs, width=6),
                    dbc.Col(graph_mod, width=6)
                ],
                align='start',
                no_gutters=True
                )]

            style = { 'display': 'table-cell' }

        else:
            raise PreventUpdate

        return eval_date, eval_graph, obs, style

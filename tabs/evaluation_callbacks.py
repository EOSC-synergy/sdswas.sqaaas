""" TAB EVALUATION """
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
from data_handler import OBS
from data_handler import DEBUG
from data_handler import DATES
from data_handler import MODEBAR_CONFIG
from data_handler import MODEBAR_CONFIG_TS
from data_handler import MODEBAR_LAYOUT
from data_handler import MODEBAR_LAYOUT_TS

from utils import calc_matrix
from utils import get_graph

from tabs.evaluation import tab_evaluation
from tabs.evaluation import STATS

from datetime import datetime as dt
import pandas as pd
import os.path


SCORES = list(STATS.keys())
start_date = DATES['start_date']
end_date = DATES['end_date']


def extend_l(l):
    """ Estend list of lists to a flat list """
    res = []
    for x in l:
        res.extend(x)
    if not isinstance(res, list):
        res = [res]
    return res


def register_callbacks(app):
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
        bold = { 'font-weight': 'bold' }
        norm = { 'font-weight': 'normal' }
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
        [Output('obs-selection-dropdown','options')],
        [Input('obs-timescale-dropdown', 'value')],
        prevent_initial_call=True
    )
    def update_time_selection(timescale):

        if timescale is None:
            raise PreventUpdate

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
                'value' : '{}{}'.format(seasons[mon.strftime('%m')],
                    mon.strftime('%Y'))
                }
                for mon in pd.date_range(start_date, end_date, freq='Q')]
        elif timescale == 'annual':
            ret = [{
                'label': mon.strftime('%Y'),
                'value': mon.strftime('%Y'),
                } for mon in 
                pd.date_range(start_date, end_date, freq='A')]
        else:   # timescale == 'monthly':
            ret = [{
                'label': mon.strftime('%B %Y'),
                'value': mon.strftime('%Y%m'),
                } for mon in 
                pd.date_range(start_date, end_date, freq='M')]
    
        return [ret]

    @app.callback(
        [Output('modis-scores-table', 'columns'),
         Output('modis-scores-table', 'data'),
         Output('modis-scores-table', 'style_table')],
        [Input('obs-models-dropdown', 'value'),
         Input('obs-statistics-dropdown', 'value'),
         Input('obs-network-dropdown', 'value'),
         Input('obs-timescale-dropdown', 'value'),
         Input('obs-selection-dropdown', 'value'),
         Input('scores-apply', 'n_clicks')],
        prevent_initial_call=True
    )
    def modis_scores_tables_retrieve(models, stat, network, timescale, selection, n):
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
        extend_l([[Output('aeronet-scores-table-{}'.format(score), 'columns'),
           Output('aeronet-scores-table-{}'.format(score), 'data'),
           Output('aeronet-scores-table-{}'.format(score), 'style_table')]
            for score in SCORES]),
        [Input('obs-models-dropdown', 'value'),
         Input('obs-statistics-dropdown', 'value'),
         Input('obs-network-dropdown', 'value'),
         Input('obs-timescale-dropdown', 'value'),
         Input('obs-selection-dropdown', 'value'),
         Input('scores-apply', 'n_clicks'),
        *[Input('aeronet-scores-table-{}'.format(score), 'active_cell')
            for score in SCORES]],
        extend_l([[State('aeronet-scores-table-{}'.format(score), 'columns'),
           State('aeronet-scores-table-{}'.format(score), 'data'),
           State('aeronet-scores-table-{}'.format(score), 'style_table')]
            for score in SCORES]),
        prevent_initial_call=True
    )
    def aeronet_scores_tables_retrieve(models, stat, network, timescale, selection, n, *tables):
        """ Read scores tables and show data """

        if not n or network != 'aeronet':
            return extend_l([[dash.no_update, dash.no_update, { 'display': 'none' }] for score in SCORES])

        areas = ['Mediterranean', 'Middle East', 'Sahel/Sahara', 'Total']

        active_cells = list(tables[:len(SCORES)])
        tables = list(tables[len(SCORES):])

        if isinstance(models, str):
            models = [models]

        if isinstance(stat, str):
            stat = [stat]

        models = ['station'] + models

        if DEBUG: print("@@@@@@@@@@@", models, stat, network, timescale, selection, n, len(tables))
        filedir = OBS[network]['path']

        stat_idxs = [SCORES.index(st) for st in stat]

        for table_idx in range(int(len(tables)/3)):
            obj_idx = table_idx * 3
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
                df = pd.read_hdf(filepath, tab_name).replace('_', ' ', regex=True)  # .round(decimals=2).fillna('-')
                # replace "tables" columns
                tables[obj_idx] = [{'name': i in MODELS and
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

                else:
                    tables[obj_idx+1] = df.loc[df['station'].isin(areas), models].to_dict('records')

            else:
                tables[obj_idx] = []
                tables[obj_idx+1] = []

            tables[obj_idx+2] = { 'display': 'block' }

        print('LEN', len(tables))
        return tables

    @app.callback(
        [Output('ts-eval-modis-modal', 'children'),
         Output('ts-eval-modis-modal', 'is_open')],
        [Input('graph-eval-modis-obs', 'clickData')],
        [State('eval-date-picker', 'date'),
         State('obs-dropdown', 'value'),
         State('obs-mod-dropdown', 'value')],
        prevent_initial_call=True
    )
    def show_eval_modis_timeseries(obs_cdata, date, obs, model):
        """ Retrieve MODIS evaluation timeseries according to station selected """
        from tools import get_timeseries
        lat = lon = None
        print(obs_cdata, date)
        if obs_cdata:
            lat = obs_cdata['points'][0]['lat']
            lon = obs_cdata['points'][0]['lon']

            models = [obs, model]  # [model for model in MODELS]
            if DEBUG: print('SHOW MODIS EVAL TS"""""', obs_cdata, lat, lon)
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
 
        return dash.no_update, False  # PreventUpdate

    @app.callback(
        [Output('ts-eval-modal', 'children'),
         Output('ts-eval-modal', 'is_open')],
        [Input('graph-eval-aeronet', 'clickData')],
        [State('eval-date-picker', 'start_date'),
         State('eval-date-picker', 'end_date'),
         State('obs-dropdown', 'value')],
        prevent_initial_call=True
    )
    def show_eval_aeronet_timeseries(cdata, start_date, end_date, obs):
        """ Retrieve AERONET evaluation timeseries according to station selected """
        from tools import get_eval_timeseries
        print(start_date, end_date, obs, cdata)
        if cdata:
            idx = cdata['points'][0]['pointIndex']
            if idx != 0:
                name = cdata['points'][0]['customdata']
                figure = get_eval_timeseries(obs, start_date, end_date, DEFAULT_VAR, idx, name)
                mb = MODEBAR_LAYOUT_TS
                figure.update_layout(mb)
                if DEBUG: print('SHOW AERONET EVAL TS"""""', obs, idx, name)
                return dbc.ModalBody(
                    dcc.Graph(
                        id='timeseries-eval-modal',
                        figure=figure,
                        config=MODEBAR_CONFIG_TS
                    )
                ), True

        raise PreventUpdate


    @app.callback(
        Output('graph-eval-aeronet', 'figure'),
        [Input('eval-date-picker', 'start_date'),
         Input('eval-date-picker', 'end_date')],
        [State('obs-dropdown', 'value'),
         State('graph-eval-aeronet', 'relayoutData')],
        prevent_initial_call=True)
    def update_eval_aeronet(sdate, edate, obs, relayoutdata):
        """ Update AERONET evaluation figure according to all parameters """
        from tools import get_figure
        from tools import get_obs1d
        if DEBUG: print('SERVER: calling figure from EVAL picker callback')
        if DEBUG: print('SERVER: SDATE' + str(sdate))

        if sdate is not None:
            sdate = sdate.split()[0]
            try:
                sdate = dt.strptime(
                    sdate, "%Y-%m-%d").strftime("%Y%m%d")
            except:
                pass
            if DEBUG: print('SERVER: callback start_date {}'.format(sdate))
        else:
            sdate = end_date

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

        fig = get_figure(model=None, var=DEFAULT_VAR)
        fig.add_trace(get_obs1d(sdate, edate, obs, DEFAULT_VAR))
        fig.update_layout(MODEBAR_LAYOUT)

        if fig and relayoutdata:
            relayoutdata = {k: relayoutdata[k]
                            for k in relayoutdata
                            if k not in ('mapbox._derived',)}
            fig.layout.update(relayoutdata)

        return fig


    @app.callback(
       [Output('graph-eval-modis-obs', 'figure'),
        Output('graph-eval-modis-mod', 'figure')],
       [Input('eval-date-picker', 'date'),
        Input('obs-mod-dropdown', 'value')],
       [State('obs-dropdown', 'value'),
        State('graph-eval-modis-obs', 'relayoutData'),
        State('graph-eval-modis-mod', 'relayoutData')],
        prevent_initial_call=True)
    def update_eval_modis(date, mod, obs, relayoutdata_obs, relayoutdata_mod):
        """ Update MODIS evaluation figure according to all parameters """
        from tools import get_figure
        if DEBUG: print('SERVER: calling figure from EVAL picker callback')
        # if DEBUG: print('SERVER: interval ' + str(n))

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

        fig_mod = get_figure(model=mod, var=DEFAULT_VAR, selected_date=date, tstep=0, hour=12)
        fig_mod.update_layout(MODEBAR_LAYOUT)
        center = fig_mod['layout']['mapbox']['center']
        fig_obs = get_figure(model=obs, var=DEFAULT_VAR, selected_date=date, tstep=2, center=center)
        fig_obs.update_layout(MODEBAR_LAYOUT)

        if fig_obs and relayoutdata_obs:
            relayoutdata_obs = {k: relayoutdata_obs[k]
                            for k in relayoutdata_obs
                            if k not in ('mapbox._derived',)}
            fig_obs.layout.update(relayoutdata_obs)

        if fig_mod and relayoutdata_mod:
            relayoutdata_mod = {k: relayoutdata_mod[k]
                            for k in relayoutdata_mod
                            if k not in ('mapbox._derived',)}
            fig_mod.layout.update(relayoutdata_mod)

        return fig_obs, fig_mod


    @app.callback(
        [Output('eval-date', 'children'),
         Output('eval-graph', 'children'),
         Output('obs-dropdown', 'value'),
         Output('obs-mod-dropdown-span', 'style')],
        [Input('obs-dropdown', 'value')],
         prevent_initial_call=True)
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
                end_date=end_date,
                updatemode='bothdates',
            )]

            eval_graph = [dbc.Spinner(
                get_graph(
                    gid='graph-eval-aeronet',
                    figure=get_figure(),
                    ))]

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
                    selected_date=end_date, tstep=0)
            center = fig_mod['layout']['mapbox']['center']
            fig_obs = get_figure(model=obs, var=DEFAULT_VAR,
                    selected_date=end_date, tstep=2, center=center)
            graph_obs, graph_mod = [
                    dbc.Spinner(
                        get_graph(
                            gid='graph-eval-modis-obs',
                            figure=fig_obs,
                            )
                        ),
                    dbc.Spinner(
                        get_graph(
                            gid='graph-eval-modis-mod',
                            figure=fig_mod,
                            )
                        )
                    ]
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

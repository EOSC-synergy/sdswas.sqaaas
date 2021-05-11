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

from tools import get_eval_timeseries
from tools import get_timeseries
from tools import get_was_figure
from tools import get_figure
from tools import get_obs1d
from tools import start_date
from tools import end_date
from utils import calc_matrix
from utils import get_graph

from tabs.evaluation import tab_evaluation
from tabs.evaluation import STATS

from datetime import datetime as dt
import pandas as pd
import os.path


SCORES = list(STATS.keys())


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
        Output('evaluation-tab', 'children'),
        [Input('nrt-evaluation', 'n_clicks'),
         Input('scores-evaluation', 'n_clicks')],
    )
    def render_evaluation_tab(nrtbutton, scoresbutton):
        """ Function rendering requested tab """
        ctx = dash.callback_context

        if not ctx.triggered:
            raise PreventUpdate
        else:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if button_id == "nrt-evaluation" and nrtbutton:
            return tab_evaluation('nrt')
        elif button_id == "scores-evaluation" and scoresbutton:
            return tab_evaluation('scores')

        raise PreventUpdate


    @app.callback(
        extend_l([[Output('scores-table-{}'.format(score), 'columns'),
           Output('scores-table-{}'.format(score), 'data')]
            for score in SCORES]),
        [Input('obs-models-dropdown', 'value'),
         Input('obs-statistics-dropdown', 'value'),
         Input('obs-network-dropdown', 'value'),
         Input('obs-timescale-dropdown', 'value'),
         Input('obs-selection-dropdown', 'value'),
         Input('scores-apply', 'n_clicks'),
        *[Input('scores-table-{}'.format(score), 'active_cell')
            for score in SCORES]],
        extend_l([[State('scores-table-{}'.format(score), 'columns'),
           State('scores-table-{}'.format(score), 'data')]
            for score in SCORES]),
    )
    def scores_tables_retrieve(models, stat, network, timescale, selection, n, *tables):
        """ Read scores tables and show data """

        areas = ['Mediterranean', 'Middle_East', 'Sahel/Sahara', 'Total']

        if not n:
            raise PreventUpdate

        active_cells = list(tables[:len(SCORES)])
        tables = list(tables[len(SCORES):])

        if isinstance(models, str):
            models = [models]

        if isinstance(stat, str):
            stat = [stat]

        models = ['station'] + models

        print("@@@@@@@@@@@", models, stat, network, timescale, selection, n)
        filedir = OBS[network]['path']

        stat_idxs = [SCORES.index(st) for st in stat]

        for table_idx in range(int(len(tables)/2)):
            obj_idx = table_idx * 2
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
                df = pd.read_hdf(filepath, tab_name)  # .round(decimals=2).fillna('-')
                # replace "tables" columns
                tables[obj_idx] = [{'name': i in MODELS and
                    [SCORES[table_idx].upper(), MODELS[i]['name']] or
                    [SCORES[table_idx].upper(), ''], 'id': i} for
                    i in models]
                # replace "tables" data
                if curr_active_cell is not None:
                    print("ACTIVE", curr_active_cell)
                    curr_data = tables[obj_idx+1]
                    if not curr_data:
                        continue
                    row_number = curr_active_cell['row']
                    # 1st case:
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
                            print("'''", curr_data)
                            print("---", foll_area)
                            foll_idx = curr_data.index([row for row in curr_data if row['station'] == foll_area][0])
                            tables[obj_idx+1] = [table_row for table_row in curr_data if curr_data.index(table_row) <= row_number] +  [table_row for table_row in curr_data if curr_data.index(table_row) >= foll_idx]

                else:
                    tables[obj_idx+1] = df.loc[df['station'].isin(areas), models].to_dict('records')

            else:
                tables[obj_idx] = []
                tables[obj_idx+1] = []

        # print(columns, data)
        return tables


    @app.callback(
        [Output('ts-eval-modal', 'children'),
         Output('ts-eval-modal', 'is_open')],
        [Input('eval-date-picker', 'start_date'),
         Input('eval-date-picker', 'end_date'),
         Input('obs-dropdown', 'value'),
         Input('graph-eval', 'clickData'),
         Input('graph-eval', 'id')],
    )
    def show_eval_timeseries(start_date, end_date, obs, cdata, element):
        """ Retrieve evaluation timeseries according to station selected """
        print(start_date, end_date, obs, cdata, element)
        if cdata:
            idx = cdata['points'][0]['pointIndex']
            if idx != 0:
                name = cdata['points'][0]['customdata']

                if DEBUG: print('SHOW EVAL TS"""""', obs, idx, name)
                return dbc.ModalBody(
                    dcc.Graph(
                        id='timeseries-eval-modal',
                        figure=get_eval_timeseries(obs, start_date, end_date, DEFAULT_VAR, idx, name),
                    )
                ), True

        raise PreventUpdate


    @app.callback(
        Output('graph-eval', 'figure'),
        [Input('eval-date-picker', 'start_date'),
         Input('eval-date-picker', 'end_date'),
         Input('obs-dropdown', 'value')],
        [State('graph-eval', 'relayoutData')])
    def update_eval(sdate, edate, obs, relayoutdata):
        """ Update evaluation figure according to all parameters """
        if DEBUG: print('SERVER: calling figure from EVAL picker callback')
        # if DEBUG: print('SERVER: interval ' + str(n))

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
        if obs == 'aeronet':
            fig.add_trace(get_obs1d(sdate, edate, obs, DEFAULT_VAR))
        elif obs == 'modis':
            fig = get_figure(model=obs, var=DEFAULT_VAR, selected_date=sdate)

        if fig and relayoutdata:
            relayoutdata = {k: relayoutdata[k]
                            for k in relayoutdata
                            if k not in ('mapbox._derived',)}
            fig.layout.update(relayoutdata)

        return fig

""" TAB OBSERVATIONS """
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

from utils import calc_matrix
from utils import get_graph

from tabs.observations import tab_observations
# from tabs.evaluation import STATS

from datetime import datetime as dt
import pandas as pd
import os.path
import math


start_date = DATES['start_date']
end_date = DATES['end_date']


def register_callbacks(app):
    """ Registering callbacks """

    @app.callback(
        [Output('observations-tab', 'children'),
         Output('rgb', 'style'),
         Output('aod', 'style'),
         Output('visibility', 'style')],
        [Input('rgb', 'n_clicks'),
         Input('aod', 'n_clicks'),
         Input('visibility', 'n_clicks')],
    )
    def render_observations_tab(rgb_button, aod_button, vis_button):
        """ Function rendering requested tab """
        ctx = dash.callback_context

        bold = { 'font-weight': 'bold' }
        norm = { 'font-weight': 'normal' }

        if ctx.triggered:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]

            if button_id == "rgb" and rgb_button:
                return tab_observations('rgb'), bold, norm, norm
            elif button_id == "aod" and aod_button:
                return tab_observations('aod'), norm, bold, norm
            elif button_id == "visibility" and vis_button:
                return tab_observations('visibility'), norm, norm, bold

        return dash.no_update, bold, norm, norm
        #raise PreventUpdate

    @app.callback(
    Output('aod-image', 'src'),
    [Input('obs-aod-date-picker', 'date'),
     Input('obs-aod-slider-graph', 'value')],
    )
    def update_aod_image_src(date, tstep):

        path_tpl = 'metoffice/{date}/MSG_{date}{tstep:02}00_AOD_444x278.gif'

        try:
            date = dt.strptime(date, '%Y-%m-%d').strftime('%Y%m%d')
        except:
            pass
        path = path_tpl.format(date=date, tstep=tstep)
        # print('......', path)
        return app.get_asset_url(path)

    # start/stop animation
    @app.callback(
        [Output('obs-aod-slider-interval', 'disabled'),
         Output('obs-aod-slider-interval', 'n_intervals')],
        [Input('btn-obs-aod-play', 'n_clicks')],
        [State('obs-aod-slider-interval', 'disabled'),
         State('obs-aod-slider-graph', 'value')],
        prevent_initial_call=True
    )
    def start_stop_obs_aod__autoslider(n, disabled, value):
        """ Play/Pause map animation """
        if DEBUG: print("VALUE", value)
        if not value:
            value = 0
        if n:
            return not disabled, int(value)
        return disabled, int(value)


    @app.callback(
        Output('obs-aod-slider-graph', 'value'),
        [Input('obs-aod-slider-interval', 'n_intervals')],
        prevent_initial_call=True
        )
    def update_obs_aod_slider(n):
        """ Update slider value according to the number of intervals """
        if DEBUG: print('SERVER: updating slider-graph ' + str(n))
        if not n:
            return 0
        if n >= 24:
            tstep = int(round(24*math.modf(n/24)[0], 0))
        else:
            tstep = int(n)
        if DEBUG: print('SERVER: updating slider-graph ' + str(tstep))
        return tstep


    @app.callback(
    [Output('rgb-image', 'src'),
     Output('btn-fulldisc', 'active'),
     Output('btn-middleeast', 'active')],
    [Input('btn-fulldisc', 'n_clicks'),
     Input('btn-middleeast', 'n_clicks'),
     Input('obs-date-picker', 'date'),
     Input('obs-slider-graph', 'value')],
    [State('btn-fulldisc', 'active'),
     State('btn-middleeast', 'active')],
     #prevent_initial_call=True
    )
    def update_image_src(btn_fulldisc, btn_middleeast, date, tstep, btn_fulldisc_active, btn_middleeast_active):

        if DEBUG:
            print('BUTTONS', date, tstep, btn_fulldisc_active, btn_middleeast_active)
        ctx = dash.callback_context
        if ctx.triggered:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        else:
            button_id = None
        if button_id not in ('btn-fulldisc', 'btn-middleeast'):
            if btn_middleeast_active:
                button_id = 'btn-middleeast'
            elif btn_fulldisc_active:
                button_id = 'btn-fulldisc'

        if DEBUG: print('BUTTONS', button_id)

        if button_id == 'btn-middleeast':
            path_tpl = 'eumetsat/MiddleEast/{date}/MET8_RGBDust_MiddleEast_{date}{tstep:02d}00.gif'
            btn_fulldisc_active = False
            btn_middleeast_active = True
        elif button_id == 'btn-fulldisc':
            path_tpl = 'eumetsat/FullDiscHD/{date}/FRAME_OIS_RGB-dust-all_{date}{tstep:02d}00.gif'
            btn_fulldisc_active = True
            btn_middleeast_active = False

        try:
            date = dt.strptime(date, '%Y-%m-%d').strftime('%Y%m%d')
        except:
            pass
        path = path_tpl.format(date=date, tstep=tstep)
        print('......', path)
        return app.get_asset_url(path), btn_fulldisc_active, btn_middleeast_active


    # start/stop animation
    @app.callback(
        [Output('obs-slider-interval', 'disabled'),
         Output('obs-slider-interval', 'n_intervals')],
        [Input('btn-obs-play', 'n_clicks')],
        [State('obs-slider-interval', 'disabled'),
         State('obs-slider-graph', 'value')],
        prevent_initial_call=True
    )
    def start_stop_obs_autoslider(n, disabled, value):
        """ Play/Pause map animation """
        if DEBUG: print("VALUE", value)
        if not value:
            value = 0
        if n:
            return not disabled, int(value)
        return disabled, int(value)


    @app.callback(
        Output('obs-slider-graph', 'value'),
        [Input('obs-slider-interval', 'n_intervals')],
        prevent_initial_call=True
        )
    def update_obs_slider(n):
        """ Update slider value according to the number of intervals """
        if DEBUG: print('SERVER: updating slider-graph ' + str(n))
        if not n:
            return 0
        if n >= 24:
            tstep = int(round(24*math.modf(n/24)[0], 0))
        else:
            tstep = int(n)
        if DEBUG: print('SERVER: updating slider-graph ' + str(tstep))
        return tstep

    @app.callback(
        Output('obs-vis-graph', 'children'),
        [Input('obs-vis-date-picker', 'date'),
         Input('obs-vis-slider-graph', 'value')]
    )
    def update_vis_figure(date, tstep):
        from tools import get_vis_figure
        if date is not None:
            date = date.split(' ')[0]
            try:
                date = dt.strptime(
                    date, "%Y-%m-%d").strftime("%Y%m%d")
            except:
                pass
        else:
            date = end_date

        if DEBUG: print('SERVER: VIS callback date {}, tstep {}'.format(date, tstep))
        return get_graph(index='vis-graph', figure=get_vis_figure(tstep=tstep, selected_date=date))

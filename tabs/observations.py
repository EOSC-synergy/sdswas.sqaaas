import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from data_handler import DEFAULT_VAR
from data_handler import DEFAULT_MODEL
from data_handler import FREQ
from data_handler import VARS
from data_handler import MODELS
from data_handler import STYLES
from tools import get_figure

from datetime import datetime as dt

start_date = "20201001"
end_date = "20201231"


eval_time_series = dbc.Spinner(
    id='loading-ts-eval-modal',
    fullscreen=True,
    fullscreen_style={'opacity': '0.5'},
    children=[
        html.Div(
        id='open-eval-timeseries',
        children=[
            dbc.Modal([
                dbc.ModalBody(
                    dcc.Graph(
                        id='timeseries-eval-modal',
                        figure={},
                    )
                )],
                id='ts-eval-modal',
                size='xl',
                centered=True,
            )
        ],
        style={'display': 'none'},
    )],
)


tab_observations = dcc.Tab(label='Observations',
    value='observations-tab',
    className='horizontal-menu',
    children=[]
)


def sidebar_observations():
    return []

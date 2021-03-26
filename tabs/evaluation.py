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


tab_evaluation = dcc.Tab(label='Evaluation',
    value='evaluation-tab',
    className='horizontal-menu',
    children=[
        html.Span(
            dcc.DatePickerRange(
                id='eval-date-picker',
                min_date_allowed=dt.strptime(start_date, "%Y%m%d"),
                max_date_allowed=dt.strptime(end_date, "%Y%m%d"),
                initial_visible_month=dt.strptime(end_date, "%Y%m%d"),
                display_format='DD MMM YYYY',
                end_date=end_date,
            ),
            className="linetool",
        ),
        html.Span(
            dcc.Dropdown(
                id='obs-dropdown',
                options=[{'label': 'Aeronet v3 lev15',
                        'value': 'aeronet'}],
                placeholder='Select observation network',
                # clearable=False,
                searchable=False
            ),
            className="linetool",
        ),
        html.Div(
            dcc.Graph(
                id='graph-eval',
                figure=get_figure(),
            ),
        ),
        eval_time_series,
    ]
)


def sidebar_evaluation():
    return [html.Div([
        html.Label("Variable"),
        dcc.Dropdown(
            id='variable-dropdown-evaluation',
            options=[{'label': VARS[variable]['name'],
                      'value': variable} for variable in VARS],
            value=DEFAULT_VAR,
            clearable=False,
            searchable=False,
            optionHeight=70,
            disabled=True,
        )],
        className="sidebar-first-item",
        style={ 'background-color': '#F1B545' },
    ),
    html.Div([
        html.Label("Near-real-time comparison"),
        ],
        className="sidebar-item",
    ),
    html.Div([
        html.Label("Evaluation skill scores"),
        ],
        className="sidebar-item",
    ),
]

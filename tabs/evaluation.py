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


def tab_evaluation(window='nrt'):
    nrt_children = [
        html.Span(
            dcc.DatePickerRange(
                id='eval-date-picker',
                min_date_allowed=dt.strptime(start_date, "%Y%m%d"),
                max_date_allowed=dt.strptime(end_date, "%Y%m%d"),
                initial_visible_month=dt.strptime(end_date, "%Y%m%d"),
                display_format='DD MMM YYYY',
                end_date=end_date,
            ),
            style={ 'width': '50%'},
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
            style={ 'width': '50%'},
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

    scores_children = [
        html.H3(
            "Evaluation skill scores"
            ),
        html.P(
            "Bñabñabñsjbkdjbhfkjdbgkjrhegkljhbgklhb",
            ),
        html.Span(
            dcc.Dropdown(
                id='obs-models-dropdown',
                options=[{'label': MODELS[model]['name'],
                          'value': model} for model in MODELS],
                placeholder='Select model',
                # clearable=False,
                searchable=False
            ),
            style={ 'width': '25%'},
            className="linetool",
        ),
        html.Span(
            dcc.Dropdown(
                id='obs-statistics-dropdown',
                options=[
                    {'label': 'BIAS', 'value': 'bias'},
                    {'label': 'CORR', 'value': 'corr'},
                    {'label': 'RMSE', 'value': 'rmse'},
                ],
                placeholder='Select statistic',
                # clearable=False,
                searchable=False
            ),
            style={ 'width': '20%'},
            className="linetool",
        ),
        html.Span(
            dcc.Dropdown(
                id='obs-network-dropdown',
                options=[{'label': 'Aeronet v3 lev15',
                        'value': 'aeronet'}],
                placeholder='Select observation network',
                # clearable=False,
                searchable=False
            ),
            style={ 'width': '25%'},
            className="linetool",
        ),
        html.Span(
            dcc.Dropdown(
                id='obs-timescale-dropdown',
                options=[{'label': 'Monthly',
                        'value': 'monthly'}],
                placeholder='Select observation network',
                value='montly',
                # clearable=False,
                searchable=False
            ),
            style={ 'width': '20%'},
            className="linetool",
        ),
        html.Span(
            dcc.Dropdown(
                id='obs-selection-dropdown',
                options=[
                    {'label': '{} 2020'.format(month),
                     'value': '{} 2020'.format(month)}
                     for month in ['Oct', 'Nov', 'Dec']
                     ],
                placeholder='Select observation network',
                value='montly',
                # clearable=False,
                searchable=False
            ),
            style={ 'width': '25%'},
            className="linetool",
        ),

    ]

    windows = {
        'nrt': nrt_children,
        'scores': scores_children,
    }
    
    return dcc.Tab(label='Evaluation',
        id='evaluation-tab',
        value='evaluation-tab',
        className='horizontal-menu',
        children=windows[window],
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
        # html.Label("Near-real-time comparison"),
        dbc.Button("Near-real-time comparison",
            color="link",
            id='nrt-evaluation'
        )],
        className="sidebar-item",
    ),
    html.Div([
        # html.Label("Evaluation skill scores"),
        dbc.Button("Evaluation skill scores",
            color="link",
            id='scores-evaluation'
        )],
        className="sidebar-item",
    ),
]

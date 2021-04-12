import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_table
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
            html.P(
                "Near-real-time Comparison"
                ),
            className="description-title"
        ),
        html.Span(
            html.P(
                """Rather than a detailed validation of the dust forecast, the
                model evaluation is an assessment of how the forecast behaves
                relative to a few key observations that are available in
                near-real-time. This allows the modelling groups and the end
                users to have a quick overview of the quality of the
                forecast.""",
                ),
            className="description-body"
        ),
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
        html.Span(
            html.P(
                "Evaluation skill scores"
                ),
            className="description-title"
        ),
        html.Span(
            html.P(
                """An important step in dust forecasting is the evaluation of
                the results that have been generated. This process consists of
                the comparison of the model results to multiple kinds of
                observations and is aimed to facilitate the understanding of
                the model capabilities, limitations, and appropriateness for
                the purpose for which it was designed.""",
                ),
            className="description-body"
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
            style={ 'width': '12rem'},
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
            style={ 'width': '10rem' },
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
            style={ 'width': '10rem'},
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
            style={ 'width': '10rem'},
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
            style={ 'width': '10rem'},
            className="linetool",
        ),
        html.Span(
            html.Button('APPLY', id='scores-apply', n_clicks=0),
            className="linetool",
        ),
        html.Div(
            dash_table.DataTable(
                id='scores-table',
                columns=[],  #get_scores_table(),
                data=[],
            ),
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

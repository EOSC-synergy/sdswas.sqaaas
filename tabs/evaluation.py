import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import dash_table
from data_handler import DEFAULT_VAR
from data_handler import DEFAULT_MODEL
from data_handler import FREQ
from data_handler import VARS
from data_handler import MODELS
from data_handler import OBS
from data_handler import STYLES
from data_handler import DATES
from data_handler import STATS

from datetime import datetime as dt

start_date = DATES['start_date']
end_date = DATES['end_date']

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
                is_open=False,
            ),
            dbc.Modal([
                dbc.ModalBody(
                    dcc.Graph(
                        id='timeseries-eval-modis-modal',
                        figure={},
                    )
                )],
                id='ts-eval-modis-modal',
                size='xl',
                centered=True,
                is_open=False,
            )
        ],),
    ],
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
            dcc.Dropdown(
                id='obs-dropdown',
                options=[{'label': OBS[obs]['name'],
                          'value': obs} for obs in OBS],
                placeholder='Select observation network',
                # clearable=False,
                searchable=False
            ),
            className="linetool",
        ),
        html.Span(
            dcc.Dropdown(
                id='obs-mod-dropdown',
                options=[{'label': MODELS[model]['name'],
                          'value': model} for model in MODELS],
                placeholder='Select model',
                # clearable=False,
                searchable=False,
                value='median',
                style={ 'display': 'none' },
            ),
            className="linetool",
        ),
        html.Span(
            id='eval-date',
            children=[],
            className="linetool",
        ),
        html.Div(
            id='eval-graph',
            children=[],
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
                id='obs-network-dropdown',
                options=[{'label': OBS[obs]['name'],
                          'value': obs} for obs in OBS],
                placeholder='Select observation network',
                # clearable=False,
                searchable=False
            ),
            style={ 'width': '12rem' },
            className="linetool",
        ),
        html.Span(
            dcc.Dropdown(
                id='obs-models-dropdown',
                options=[{'label': MODELS[model]['name'],
                          'value': model} for model in MODELS],
                placeholder='Select model',
                # clearable=False,
                searchable=False,
                multi=True,
            ),
            style={ 'width': '12rem' },
            className="linetool",
        ),
        html.Span(
            dcc.Dropdown(
                id='obs-statistics-dropdown',
                options=[
                    {'label': v, 'value': l} for l, v in STATS.items()
                ],
                placeholder='Select statistic',
                # clearable=False,
                searchable=False,
                multi=True,
            ),
            style={ 'width': '14rem' },
            className="linetool",
        ),
        html.Span(
            dcc.Dropdown(
                id='obs-timescale-dropdown',
                options=[
                    {'label': 'Monthly', 'value': 'monthly'},
                    {'label': 'Seasonal', 'value': 'seasonal'},
                    {'label': 'Annual', 'value': 'annual'},
                ],
                placeholder='Select timescale',
                value='montly',
                # clearable=False,
                searchable=False
            ),
            style={ 'width': '8rem' },
            className="linetool",
        ),
        html.Span(
            dcc.Dropdown(
                id='obs-selection-dropdown',
                options=[
#                     {'label': '{}'.format(dt.strftime(dt.strptime(month, "%Y%m"), "%B %Y")),
#                      'value': '{}'.format(month)}
#                      for month in ['202010', '202011', '202012']
                ],
                placeholder='Select month',
                # value='montly',
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
        html.Div([
            dash_table.DataTable(
                id='modis-scores-table',
                columns=[],
                data=[],
                style_cell={
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'textAlign': 'center',
                    'font-family': '"Roboto", sans-serif',
                    "fontWeight": "bold",
                },
                style_header={
                    'backgroundColor': '#2B383E',
                    'fontWeight': 'bold',
                    'color': '#FFFFFF',
                    'textAlign': 'center',
                },
                style_header_conditional=[
                    {
                        'if': {'header_index': 0},
                        'backgroundColor': '#F1B545',
                        'color': '#2B383E',
                    },
                ],
                merge_duplicate_headers=True,
            )] + [
            dash_table.DataTable(
                id='aeronet-scores-table-{}'.format(score),
                columns=[],  #get_scores_table(),
                data=[],
                #fixed_rows={'headers': True},
                style_cell={
                    'whiteSpace': 'normal',
                    'height': 'auto',
                    'textAlign': 'center',
                    'font-family': '"Roboto", sans-serif',
                },
                style_data_conditional=[
                    {
                        'if': {'column_id': 'station'},
                        'textAlign': 'left',
                        'padding': '0.1rem 1rem',
                    },
                    {
                        "if": {
                            "state": "selected"
                            },
                        "backgroundColor": "inherit !important",
                        "border": "inherit !important",
                    },
                    {
                        "if": {
                            'filter_query': '{station} = "Mediterranean" || {station} = "Middle_East" || {station} = "Sahel/Sahara" || {station} = "Total"',
                            },
                        "fontWeight": "bold",
                        'padding': '1rem',
                    },
                    {
                        "if": {
                            'filter_query': '{station} = "Total"',
                            },
                        "backgroundColor": "#F0F1F2",
                    }
                ],
                style_header={
                    'backgroundColor': '#2B383E',
                    'fontWeight': 'bold',
                    'color': '#FFFFFF',
                    'textAlign': 'center',
                },
                style_header_conditional=[
                    {
                        'if': {'header_index': 0},
                        'backgroundColor': '#F1B545',
                        'color': '#2B383E',
                    },
                ],
                merge_duplicate_headers=True,
            ) for score in STATS.keys()
        ],
        style={
                'padding': '1rem 0.1rem 0.1rem 1rem',
                'width': '95%',
              },
        id='eval-tables',
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
    ),
    html.Div([
        dbc.Button("Near-real-time comparison",
            color="link",
            id='nrt-evaluation'
        )],
        className="sidebar-item",
    ),
    html.Div([
        dbc.Button("Evaluation skill scores",
            color="link",
            id='scores-evaluation'
        )],
        className="sidebar-item",
    ),
]

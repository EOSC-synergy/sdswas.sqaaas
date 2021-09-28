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
from data_handler import MODEBAR_CONFIG

from datetime import datetime as dt

start_date = DATES['start_date']
end_date = DATES['end_date']

scores_maps = dbc.Spinner(
    id='loading-scores-map-modal',
    fullscreen=True,
    fullscreen_style={'opacity': '0.5'},
    children=[
        html.Div(
        id='open-scores-map',
        children=[
            dbc.Modal([
                dbc.ModalBody([
                    html.Span([
                        html.Label("Models"),
                        dcc.Dropdown(
                            id='obs-models-dropdown-modal',
                            options=[{'label': MODELS[model]['name'],
                                      'value': model} for model in MODELS],
                            value=DEFAULT_MODEL,
                            clearable=False,
                            searchable=False,
                            className="sidebar-dropdown"
                        ),
                        ],
                        style={ 'width': '12rem' },
                        className="linetool",
                    ),
                    html.Span([
                        html.Label("Statistics"),
                        dcc.Dropdown(
                            id='obs-statistics-dropdown-modal',
                            options=[
                                {'label': v, 'value': l} for l, v in STATS.items() if l != 'totn'
                            ],
                            value='bias',
                            clearable=False,
                            searchable=False,
                            className="sidebar-dropdown"
                        )
                        ],
                        style={ 'width': '10rem' },
                        className="linetool",
                    ),
                    dcc.Graph(
                        id='scores-map-modalbody',
                        figure={},
                        config={"displayModeBar": False}
                    )]
                )],
                id='scores-map-modal',
                size='xl',
                centered=True,
                is_open=False,
            ),
        ],),
    ],
)

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
                "Visual comparison"
                ),
            className="description-title"
        ),
        html.Span(
            html.P(
                """The visual comparison offers a quick overview of the quality of the forecast. Please select among the available dust-related observations in near-real-time.""",
                ),
            className="description-body"
        ),
        html.Div(
            html.Div([
                html.Span([
                    html.Label("Network"),
                    dcc.Dropdown(
                        id='obs-dropdown',
                        options=[{'label': OBS[obs]['name'],
                                  'value': obs} for obs in OBS],
                        placeholder='Select network',
                        clearable=False,
                        searchable=False
                    )],
                    className="linetool",
                ),
                html.Span([
                    html.Label("Model"),
                    dcc.Dropdown(
                        id='obs-mod-dropdown',
                        options=[{'label': MODELS[model]['name'],
                                  'value': model} for model in MODELS],
                        placeholder='Select model',
                        clearable=False,
                        searchable=False,
                        value='median',
                        #style={ 'display': 'none' },
                    )],
                    id="obs-mod-dropdown-span",
                    className="linetool",
                    style={ 'display': 'none' }
                ),
                html.Span(
                    id='eval-date',
                    children=[],
                    className="linetool",
                )],
                className="statistics-inputs",
            ),
            className="eval-statistics-nav"
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
                "Statistics"
                ),
            className="description-title"
        ),
        html.Span(
            html.P([
                """The accuracy of the forecast can be quantified by comparing it to observations and is presented by a set of statistics (skill scores).""",
            html.B("""Here, you can use the selection menu to explore the skill scores results, based on the selected observation dataset."""),
                ]),
            className="description-body"
        ),
        html.Div([
            html.Div([
                html.Span([
                    html.Label("Network"),
                    dcc.Dropdown(
                        id='obs-network-dropdown',
                        options=[{'label': OBS[obs]['name'],
                                  'value': obs} for obs in OBS],
                        placeholder='Select network',
                        clearable=False,
                        searchable=False
                    )],
                    style={ 'width': '12rem' },
                    className="linetool",
                ),
                html.Span([
                    html.Label("Models"),
                    dbc.DropdownMenu(
                        label="Select model",
                        children=[
                            dcc.Checklist(
                                id='obs-models-dropdown',
                                options=[{'label': MODELS[model]['name'],
                                          'value': model} for model in MODELS],
                                #value=[default_model,],
                                className="sidebar-dropdown"
                            )
                        ],
                    ),
                    ],
                    #style={ 'width': '9.5rem' },
                    className="linetool",
                ),
                html.Span([
                    html.Label("Statistics"),
                    dbc.DropdownMenu(
                        label="Select statistics",
                        children=[
                            dcc.Checklist(
                                id='obs-statistics-dropdown',
                                options=[
                                    {'label': v, 'value': l} for l, v in STATS.items()
                                ],
                                #value=[default_model,],
                                className="sidebar-dropdown"
                            )
                        ],
                    ),
                    ],
                    className="linetool",
                ),
                html.Span([
                    html.Label("Timescale"),
                    dcc.Dropdown(
                        id='obs-timescale-dropdown',
                        options=[
                            {'label': 'Monthly', 'value': 'monthly'},
                            {'label': 'Seasonal', 'value': 'seasonal'},
                            {'label': 'Annual', 'value': 'annual'},
                        ],
                        placeholder='Select timescale',
                        value='montly',
                        clearable=False,
                        searchable=False
                    )],
                    style={ 'width': '8rem' },
                    className="linetool",
                ),
                html.Span([
                    html.Label("Selection"),
                    dcc.Dropdown(
                        id='obs-selection-dropdown',
                        options=[
                        ],
                        placeholder='Select month',
                        # value='montly',
                        clearable=False,
                        searchable=False
                    )],
                    style={ 'width': '10rem'},
                    className="linetool",
                )],
                className="statistics-inputs"
            ),
            html.Div([    
                html.Span(
                    html.Button('APPLY', id='scores-apply', n_clicks=0),
                    className="linetool",
                ),
                html.Span(
                    html.Button('VIEW MAP', id='scores-map-apply', n_clicks=0),
                    className="linetool",
                )],
                className="statistics-ctas"
            )],
            className="eval-statistics-nav"
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
                            'filter_query': '{station} = "Mediterranean" || {station} = "Middle East" || {station} = "Sahel/Sahara" || {station} = "Total"',
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
        ] + [ scores_maps ],
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
            options=[{'label': VARS[variable]['name_sidebar'],
                      'value': variable} for variable in VARS],
            value=DEFAULT_VAR,
            clearable=False,
            searchable=False,
            optionHeight=70,
            disabled=True,
        )],
        id='evaluation-variable',
        className="sidebar-first-item",
    ),
    html.Div([
        dbc.Button("Visual comparison",
            color="link",
            id='nrt-evaluation'
        )],
        className="sidebar-item",
    ),
    html.Div([
        dbc.Button("Statistics",
            color="link",
            id='scores-evaluation'
        )],
        className="sidebar-item",
    ),
#     html.Div([
#         dbc.Row([
#           dbc.Col(
#             dbc.Button(
#                 "",
#                 id="info-button",
#             ),
#             width=12,
#             ),
#           ],
#           no_gutters=True,
#           ),
#         dbc.Row([
#             dbc.Col([
#               dbc.Collapse(
#                 dbc.Card(dbc.CardBody(
#                     [
#                         html.Button('USER GUIDE',
#                             id='btn-userguide-download',
#                             n_clicks=0,
#                             className='download-section',
#                             ),
#                         html.H6("Glossary"),
#                         html.P("""
#                             1. Variables: Lorem ipsum dolor sit amet, consectetur adipiscing elit."""),
#                         html.P("""
#                             2. Comparing: Lorem ipsum dolor sit , conssit amet, sit amet, consecte dolor elit."""),
#                         html.P("""
#                             3. User Oriented Products: Lorem ipsum dolor sit amet, consectetur adipiscing elitLorem consectetur adipiscing elit"""),
#                     ],
#                     className="card-text",
#                     )),
#                 id="info-collapse",
#                 is_open=False,
#               ),
#         ],
#         className="collapsible-cards",
#         ),
#     ],
#     className="sidebar-bottom",
#     )
#     ])
]

import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from data_handler import DEFAULT_VAR
from data_handler import DEFAULT_MODEL
from data_handler import FREQ
from data_handler import VARS
from data_handler import MODELS
from data_handler import STYLES

from datetime import datetime as dt

start_date = "20200501"
end_date = "20200713"


sidebar_forecast = [
    html.Div([
        html.Label("Variable"),
        dcc.Dropdown(
            id='variable-dropdown-forecast',
            options=[{'label': VARS[variable]['name'],
                      'value': variable} for variable in VARS],
            value=DEFAULT_VAR,
            clearable=False,
            searchable=False,
            optionHeight=70,
        )],
        className="sidebar-first-item",
        style={ 'background-color': '#F1B545' },
    ),
    html.Details([
        html.Summary("Models"),
        dcc.Checklist(
            id='model-dropdown',
            options=[{'label': MODELS[model]['name'],
                      'value': model} for model in MODELS],
            value=[DEFAULT_MODEL,],
        )],
        className="sidebar-item",
    ),
]

sidebar_evaluation = [
    html.Div([
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

time_slider = html.Div([
                    html.Span(
                        dcc.DatePickerSingle(
                            id='model-date-picker',
                            min_date_allowed=dt.strptime(start_date, "%Y%m%d"),
                            max_date_allowed=dt.strptime(end_date, "%Y%m%d"),
                            initial_visible_month=dt.strptime(end_date, "%Y%m%d"),
                            display_format='DD MMM YYYY',
                            date=end_date,
                            with_portal=True,
                        ),
                        className="timesliderline",
                    ),
                    html.Span(
                        html.Button('\u2023', title='Play/Stop',
                                    id='btn-play', n_clicks=0),
                        className="timesliderline",
                    ),
                    html.Span(
                        dcc.Slider(
                            id='slider-graph',
                            min=0, max=72, step=FREQ, value=0,
                            marks={
                                tstep: '{:d}'.format(tstep)
                                # if tstep%2 == 0 else ''
                                for tstep in range(0, 75, FREQ)
                            },
                            # updatemode='drag',
                        ),
                        className="timesliderline",
                    ),
                    html.Span(
                        dbc.DropdownMenu(
                            id='layout-dropdown',
                            label='Layout',
                            children=[
                                dbc.DropdownMenuItem(STYLES[style], id=style)
                                for style in STYLES],
                            direction="up",
                            #value="open-street-map",
                        ),
                        className="timesliderline",
                    )
                ],
                className="timeslider"
            )

time_series = html.Div(
    id='open-timeseries',
    children=[
        dbc.Spinner([
            dbc.Modal([
                dbc.ModalBody(
                    dcc.Graph(
                        id='timeseries-modal',
                        figure={},
                    ),
                )],
                id='ts-modal',
                size='xl',
                centered=True,
            ),
        ]),
    ],
    style={'display': 'none'},
)

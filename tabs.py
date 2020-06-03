import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from data_handler import DEFAULT_VAR
from data_handler import DEFAULT_MODEL
from data_handler import FREQ
from data_handler import VARS
from data_handler import MODELS

from datetime import datetime as dt

start_date = "20200301"
end_date = "20200416"


sidebar = html.Div([
    html.Span([
        html.Label("Variable"),
        dcc.Dropdown(
            id='variable-dropdown',
            options=[{'label': VARS[variable]['name'],
                      'value': variable} for variable in VARS],
            value=DEFAULT_VAR,
            clearable=False,
            searchable=False
        )],
        className="sidebar-first-item",
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
    html.Span(
        dcc.Dropdown(
            id='obs-dropdown',
            options=[{'label': 'Aeronet v3 lev15',
                      'value': 'aeronet'}],
            placeholder='Select observation network',
            clearable=False,
            searchable=False
        ),
        className="sidebar-item",
    ),
    ],
    className="sidebar",
)

time_slider = html.Div([
                    html.Span(
                        dcc.DatePickerSingle(
                            id='model-date-picker',
                            min_date_allowed=dt.strptime(start_date, "%Y%m%d"),
                            max_date_allowed=dt.strptime(end_date, "%Y%m%d"),
                            initial_visible_month=dt.strptime(end_date, "%Y%m%d"),
                            display_format='DD MMM YYYY',
                            date=end_date,
                        ),
                        className="linetool",
                    ),
                    html.Span(
                        html.Button('\u2023', title='Play/Stop',
                                    id='btn-play', n_clicks=0),
                        className="linetool",
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
                        className="linetool",
                    )],
                    className="timeslider"
            )

time_series = html.Div([
                    # dbc.Button('open', id='open-ts'),
                    dcc.Loading([
                        dbc.Modal([
                            dbc.ModalBody(
                                dcc.Graph(
                                    id='timeseries-modal',
                                    figure=None,
                                ),
                            )],
                            id='ts-modal',
                            size='xl',
                            centered=True,
                        ),
                    ]),
                ])

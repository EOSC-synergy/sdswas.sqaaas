#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Dash Server """

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

from datetime import datetime as dt

from data_handler import STYLES
from data_handler import DATES
from data_handler import DISCLAIMER

start_date = DATES['start_date']
end_date = DATES['end_date']

forecast_days = ('Today', 'Tomorrow')

time_series = html.Div(
    id='open-timeseries',
    children=[
        dbc.Spinner(
            id='loading-ts-modal',
            fullscreen=True,
            fullscreen_style={'opacity': '0.5'},
            show_initially=False,
            children=[
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
                    is_open=False,
                ),
            ],
        )],
    #style={'display': 'none'},
)


layout_view = html.Div([
    html.Span(
        dbc.DropdownMenu(
            id='map-view-dropdown',
            label='VIEW',
            children=[
                dbc.DropdownMenuItem(STYLES[style], id=style)
                for style in STYLES],
            direction="up",
        ),
    )])

layout_layers = html.Div([
    html.Span(
        dbc.DropdownMenu(
            id='map-layers-dropdown',
            label='LAYERS',
            children=[
                dbc.DropdownMenuItem('AIRPORTS', id='airports')
            ],
            direction="up",
        ),
    )])

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
    html.Span(children=[
        html.Button('\u2023', title='Play',
                    id='btn-play', n_clicks=0),
        html.Button('\u25A0', title='Stop',
                    id='btn-stop', n_clicks=0)],
        className="timesliderline",
    ),
    html.Span(
        dcc.Slider(
            id='slider-graph',
            min=0, max=72, step=3, value=0,
            marks={
                tstep: '{:d}'.format(tstep)
                # if tstep%2 == 0 else ''
                for tstep in range(0, 75, 3)
            },
            # updatemode='drag',
        ),
        className="timesliderline",
    ),
    html.Div(DISCLAIMER),
    ],
    className="timeslider"
)


prob_time_slider = html.Div([
    html.Span(
        dcc.DatePickerSingle(
            id='prob-date-picker',
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
        dcc.Slider(
            id='prob-slider-graph',
            min=0, max=1, step=1, value=0,
            marks={
                tstep: forecast_days[tstep]
                for tstep in range(2)
            },
        ),
        className="timesliderline",
    ),
    html.Div(DISCLAIMER),
    ],
    className="timeslider"
)


was_time_slider = html.Div([
    html.Span(
        dcc.DatePickerSingle(
            id='was-date-picker',
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
        dcc.Slider(
            id='was-slider-graph',
            min=1, max=2, step=1, value=1,
            marks={
                tstep: forecast_days[tstep-1]
                for tstep in range(1, 3)
            },
        ),
        className="timesliderline",
    ),
    html.Div(DISCLAIMER),
    ],
    className="timeslider"
)


def tab_forecast(window='models'):
    models_children = [
        dbc.Alert(
            "To ensure a better experience, please note that you cannot select more than 4 models at once.",
            id="alert-models-auto",
            is_open=False,
            duration=6000,
            fade=True,
            color="primary",
            style={ 'overflow': 'auto', 'margin-bottom': 0 }
        ),
        html.Div(
            id='div-collection',
            children=[dbc.Spinner(
            id='loading-graph-collection',
            debounce=10,
            show_initially=False,
            children=[
                dbc.Container(
                    id='graph-collection',
                    children=[],
                    fluid=True,
                    )]
            )],
        ),
        html.Div(
            dcc.Interval(id='slider-interval',
                interval=1500,
                n_intervals=0,
                disabled=True
        )),
        html.Div([
            time_slider,
            layout_view,
            layout_layers,
            ],
            id='layout-dropdown',
            className="layout-dropdown",
        ),
        time_series,
    ]

    was_children = [
        dbc.Alert(
            "To ensure a better experience, please note that you cannot select more than 4 models at once.",
            id="alert-models-auto",
            is_open=False,
            duration=6000,
            fade=True,
            color="primary",
            style={ 'overflow': 'auto', 'margin-bottom': 0 }
        ),
        dbc.Spinner(
            html.Div(
                id='was-graph',
                children=[],
            ),
        ),
        html.Div([
            was_time_slider,
            layout_view,
            layout_layers,
            ],
            id='layout-dropdown',
            className="layout-dropdown",
        ),
    ]

    prob_children = [
        dbc.Alert(
            "To ensure a better experience, please note that you cannot select more than 4 models at once.",
            id="alert-models-auto",
            is_open=False,
            duration=6000,
            fade=True,
            color="primary",
            style={ 'overflow': 'auto', 'margin-bottom': 0 }
        ),
        dbc.Spinner(
            html.Div(
                id='prob-graph',
                children=[],
            )
        ),
        html.Div([
            prob_time_slider,
            layout_view,
            layout_layers,
            ],
            id='layout-dropdown',
            className="layout-dropdown",
        ),
    ]

    windows = {
        'models': models_children,
        'was': was_children,
        'prob': prob_children,
    }
    
    return dcc.Tab(label='Forecast',
        id='forecast-tab',
        value='forecast-tab',
        className='horizontal-menu',
        children=windows[window],
    )


def sidebar_forecast(variables, default_var, models, default_model):
    return [
    html.Div([
        html.Label("Variable"),
        dcc.Dropdown(
            id='variable-dropdown-forecast',
            options=[{'label': variables[variable]['name_sidebar'],
                      'value': variable} for variable in variables],
            value=default_var,
            clearable=False,
            searchable=False,
            optionHeight=50,
        )],
        className="sidebar-first-item",
    ),
    html.Div([
        dbc.Card([
            dbc.CardHeader(html.H2(
                dbc.Button("Models",
                    color="link", id='group-1-toggle'),
            )),
            dbc.Collapse(
                id='collapse-1',
                is_open=True,
                children=[
                    dbc.CardBody([
                        dbc.Checklist(
                            id='model-dropdown',
                            options=[{'label': models[model]['name'],
                                      'value': model} for model in models],
                            value=[default_model,],
                            className="sidebar-dropdown",
                        ),
                        html.Span([
                            html.Button('APPLY', id='models-apply', n_clicks=0),
                        ],
                        )],
                    )
                ]
            )],
        ),
        dbc.Card([
            dbc.CardHeader(html.H2(
                dbc.Button("Probability of exceedance",
                    color="link", id='group-2-toggle'),
            )),
            dbc.Collapse(
                id='collapse-2',
                children=[
                    dbc.CardBody([
                        dcc.RadioItems(
                            id='prob-dropdown',
                            options=[],
                            value=None,
                            className="sidebar-dropdown"
                        ),
                        html.Span([
                            html.Button('APPLY', id='prob-apply', n_clicks=0),
                        ]
                        )]
                    )
                ]
            )],
        ),
        dbc.Card([
            dbc.CardHeader(html.H2(
                dbc.Button("Warning Advisory System",
                    color="link", id='group-3-toggle')
            )),
            dbc.Collapse(
                id='collapse-3',
                children=[
                    dbc.CardBody([
                        dcc.Checklist(
                            id='was-dropdown',
                            options=[{'label': 'BURKINA FASO',
                                      'value': 'burkinafaso'}],
                            value=['burkinafaso',],
                            className="sidebar-dropdown"
                        ),
                        html.Span([
                            html.Button('APPLY', id='was-apply', n_clicks=0),
                        ]
                        )]
                    )
                ]
            )],
        ),
    ],
    className="accordion"
    ),
    html.Div([
        dbc.Row([
          dbc.Col(
            dbc.Button(
                "",
                id="info-button",
            ),
            width=3,
            ),
          dbc.Col(
            dbc.Button(
                "DOWNLOAD",
                id="download-button",
            ),
            width=9,
            ),
          ],
          no_gutters=True,
          ),
        dbc.Row([
            dbc.Col([
              dbc.Collapse(
                dbc.Card(dbc.CardBody(
                    [
                        html.Button('USER GUIDE',
                            id='btn-userguide-download',
                            n_clicks=0,
                            className='download-section',
                            ),
                        html.P("""
                        Please check out the User Guide for more information."""),
                    ],
                    className="card-text",
                    )),
                id="info-collapse",
                is_open=False,
              ),
              dbc.Collapse(
                dbc.Card(dbc.CardBody(
                    [
                        html.Button('PNG FRAME',
                            id='btn-frame-download',
                            n_clicks=0,
                            className='download-section',
                            ),
                        dbc.Spinner(
                                dcc.Download(
                                    id="frame-download",
                                base64=True,
                                )
                            ),
                        html.Button('GIF ANIM',
                            id='btn-anim-download',
                            n_clicks=0,
                            className='download-section',
                            ),
                        dbc.Spinner(
                            dcc.Download(
                                id="anim-download",
                                base64=True,
                                )
                            ),
                        html.Button('NETCDF',
                            id='btn-netcdf-download',
                            n_clicks=0,
                            className='download-section',
                            ),
                        dbc.Spinner(
                            dcc.Download(
                                id="netcdf-download",
                                base64=True,
                                ),
                            ),
                        html.P("""This button allows you to get selected models netCDF files."""),
                        html.P([
                            """To get access to the forecast archive please click """,
                            dcc.Link('here', href="https://earth.bsc.es/thredds/catalog/exp/monarch/a2in/regional/catalog.html"),
                            ]),
                    ],
                    className="card-text",
                    )),
                id="download-collapse",
                is_open=False,
              )
            ]),
        ],
        className="collapsible-cards",
        ),
    ],
    className="sidebar-bottom",
    )
]


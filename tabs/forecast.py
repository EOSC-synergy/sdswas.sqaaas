#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Dash Server """

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

from datetime import datetime as dt

from data_handler import STYLES
from tools import start_date
from tools import end_date


time_series = dbc.Spinner(
    id='loading-ts-modal',
    fullscreen=True,
    fullscreen_style={'opacity': '0.5'},
    children=[
        html.Div(
            id='open-timeseries',
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
                ),
            ],
            style={'display': 'none'},
        )],
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
                tstep: 'Day {:d}'.format(tstep)
                for tstep in range(3)
            },
        ),
        className="timesliderline",
    ),
    ],
    className="timeslider"
)


def tab_forecast(window='models'):
    models_children = [dbc.Spinner(
        id='loading-models-graph-collection',
        fullscreen=True,
        fullscreen_style={'opacity': '0.5'},
        children=[
            html.Div(
                dbc.Container(
                    id='graph-collection',
                    children=[],
                    fluid=True,
            )),
            html.Div(
                dcc.Interval(id='slider-interval',
                    interval=1000,
                    n_intervals=0,
                    disabled=True
            )),
            html.Div(
                time_slider,
            ),
        ]),
        # tabs.progress_bar,
        time_series,
    ]

    was_children = [dbc.Spinner(
        id='loading-was-graph',
        fullscreen=True,
        fullscreen_style={'opacity': '0.5'},
        children=[
            html.Div(
                    id='was-graph',
                    children=[],
            ),
            html.Div(
                was_time_slider,
            ),
        ]),
    ]

    windows = {
        'models': models_children,
        'was': was_children,
        # 'prob': prob_children
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
            options=[{'label': variables[variable]['name'],
                      'value': variable} for variable in variables],
            value=default_var,
            clearable=False,
            searchable=False,
            optionHeight=70,
        )],
        className="sidebar-first-item",
        style={ 'background-color': '#F1B545' },
    ),
    html.Div([
        dbc.Card([
            dbc.CardHeader(html.H2(
                dbc.Button("Models", id='group-1-toggle'),
            )),
            dbc.Collapse(
                id='collapse-1',
                children=[
                    dbc.CardBody(
                        dcc.Checklist(
                            id='model-dropdown',
                            options=[{'label': models[model]['name'],
                                      'value': model} for model in models],
                            value=[default_model,],
                            className="sidebar-dropdown"
                        )
                    )
                ]
            )],
        ),
        html.Div([
            dbc.CardHeader(html.H2(
                dbc.Button("Warning Advisory", id='group-2-toggle'),
            )),
            dbc.Collapse(
                id='collapse-2',
                children=[
                    dbc.CardBody(
                        dcc.Checklist(
                            id='was-dropdown',
                            options=[{'label': 'BURKINA FASO',
                                      'value': 'burkinafaso'}],
                            value=['burkinafaso',],
                            className="sidebar-dropdown"
                        )
                    )
                ]
            )],
        ),
    ],
    className="accordion"
    )
]


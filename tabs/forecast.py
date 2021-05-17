#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Dash Server """

import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html

from datetime import datetime as dt

from data_handler import STYLES
from data_handler import DATES

start_date = DATES['start_date']
end_date = DATES['end_date']


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
                tstep: 'Day {:d}'.format(tstep+1)
                for tstep in range(3)
            },
        ),
        className="timesliderline",
    ),
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
    models_children = [
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
        html.Div([
            time_slider,
            layout_view,
            layout_layers,
            ],
            id='layout-dropdown',
        ),
        time_series,
    ]

    was_children = [
        html.Div(
            id='was-graph',
            children=[],
        ),
        html.Div([
            was_time_slider,
            layout_view,
            ],
            id='layout-dropdown',
        ),
    ]

    prob_children = [
        html.Div(
            id='prob-graph',
            children=[],
        ),
        html.Div([
            prob_time_slider,
            layout_view,
            ],
            id='layout-dropdown',
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
            options=[{'label': variables[variable]['name'],
                      'value': variable} for variable in variables],
            value=default_var,
            clearable=False,
            searchable=False,
            optionHeight=70,
        )],
        className="sidebar-first-item",
        #style={ 'background-color': '#F1B545' },
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
        dbc.Card([
            dbc.CardHeader(html.H2(
                dbc.Button("Probability Maps",
                    color="link", id='group-2-toggle'),
            )),
            dbc.Collapse(
                id='collapse-2',
                children=[
                    dbc.CardBody(
                        dcc.RadioItems(
                            id='prob-dropdown',
                            options=[],
                            value=None,
                            className="sidebar-dropdown"
                        )
                    )
                ]
            )],
        ),
        dbc.Card([
            dbc.CardHeader(html.H2(
                dbc.Button("Warning Advisory",
                    color="link", id='group-3-toggle')
            )),
            dbc.Collapse(
                id='collapse-3',
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


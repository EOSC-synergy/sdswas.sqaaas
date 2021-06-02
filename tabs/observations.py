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

start_date = "20201001"
end_date = "20201231"


def obs_time_slider(div='obs', start=0, end=23, step=1):
    return html.Div([
    html.Span(
        dcc.DatePickerSingle(
            id='{}-date-picker'.format(div),
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
                    id='btn-{}-play'.format(div), n_clicks=0),
        className="timesliderline",
    ),
    html.Span(
        dcc.Slider(
            id='{}-slider-graph'.format(div),
            min=start, max=end, step=step, value=0,
            marks={
                tstep: '{:d}'.format(tstep)
                # if tstep%2 == 0 else ''
                for tstep in range(start, end+1, step)
            },
            # updatemode='drag',
        ),
        className="timesliderline",
    ),
    ],
    className="timeslider"
)

def tab_observations(window='rgb'):
    """ """
    rgb_children = [
        html.Span(
            html.P(
                "EUMETSTAT RGB"
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
        html.Div([
            dbc.Button("HEMISPHERIC",
                id='btn-fulldisc',
                active=True,
            ),
            dbc.Button("MIDDLE EAST",
                id='btn-middleeast',
                active=False,
            ),
            ],
            id='rgb-buttons'
        ),
        html.Div(
            html.Img(
                id='rgb-image',
                )
        ),
        html.Div(
            dcc.Interval(id='obs-slider-interval',
                interval=500,
                n_intervals=0,
                disabled=True
        )),
        html.Div(
            obs_time_slider(div='obs'),
        ),
    ]

    aod_children = [
        html.Span(
            html.P(
                "UK METOFFICE AOD"
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
        html.Div(
            html.Img(
                id='aod-image',
                )
        ),
        html.Div(
            dcc.Interval(id='obs-aod-slider-interval',
                interval=500,
                n_intervals=0,
                disabled=True
        )),
        html.Div(
            obs_time_slider(div='obs-aod'),
        ),
    ]

    visibility_children = [
        html.Span(
            html.P(
                "NOAA Visibility"
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
        html.Div(
            id='vis-graph',
            children=[],
        ),
        html.Div(
            obs_time_slider(div='obs-vis',
                start=0,
                end=23,
                step=6),
        ),
    ]

    windows = {
        'rgb': rgb_children,
        'aod': aod_children,
        'visibility': visibility_children,
    }
    
    return dcc.Tab(label='Observations',
        id='observations-tab',
        value='observations-tab',
        className='horizontal-menu',
        children=windows[window],
    )

def sidebar_observations():
    return [html.Div([
        html.Label("Variable"),
        dcc.Dropdown(
            id='variable-dropdown-observation',
            options=[
                {'label': 'RGB', 'value': 'rgb'},
                {'label': 'AOD', 'value': 'aod'},
                {'label': 'Visibility', 'value': 'visibility'}
            ],
            value='rgb',
            clearable=False,
            searchable=False,
            disabled=True
            # optionHeight=70,
        )],
        className="sidebar-first-item",
    ),
    # html.Label("Column integrated"),
    html.Div([
        dbc.Button("EUMETSAT - RGB",
            color="link",
            id='rgb'
        )],
        className="sidebar-item",
    ),
    html.Div([
        dbc.Button("UK METOFFICE - AOD",
            color="link",
            id='aod'
        )],
        className="sidebar-item",
    ),
    # html.Label("Surface level"),
    html.Div([
        dbc.Button("NOAA - Visibility",
            color="link",
            id='visibility'
        )],
        className="sidebar-item",
    ),
]

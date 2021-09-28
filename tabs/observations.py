import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
from data_handler import DEFAULT_VAR
from data_handler import DEFAULT_MODEL
from data_handler import FREQ
from data_handler import VARS
from data_handler import MODELS
from data_handler import STYLES
from data_handler import DISCLAIMER

from datetime import datetime as dt

start_date = "20201001"
end_date = "20201231"


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

def obs_time_slider(div='obs', start=0, end=23, step=1):

    date_picker = html.Span(
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
    )

    play_button = html.Span(children=[
        html.Button('\u2023', title='Play',
                    id='btn-{}-play'.format(div), n_clicks=0),
        html.Button('\u25A0', title='Stop',
                    id='btn-{}-stop'.format(div), n_clicks=0),
        ],
        className="timesliderline",
    )
    
    slider = html.Span(
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
    )
    if div == 'obs-vis':
        return html.Div([
                date_picker,
                slider,
            ],
            className="timeslider"
        )

    return html.Div([
            date_picker,
            play_button,
            slider,
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
            html.P([
                html.B(
                    """
                    You can explore key observations that can be used to track dust events.
                    """
                    ),
                """ All observations are kindly offered by Partners of the WMO Barcelona Dust Regional Center. RGB is a qualitative satellite product that indicates desert dust in the entire atmospheric column (represented by pink colour).""",
                ]
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
        html.Div([
            html.Img(
                id='rgb-image',
                ),
            html.Div(
                obs_time_slider(div='obs'),
                className="layout-dropdown",
            )],
            className='centered-image',
        ),
        html.Div(
            dcc.Interval(id='obs-slider-interval',
                interval=1000,
                n_intervals=0,
                disabled=True
        )),
    ]

    aod_children = [
        html.Span(
            html.P(
                "UK METOFFICE AOD"
                ),
            className="description-title"
        ),
        html.Span(
            html.P([
                html.B("""You can explore key observations that can be used to track dust events."""),
                """All observations are kindly offered by Partners of the WMO Barcelona Dust Regional Center. AOD is a quantitative measure of the aerosol content in the entire atmospheric column."""]
                ),
            className="description-body"
        ),
        html.Div([
            html.Img(
                id='aod-image',
                ),
            html.Div(
                obs_time_slider(div='obs-aod'),
                className="layout-dropdown",
            )],
            className='centered-image',
        ),
        html.Div(
            dcc.Interval(id='obs-aod-slider-interval',
                interval=1000,
                n_intervals=0,
                disabled=True
        )),
    ]

    visibility_children = [
        html.Span(
            html.P(
                "NOAA Visibility"
                ),
            className="description-title"
        ),
        html.Span(
            html.P([
                html.B("""You can explore key observations that can be used to track dust events."""),
                """All observations are kindly offered by Partners of the WMO Barcelona Dust Regional Center. The reduction of VISIBILITY is an indirect measure of the occurrence of sand and dust storms on the surface.""",
                ]),
            className="description-body"
        ),
        dbc.Spinner(
            html.Div(
                id='obs-vis-graph',
                children=[],
            ),
        ),
        html.Div([
            obs_time_slider(div='obs-vis',
                start=0,
                end=18,
                step=6),
            layout_view,
            # html.Br(),
            # html.Br(),
            # html.Div(html.Span(DISCLAIMER)),
            ],
            className="layout-dropdown",
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
        id='observations-variable',
        className="sidebar-first-item",
    ),
    html.Label("Column integrated"),
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
    html.Label("Surface level"),
    html.Div([
        dbc.Button("NOAA - Visibility",
            color="link",
            id='visibility'
        )],
        className="sidebar-item",
    ),
]

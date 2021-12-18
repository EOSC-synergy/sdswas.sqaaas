from dash import dcc
import dash_bootstrap_components as dbc
from dash import html
from data_handler import DEFAULT_VAR
from data_handler import DEFAULT_MODEL
from data_handler import FREQ
from data_handler import VARS
from data_handler import MODELS
from data_handler import DATES
from data_handler import STYLES
from data_handler import DISCLAIMER_NO_FORECAST
# from tabs.forecast import layout_view

from datetime import datetime as dt
from datetime import timedelta

start_date = DATES["start_date"]
end_date = DATES['end_date'] or dt.now().strftime("%Y%m%d")
aod_end_date = '20210318'


layout_view = html.Div([
    html.Span(
        dbc.DropdownMenu(
            id='map-view-dropdown',
            label='VIEW',
            children=[
                dbc.DropdownMenuItem(
                    STYLES[style]['name'],
                    id=dict(
                        tag='vis-view-style',
                        index=style
                    ),
                    active=active
                )
                for style, active in zip(STYLES, [True if i == 'carto-positron'
                    else False for i in STYLES])
                ],
            direction="up",
        ),
    )])


def obs_time_slider(div='obs', start=0, end=23, step=1):

    if div == 'obs-aod':
        edate = aod_end_date
    else:
        edate = end_date

    date_picker = html.Span(
        dcc.DatePickerSingle(
            id='{}-date-picker'.format(div),
            min_date_allowed=dt.strptime(start_date, "%Y%m%d"),
            max_date_allowed=dt.strptime(edate, "%Y%m%d"),
            initial_visible_month=dt.strptime(edate, "%Y%m%d"),
            display_format='DD MMM YYYY',
            # date=(dt.strptime(edate, "%Y%m%d") - timedelta(days=1)).strftime("%Y%m%d"),
            date=dt.strptime(edate, "%Y%m%d").strftime("%Y%m%d"),
            with_portal=True,
        ),
        className="timesliderline",
    )

    play_button = html.Span(children=[
        html.Button(title='Play',
                    id='btn-{}-play'.format(div), n_clicks=0,
                    className='fa fa-play'),
        html.Button(title='Stop',
                    id='btn-{}-stop'.format(div), n_clicks=0,
                    className='fa fa-pause'),
        ],
        className="timesliderline anim-buttons",
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
                src='./assets/eumetsat/FullDiscHD/archive/{date}/FRAME_OIS_RGB-dust-all_{date}{tstep:02d}00.gif'.format(date=end_date, tstep=0),
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
                "MetOffice AOD"
                ),
            className="description-title"
        ),
        html.Span(
            html.P([
                html.B("""You can explore key observations that can be used to track dust events. """),
                """All observations are kindly offered by Partners of the WMO Barcelona Dust Regional Center. AOD is a quantitative measure of the aerosol content in the entire atmospheric column."""]
                ),
            className="description-body"
        ),
        html.Div([
            html.Img(
                id='aod-image',
                src='./assets/metoffice/{date}/MSG_{date}{tstep:02}00_AOD_444x278.gif'.format(date=aod_end_date, tstep=0),
                alt='MetOffice AOD - NOT AVAILABLE',
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
                "Visibility"
                ),
            className="description-title"
        ),
        html.Span(
            html.P([
                html.B("""You can explore key observations that can be used to track dust events. """),
                """All observations are kindly offered by Partners of the WMO Barcelona Dust Regional Center. The reduction of VISIBILITY is an indirect measure of the occurrence of sand and dust storms on the surface.""",
                ]),
            className="description-body"
        ),
        html.Div(
            id='obs-vis-graph',
            children=[],
        ),
#        dbc.Spinner(
#        ),
        html.Div([
            obs_time_slider(div='obs-vis',
                start=0,
                end=18,
                step=6),
            #layout_view,
            html.Br(),
            html.Br(),
            html.Div(DISCLAIMER_NO_FORECAST,
                className='disclaimer'),
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
        dbc.Button("EUMETSAT RGB",
            color="link",
            id='rgb'
        )],
        className="sidebar-item",
    ),
    html.Div([
        dbc.Button("MetOffice AOD",
            color="link",
            id='aod'
        )],
        className="sidebar-item",
    ),
    html.Label("Surface"),
    html.Div([
        dbc.Button("Visibility",
            color="link",
            id='visibility'
        )],
        className="sidebar-item",
    ),
]

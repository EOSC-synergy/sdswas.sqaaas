import matplotlib as mpl
from matplotlib import cm
import numpy as np
import math

TIMES = {
    'animation': 900,
    'transition': 500,
    'slider_transition': 500
}


def magnitude(num):
    """ Calculate magnitude """
    return int(math.floor(math.log10(num)))


def normalize_vals(vals, valsmin, valsmax, rnd=2):
    """ Normalize values to 0-1 scale """
    vals = np.array(vals)
    if rnd < 2:
        rnd = 2
    return np.around((vals-valsmin)/(valsmax-valsmin), rnd)


def get_colorscale(bounds, colormap, discrete=True):
    """ Create colorscale """
    bounds = np.array(bounds).astype('float32')
    magn = magnitude(bounds[-1])
    n_bounds = normalize_vals(bounds, bounds[0], bounds[-1], magn)
    norm = mpl.colors.BoundaryNorm(bounds, len(bounds)-1, clip=True)
    s_map = cm.ScalarMappable(norm=norm, cmap=colormap)

    colorscale = [[idx,
                   'rgba' + str(s_map.to_rgba(val,
                                              alpha=True,
                                              bytes=True,
                                              norm=True))]
                  for idx, val in zip(n_bounds, bounds)]

    if discrete:
        for item in colorscale.copy():
            if colorscale.index(item) < len(colorscale)-2:
                colorscale.insert(colorscale.index(item)+1,
                                  [colorscale[colorscale.index(item)+1][0],
                                   colorscale[colorscale.index(item)][1]])

    return colorscale


def get_animation_buttons():
    """ Returns play and stop buttons """
    return dict(
        type="buttons",
        direction="left",
        buttons=[
            dict(label="&#9654;",
                 method="animate",
                 args=[
                     None,
                     dict(
                         frame=dict(duration=TIMES['animation'],
                                    redraw=True),
                         transition=dict(duration=TIMES['transition'],
                                         easing="quadratic-in-out"),
                         fromcurrent=True,
                         mode='immediate'
                     )
                 ]),
            dict(label="&#9724;",
                 method="animate",
                 args=[
                     [None],
                     dict(
                         frame=dict(duration=0,
                                    redraw=True),
                         transition=dict(duration=0),
                         mode='immediate'
                         )
                 ])
            ],
        pad={"r": 0, "t": 0},
        x=0.50,
        y=1.07,
        xanchor="right",
        yanchor="top"
    )

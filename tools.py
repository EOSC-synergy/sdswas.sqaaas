#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Tools module with functions related to plots """

import dash_core_components as dcc

from data_handler import FigureHandler
from data_handler import WasFigureHandler
from data_handler import ProbFigureHandler
from data_handler import VisFigureHandler
from data_handler import TimeSeriesHandler
from data_handler import ObsTimeSeriesHandler
from data_handler import Observations1dHandler
from data_handler import DEBUG
from data_handler import DATES
from dash_server import cache
from utils import calc_matrix

from datetime import datetime as dt
from PIL import Image
import tempfile
import gif

start_date = DATES['start_date']
end_date = DATES['end_date']

@gif.frame
def get_gif_figure(model, variable, curdate, tstep):
    return get_figure(model, variable, curdate, tstep, static=False)

@gif.frame
def get_composite(models, variable, curdate, tstep):
        ncols, nrows = calc_matrix(len(models))
        
        row = col = 1
        xpos = ypos = 0
        composite_fp = tempfile.NamedTemporaryFile()
        mod_fps = [tempfile.NamedTemporaryFile() for model in models]

        composite_img = None
        for fp, model in zip(mod_fps, models):
            
            if col == ncols + 1:
                row += 1
                col = 1
            if row == nrows + 1:
                break

            if DEBUG: print('ROWCOL', row, col)
            fig = get_figure(model, variable, curdate, hour=tstep, static=False)
            fig.write_image(fp.name, format='png', engine='kaleido')
            img = Image.open(fp.name)
            img_size = img.size
            if row == 1 and col == 1:
                composite_img = Image.new("RGB", (img_size[0]*ncols, img_size[1]*nrows), 'white')

            composite_img.paste(img, (img_size[0]*(col-1), img_size[1]*(row-1)))

            col += 1

        if composite_img is not None:
            return composite_img


def download_image(models, variable, curdate, tstep=0, anim=False):
    """ """
    if len(models) == 1:
        model = models[0]
        if anim:
            frames = [get_gif_figure(model, variable, curdate, ts) for ts in range(21)]
            fname = "{date}_LOOP_{model}_{variable}.gif".format(date=curdate, model=model, variable=variable)
            gif.save(frames, '/tmp/{}'.format(fname), duration=120)
            return dcc.send_file(
                    '/tmp/{}'.format(fname),
                    filename=fname)

        fig = get_figure(model, variable, curdate, hour=tstep, static=False)
        fname = "{date}{hour:02d}_{model}_{variable}.png".format(date=curdate, hour=tstep, model=model, variable=variable)
        with tempfile.NamedTemporaryFile() as fp:
            fig.write_image(fp.name, format='png', engine='kaleido')
            if DEBUG: print('DOWNLOAD SINGLE PNG', fp.name)
            return dcc.send_file(
                    fp.name,
                    filename=fname)
    else:
        if anim:
            frames = [get_composite(models, variable, curdate, ts) for ts in range(21)]
            fname = "{date}_LOOP_MULTIMODEL_{variable}.png".format(date=curdate, variable=variable)
            gif.save(frames, '/tmp/{}'.format(fname), duration=120)
            return dcc.send_file(
                    '/tmp/{}'.format(fname),
                    filename=fname)

        composite_img = get_composite(models, variable, curdate, tstep)
        if composite_img is not None:
            composite_img.save(composite_fp.name + '.png')

        fname = "{date}{hour:02d}_MULTIMODEL_{variable}.png".format(date=curdate, hour=tstep, variable=variable)

        if DEBUG: print('DOWNLOAD PNG', composite_fp.name + '.png')
        return dcc.send_file(
                composite_fp.name + '.png',
                filename=fname)

def get_eval_timeseries(obs, start_date, end_date, var, idx, name):
    """ Retrieve timeseries """
    if DEBUG: print('SERVER: OBS TS init for obs {} ... '.format(str(obs)))
    th = ObsTimeSeriesHandler(obs, start_date, end_date, var)
    if DEBUG: print('SERVER: OBS TS generation ... ')
    return th.retrieve_timeseries(idx, name)


def get_timeseries(model, date, var, lat, lon):
    """ Retrieve timeseries """
    if DEBUG: print('SERVER: TS init for models {} ... '.format(str(model)))
    th = TimeSeriesHandler(model, date, var)
    if DEBUG: print('SERVER: TS generation ... ')
    return th.retrieve_timeseries(lat, lon, method='feather')


def get_obs1d(sdate, edate, obs, var):
    """ Retrieve 1D observation """
    obs_handler = Observations1dHandler(sdate, edate, obs)
    return obs_handler.generate_obs1d_tstep_trace(var)


def get_prob_figure(var, prob=None, day=0, selected_date=end_date):
    """ Retrieve figure """
    if DEBUG: print(prob, day, selected_date)
    try:
        selected_date = dt.strptime(
            selected_date, "%Y-%m-%d").strftime("%Y%m%d")
    except:
        pass
    if DEBUG: print(prob, day, selected_date)
    if prob:
        if DEBUG: print('SERVER: PROB Figure init ... ')
        fh = ProbFigureHandler(var=var, prob=prob, selected_date=selected_date)
        if DEBUG: print('SERVER: PROB Figure generation ... ')
        return fh.retrieve_var_tstep(day=day)
    if DEBUG: print('SERVER: NO PROB Figure')
    return ProbFigureHandler().retrieve_var_tstep()


def get_was_figure(was=None, day=1, selected_date=end_date):
    """ Retrieve figure """
    if DEBUG: print(was, day, selected_date)
    try:
        selected_date = dt.strptime(
            selected_date, "%Y-%m-%d").strftime("%Y%m%d")
    except:
        pass
    if DEBUG: print(was, day, selected_date)
    if was:
        if DEBUG: print('SERVER: WAS Figure init ... ')
        fh = WasFigureHandler(was=was, selected_date=selected_date)
        if DEBUG: print('SERVER: WAS Figure generation ... ')
        return fh.retrieve_var_tstep(day=day)
    if DEBUG: print('SERVER: NO WAS Figure')
    return WasFigureHandler().retrieve_var_tstep()

def get_vis_figure(tstep=0, selected_date=end_date):
    """ Retrieve figure """
    if DEBUG: print(tstep, selected_date)
    try:
        selected_date = dt.strptime(
            selected_date, "%Y-%m-%d").strftime("%Y%m%d")
    except:
        pass
    if DEBUG: print(tstep, selected_date)
    if tstep is not None:
        if DEBUG: print('SERVER: VIS Figure init ... ')
        fh = VisFigureHandler(selected_date=selected_date)
        if DEBUG: print('SERVER: VIS Figure generation ... ')
        return fh.retrieve_var_tstep(tstep=tstep)
    if DEBUG: print('SERVER: NO VIS Figure')
    return VisFigureHandler().retrieve_var_tstep()

#@app.app_context
#@cache.cached(timeout=60, key_prefix='figure')
def get_figure(model=None, var=None, selected_date=end_date, tstep=0, hour=None, static=True, aspect=(1, 1), center=None):
    """ Retrieve figure """
    #if DEBUG: print("***", model, var, selected_date, tstep, hour, "***")
    try:
        selected_date = dt.strptime(
            selected_date, "%Y-%m-%d %H:%M:%S").strftime("%Y%m%d")
    except:
        pass
    if model:
        if DEBUG: print('SERVER: Figure init ... ')
        fh = FigureHandler(model, selected_date)
        if isinstance(hour, list):
            return [fh.retrieve_var_tstep(var, tstep, h, static, aspect, center) for h in hour]
        elif isinstance(tstep, list):
            return [fh.retrieve_var_tstep(var, ts, hour, static, aspect, center) for ts in tstep]
        elif hour == 'all' or tstep == 'all':
            return [fh.retrieve_var_tstep(var, ts, hour, static, aspect, center) for ts in fh.tim]

        if DEBUG: print('SERVER: Figure generation ... ')
        return fh.retrieve_var_tstep(var, tstep, hour, static, aspect, center)
    if DEBUG: print('SERVER: No Figure')
    return FigureHandler().retrieve_var_tstep()

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
from data_handler import MODELS
from dash_server import cache
from utils import calc_matrix

from datetime import datetime as dt
from PIL import Image
from wand.image import Image as wimage
import tempfile
import gif
import os.path
import subprocess

start_date = DATES['start_date']
end_date = DATES['end_date']

@gif.frame
def get_gif_figure(model, variable, curdate, tstep):
    return get_figure(model, variable, curdate, tstep, static=False)

def get_composite(models, variable, curdate, tstep):
    """ """
    ncols, nrows = calc_matrix(len(models))
    
    row = col = 1
    xpos = ypos = 0

    composite_img = None
    for model in models:

        download_dir = os.path.join(MODELS[model]['path'],
                'images',
                dt.strptime(curdate, '%Y%m%d').strftime('%Y'),
                dt.strptime(curdate, '%Y%m%d').strftime('%m'))
        
        fname = "{date}{tstep:02d}_{model}_{variable}.png".format(date=curdate, tstep=tstep, model=model, variable=variable)

        filename = os.path.join(download_dir, fname)

        if col == ncols + 1:
            row += 1
            col = 1
        if row == nrows + 1:
            break

        if DEBUG: print('ROWCOL', row, col)
        if not os.path.exists(filename):
            if DEBUG: print("MODEL", model, "NOT EXISTING")
            try:
                fig = get_figure(model, variable, curdate, tstep=tstep, static=False)
            except:
                return None
            fig.write_image(filename, format='png', engine='kaleido')
        img = Image.open(filename)
        img_size = img.size
        if row == 1 and col == 1:
            composite_img = Image.new("RGB", (img_size[0]*ncols, img_size[1]*nrows), 'white')

        composite_img.paste(img, (img_size[0]*(col-1), img_size[1]*(row-1)))

        col += 1

    if DEBUG: print(composite_img)
    if composite_img is not None:
        return composite_img


def download_image(models, variable, curdate, tstep=0, anim=False):
    """ """
    if len(models) == 1:
        model = models[0]
        download_dir = os.path.join(MODELS[model]['path'],
                'images',
                dt.strptime(curdate, '%Y%m%d').strftime('%Y'),
                dt.strptime(curdate, '%Y%m%d').strftime('%m'))
        if anim:
            fname = "{date}_LOOP_{model}_{variable}.gif".format(date=curdate, model=model, variable=variable)
            filename = os.path.join(download_dir, fname)
            if not os.path.exists(filename):
                frames = [get_gif_figure(model, variable, curdate, ts) for ts in range(25)]
                frames = [f for f in frames if f is not None]
                gif.save(frames, filename, duration=120)
            return dcc.send_file(
                    filename,
                    filename=os.path.basename(filename))

        fname = "{date}{tstep:02d}_{model}_{variable}.png".format(date=curdate, tstep=tstep, model=model, variable=variable)
        filename = os.path.join(download_dir, fname)
        if not os.path.exists(filename):
            fig = get_figure(model, variable, curdate, tstep=tstep, static=False)
            fig.write_image(filename, format='png', engine='kaleido')
        if DEBUG: print('DOWNLOAD SINGLE PNG', filename)
        return dcc.send_file(
                filename,
                filename=os.path.basename(filename))
    else:
        if anim:
            fname = "{date}_LOOP_MULTIMODEL_{variable}.gif".format(date=curdate, variable=variable)
            frames = [get_composite(models, variable, curdate, ts) for ts in range(25)]
            frames = [f for f in frames if f is not None]
            with tempfile.NamedTemporaryFile() as anim_fp:
                anim_fp.name = anim_fp.name + '.gif'
                frames[0].save(anim_fp.name, save_all=True, append_images=frames[1:],
                   optimize=True, duration=120, loop=0)
                return dcc.send_file(
                        anim_fp.name,
                        filename=fname)

        composite_fp = tempfile.NamedTemporaryFile()
        composite_img = get_composite(models, variable, curdate, tstep)
        if composite_img is not None:
            composite_fp.name = composite_fp.name + '.png'
            composite_img.save(composite_fp.name)

        fname = "{date}{tstep:02d}_MULTIMODEL_{variable}.png".format(date=curdate, tstep=tstep, variable=variable)

        if DEBUG: print('DOWNLOAD PNG', composite_fp.name)
        return dcc.send_file(
                composite_fp.name,
                filename=fname)

def get_eval_timeseries(obs, start_date, end_date, var, idx, name):
    """ Retrieve timeseries """
    if DEBUG: print('SERVER: OBS TS init for obs {} ... '.format(str(obs)))
    th = ObsTimeSeriesHandler(obs, start_date, end_date, var)
    if DEBUG: print('SERVER: OBS TS generation ... ')
    return th.retrieve_timeseries(idx, name)


def get_timeseries(model, date, var, lat, lon, forecast=False):
    """ Retrieve timeseries """
    if DEBUG: print('SERVER: TS init for models {} ... '.format(str(model)))
    th = TimeSeriesHandler(model, date, var)
    if DEBUG: print('SERVER: TS generation ... ')
    return th.retrieve_timeseries(lat, lon, method='feather', forecast=forecast)


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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Tools module with functions related to plots """

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
#from dash_server import srv as app

from datetime import datetime as dt

start_date = DATES['start_date']
end_date = DATES['end_date']


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
        if DEBUG: print('SERVER: Figure generation ... ')
        return fh.retrieve_var_tstep(var, tstep, hour, static, aspect, center)
    if DEBUG: print('SERVER: No Figure')
    return FigureHandler().retrieve_var_tstep()

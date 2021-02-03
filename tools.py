#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Tools module with functions related to plots """

from data_handler import FigureHandler
from data_handler import TimeSeriesHandler
from data_handler import ObsTimeSeriesHandler
from data_handler import Observations1dHandler
from data_handler import DEBUG
from tabs import end_date


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


def get_figure(model=None, var=None, selected_date=end_date, tstep=0,
               static=True, aspect=(1, 1)):
    """ Retrieve figure """
    # if DEBUG: print(var, selected_date, tstep)
    try:
        selected_date = dt.strptime(
            selected_date, "%Y-%m-%d %H:%M:%S").strftime("%Y%m%d")
    except:
        pass
    if model:
        if DEBUG: print('SERVER: Figure init ... ')
        fh = FigureHandler(model, selected_date)
        if DEBUG: print('SERVER: Figure generation ... ')
        return fh.retrieve_var_tstep(var, tstep, static, aspect)
    if DEBUG: print('SERVER: No Figure')
    return FigureHandler().retrieve_var_tstep()


def get_obs1d(sdate, edate, obs, var):
    """ Retrieve 1D observation """
    obs_handler = Observations1dHandler(sdate, edate, obs)
    return obs_handler.generate_obs1d_tstep_trace(var)


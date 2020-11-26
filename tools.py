#!/usr/bin/env python3
# -*- coding: utf-8 -*-
""" Tools module with utility functions """

from data_handler import FigureHandler
from data_handler import TimeSeriesHandler
from data_handler import Observations1dHandler
from data_handler import DEBUG
from tabs import end_date
import math


def calc_matrix(n):
    sqrt_n = math.sqrt(n)
    ncols = sqrt_n == int(sqrt_n) and int(sqrt_n) or int(sqrt_n) + 1
    nrows = n%ncols > 0 and int(n/ncols)+1 or int(n/ncols)
    return ncols, nrows


def get_timeseries(model, date, var, lat, lon):
    """ Retrieve timeseries """
    # if DEBUG: print(var, selected_date, tstep)
    if DEBUG: print('SERVER: TS init for models {} ... '.format(str(model)))
    th = TimeSeriesHandler(model, date, var)
    if DEBUG: print('SERVER: TS generation ... ')
    return th.retrieve_timeseries(lat, lon)


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


def get_obs1d(date, var):
    """ Retrieve 1D observation """
    obs_handler = Observations1dHandler('./data/obs/aeronet/netcdf/od550aero_202004.nc', date)
    return obs_handler.generate_obs1d_tstep_trace(var)


# -*- coding: utf-8 -*-
# Copyright 2016 Earth Sciences Department, BSC-CNS
#

"""nc2geojson module.

This module provide conversion from netCDF to geojson format.

"""

from netCDF4 import Dataset as nc_file
import geopandas as gpd
import pandas as pd
from shapely import geometry
import numpy as np
import json
import os
import os.path
import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta

np.set_printoptions(precision=2)

DIR_PATH = os.path.abspath(os.path.dirname(__file__))
MODELS = json.load(open(os.path.join(DIR_PATH, '../conf/models.json')))
WAS = json.load(open(os.path.join(DIR_PATH, '../conf/was.json')))
NETCDF_TEMPLATE = "{}/netcdf/{}{}.nc"

DEBUG = True

class WasTables(object):
    """ Class to manage the figure creation """

    def __init__(self, was=None, model='median', variable='SCONC_DUST', selected_date=None):
        """ Initialize WasFigureHandler with shapefile and netCDF data """
        self.model = model
        self.was = was

        if self.was:
            # read shapefile
            print(WAS[self.was]['shp'])
            self.was_df = gpd.read_file(WAS[self.was]['shp'])
            self.was_df['lon_lat'] = self.was_df['geometry'].apply(lambda row: row.centroid)
            self.was_df['LON'] = self.was_df['lon_lat'].apply(lambda row: row.x)
            self.was_df['LAT'] = self.was_df['lon_lat'].apply(lambda row: row.y)
            self.was_df = self.was_df.drop('lon_lat', axis=1)
            self.wlon = self.was_df['LON']
            self.wlat = self.was_df['LAT']

        if self.model and selected_date:
            # read nc file
            if DEBUG: print("MODEL", model)
            filepath = NETCDF_TEMPLATE.format(
                MODELS[self.model]['path'],
                selected_date,
                MODELS[self.model]['template']
            )
            self.input_file = nc_file(filepath)
            if 'lon' in self.input_file.variables:
                lon = self.input_file.variables['lon'][:]
                lat = self.input_file.variables['lat'][:]
            else:
                lon = self.input_file.variables['longitude'][:]
                lat = self.input_file.variables['latitude'][:]
            time_obj = self.input_file.variables['time']
            self.tim = time_obj[:]
            self.what, _, rdate, rtime = time_obj.units.split()[:4]
            if len(rtime) > 5:
                rtime = rtime[:5]
            self.rdatetime = datetime.strptime("{} {}".format(rdate, rtime),
                                               "%Y-%m-%d %H:%M")

            self.xlon, self.ylat = np.meshgrid(lon, lat)
            self.vardata = self.input_file.variables[variable][:]*1e9

        if selected_date:
            self.selected_date_plain = selected_date

            self.selected_date = datetime.strptime(
                selected_date, "%Y%m%d").strftime("%Y-%m-%d")

        opath = WAS[was]['path'].format(was=was, date=self.selected_date_plain)
        os.makedirs(opath, exist_ok=True)
        otpl = WAS[was]['template'].format(date=self.selected_date_plain, var=variable)
        self.output = os.path.join(opath, otpl)


    def set_data(self, day=1):
        """ Set time dependent data """

        d_idx = []
        d_date = self.rdatetime + relativedelta(days=day)

        for n, tstep in enumerate(self.tim[:]):
            ctime = (self.rdatetime + relativedelta(hours=float(tstep)))
            if ctime.strftime("%Y%m%d") == d_date.strftime("%Y%m%d"):
                d_idx.append(n)

        return self.vardata[d_idx,:,:].max(axis=0)

    def get_regions_data(self):
        if not hasattr(self, 'xlon'):
            return names, colors, definitions

        flon = self.xlon.flatten()
        print('SHAPE LON', flon.shape)
        flat = self.ylat.flatten()
        print('SHAPE LAT', flat.shape)
        out_df = pd.DataFrame(
                columns=['day', 'names', 'colors', 'definitions'])

        names = []
        colors = []
        definitions = []
        days = []
        for day in [1, 2]:
            data = self.set_data(day=day).flatten()
            print('SHAPE DATA', data.shape)

            for idx in self.was_df.index.values:
                name = self.was_df.iloc[idx]['NAME_1']
                geom = self.was_df.iloc[idx]['geometry']
                mask = np.array([geom.contains(geometry.Point(x, y)) for x, y in np.array([flon, flat]).T])
                mdata = np.ma.masked_array(data, mask=~mask)
                print(";;;;", mdata[~mdata.mask])
                reg_var = mdata[~mdata.mask].max()
                perc = WAS[self.was]['values'][name]
                print("::::", name, reg_var, perc)
                color = ((reg_var<perc[0]) and 'green') or \
                    (((reg_var>=perc[0]) and (reg_var<perc[1])) and 'gold') or \
                    (((reg_var>=perc[1]) and (reg_var<perc[2])) and 'darkorange') or 'red'
                names.append(name)
                colors.append(color)
                definitions.append(WAS[self.was]['colors'][color])
                days.append('Day{}'.format(day))


        print(names, colors, definitions, days)
        out_df['names'] = names
        out_df['colors'] = colors
        out_df['definitions'] = definitions
        out_df['day'] = days
        out_df.set_index('day')
        print(self.output)
        out_df.to_hdf(self.output, 'was_{}'.format(self.selected_date_plain), format='table')

#         print(names, colors, definitions)
#         return names, colors, definitions


if __name__ == "__main__":
    curdate = sys.argv[1]
    WasTables(was='burkinafaso', selected_date=curdate).get_regions_data()

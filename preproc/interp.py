#import numpy as np
import xarray as xr
import dask
#from dask.diagnostics import ProgressBar
#import matplotlib.pyplot as plt

dask.config.set(scheduler='processes')

EXP = {
    'cams': '../data/models/CAMS/netcdf/20200*.nc4',
    'monarch': '../data/models/MONARCH/netcdf/20200*.nc4',
    'dream8-macc': '../data/models/DREAM8-MACC/netcdf/20200*.nc4',
    'nasa-geos': '../data/models/NASA-GEOS/netcdf/20200*.nc4',
    'median': '../data/models/median/netcdf/20200*.nc4',
}
OBS = '../data/obs/aeronet/netcdf/od550aero_2020*.nc'
FIL = '../data/obs/aeronet/netcdf/ae440-870aero_20200*.nc'

DEST = '../data/obs/aeronet/feather'


def preprocess(ds, n=8):
    '''keep only the first N timestep for each file'''
    return ds.isel(time=range(n))


def plot_station(i=0):

    obs_ds = xr.open_mfdataset(OBS, parallel=True)
    filter_ds = xr.open_mfdataset(FIL, parallel=True)

    obs_df = obs_ds['od550aero'].to_dataframe()
    obs_df.reset_index(inplace=True)
    obs_df.to_feather(
        '{}/{}.ft'.format(DEST, 'od550aero'),
    )
    filter_df = filter_ds['ae440-870aero'].to_dataframe()
    filter_df.reset_index(inplace=True)
    filter_df.to_feather(
        '{}/{}.ft'.format(DEST, 'ae440-870aero'),
    )

    obs_lon = obs_ds['longitude'][0].data
    obs_lat = obs_ds['latitude'][0].data

#     olon = obs_lon.compute()
#     olat = obs_lat.compute()

#    print("Station with LON: {} and LAT: {}".format(olon[i], olat[i]))
    # interpolated = []
    print(obs_ds['od550aero'].shape)
    print(filter_ds['ae440-870aero'].shape)
    for exp in EXP:
        print(exp)
        exp_ds = xr.open_mfdataset(EXP[exp], concat_dim='time',
                                   preprocess=preprocess, parallel=True)

        da = exp_ds['od550_dust']
        da
        print(exp_ds['od550_dust'].shape)
        int_data = exp_ds['od550_dust'].interp(lon=obs_lon, lat=obs_lat)
        print(int_data.shape)
        int_df = int_data.to_dataframe()
        int_df.reset_index(inplace=True)
        int_df.to_feather(
            '{}/{}.ft'.format(DEST, exp),
        )
#        interpolated.append(int_data[:, i, i])

#     for ar in interpolated:
#         print(ar)
#     print(obs_ds['od550aero'])
#     print(filter_ds['ae440-870aero'])
#     merged = xr.merge(interpolated + [obs_ds['od550aero'][:, i], filter_ds['ae440-870aero'][:, i]],
#                       compat='no_conflicts',)
#
#     fig, axes = plt.subplots()
#
#     print("Station with LON: {} and LAT: {}".format(olon[i], olat[i]))
#     with ProgressBar():
#         data = merged.compute().astype('float32')
#         print((data == np.nan).all())
#         print(data)
#         data.plot.line()
#         plt.savefig('test.png')
#         print('done')


if __name__ == "__main__":
    plot_station()
#    import sys
#     i = int(sys.argv[1])
#     j = int(sys.argv[2])
#     for s in range(i, j):

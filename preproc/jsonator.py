"""Modulo para escribir GeoJSONs.

Test:
http://geojson.io

Estilo (propiedades):
https://github.com/mapbox/simplestyle-spec/tree/master/1.1.0

"""

import matplotlib as mpl
mpl.use('agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import json


def ncl_colors(path, rev=False, n=None):
    ncolors = 0
    colors = []

    with open(path) as fp:
        for line in fp:
            line = line.split('#')[0].split(';')[0].split('/*')[0].strip()
            if line:
                if line.startswith('ncolors'):
                    ncolors = int(line.split('=')[1])
                else:
                    colors += [tuple(float(i) for i in line.split())]

    colors = np.array(colors)

    if np.any(colors > 1):
        colors /= 255.

    if rev:
        colors = colors[::-1]

    if n is not None:
        if ncolors:
            assert len(colors) == ncolors
        else:
            ncolors = len(colors)

        csel = np.linspace(0, ncolors - 1, n).round().astype(int)
        offset = (ncolors - csel[-1] - 1) // 2
        colors = colors[csel + offset]

    return colors


def contourf(lon, lat, values, levels=None, cmap=None, cmap_file=None, cmap_rev=False,
             pretty_print=False, custom_properties={}):

    data = np.ma.fix_invalid(values)

    if levels is None:
        n = 12
    else:
        n = len(levels)

    if cmap is not None and type(cmap) == str:
        cmap = mpl.cm.get_cmap(cmap, n)
    elif cmap is not None:
        cmap = cmap  # mpl.colors.ListedColormap(cmap)
    elif cmap_file is None:
        cmap = None
    else:
        cmap = ncl_colors(cmap_file, n=n, rev=cmap_rev)

    if levels is None:
        cs = plt.contourf(lon, lat, data, n, colors=cmap)
    else:
        cs = plt.contourf(lon, lat, data, levels, colors=cmap)

    # Procesa los contornos

    features = []

    for i, patch in enumerate(cs.collections):  # Contorno

        parent = None
        polygons = []

        for path in patch.get_paths():
            for poly in path.to_polygons():  # Poligonos de un contorno

                curr = mpl.path.Path(poly, closed=True)

                # Reduce el numero de decimales

                if pretty_print:
                    coords = poly.tolist()
                else:
                    coords = []
                    for c in poly.tolist():
                        p = [round(v, 2) for v in c]
                        coords.append(p)

                # Guarda el poligono

                if len(coords) > 3:

                    if parent is None or not parent.contains_path(curr):
                        # Poligono exterior
                        polygons.append([coords])
                        parent = curr
                    else:
                        # Poligono interior
                        polygons[-1].append(coords)

        if not polygons:
            continue

        # Calculo de propiedades
        if cmap is not None:
            color = cs.tcolors[i]
            r, g, b, a = [int(c * 255) for c in color[0]]
            fill = '#{:02x}{:02x}{:02x}'.format(r, g, b)

        lolimit = cs.levels[i]
        hilimit = cs.levels[i+1]

        properties = {
#             'title': '',
#             'description': 'Contour: {} to {}'.format(lolimit, hilimit),
# 
#             # Propiedades de estilo
#             'marker-size': 'medium',
#             'marker-symbol': '',
#             'marker-color': '#7e7e7e',
#             'stroke': '#555555',
#             'stroke-opacity': 1.0,
#             'stroke-width': 0.0,
#             'fill': fill,
#             'fill-opacity': 0.6,
             'value': (hilimit+lolimit)/2,
# 
#             # Opcionales
#             'hilimit': hilimit,
#             'lolimit': lolimit
        }

        properties.update(custom_properties)

        elem = {
            'type': 'Feature',
            'geometry': {
                'coordinates': polygons,
                'type': 'MultiPolygon',
            },
            'properties': properties,
            'id': '{:02d}'.format(i),
        }

        features.append(elem)

    geojson = {
        'type': 'FeatureCollection',
        'features': features
    }

    if pretty_print:
        res = json.dumps(geojson, indent=2)
    else:
        res = json.dumps(geojson, separators=(',', ':'))

    return res


def pcolormesh(x, y, values, levels=12, proj=None, gridded_metadata={},
               cmap=None, cmap_file=None, cmap_rev=False, pretty_print=False,
               properties={}):
    """Representa celdas con metadatos.

        x, y -- Coordenadas del dominio (1D) correspondientes a la
                proyeccion de los datos.
        values -- Array 2D de valores para representar.
        levels -- Informacion de niveles de la escala de colores.
                  Valores posibles:
                  . Secuencia de floats -> Ej: np.linspace(-10,10,11)
                  . Si levels es int -> Representa ese numero de niveles
                  . Si levels es None -> Se toma levels=12
        proj -- Proyeccion geografica del dominio (pyproj). Si los datos
                estan en lat/lon (unidades: grados) seleccionar None.
                IMPORTANTE:
                . Proj=None ==> X, Y es lon/lat en GRADOS
                . Si Proj!=None y la proyeccion tiene unidades angulares
                  (rotated-pole, EPSG:4326), entonces las coordenadas
                  X, Y deben introducirse en RADIANES.
        gridded_metadata -- Dict de arrays 2D+.
                            {'property': array[..., ny, nx], ...}
                            A cada celda se le asignara el valor de XY
                            correspondiente. Si el array tiene 3D o mas,
                            el resultado sera una lista.
        cmap_file -- Fichero de colores de NCL.
        cmap_rev -- Invierte la secuencia de colores.
        pretty_print -- Si es True, el JSON estara tabulado
                        Se es False, el JSON no tiene espacio en blanco
        properties -- Metadata del JSON comun en todos los poligonos.

    """

    # Convierte datos a arrays

    values = np.ma.asarray(values, dtype=float)
    for k, v in gridded_metadata.items():
        gridded_metadata[k] = np.ma.asarray(v)

    # Calculo de niveles automaticos

    if isinstance(levels, int):
        zmin = np.ma.fix_invalid(values).min()
        zmax = np.ma.fix_invalid(values).max()
        locator = ticker.MaxNLocator(levels, min_n_ticks=1)
        levels = locator.tick_values(zmin, zmax)

    n = len(levels) + 1

    levels = np.sort(levels)
#    lolimits = np.concatenate([[-np.inf], levels])
#    hilimits = np.concatenate([levels, [np.inf]])
    lolimits = levels[:-1]
    hilimits = levels[1:]

    dx = x[1] - x[0]
    dy = y[1] - y[0]

    # Coordenadas de los vertices
    # Si tiene una proyeccion las convierte a latlon
    # Se redondean a 6 decimales

    x0 = x - dx / 2
    x1 = x + dx / 2
    y0 = y - dy / 2
    y1 = y + dy / 2

    x0 = np.where(x0 == -180, -179.9, x0)
    x0 = np.where(x0 == 180, 179.99, x0)
    x1 = np.where(x1 == -180, -179.9, x1)
    x1 = np.where(x1 == 180, 179.9, x1)
    y0 = np.where(y0 == -90, -89.9, y0)
    y0 = np.where(y0 == 90, 89.9, y0)
    y1 = np.where(y1 == -90, -89.9, y1)
    y1 = np.where(y1 == 90, 89.9, y1)

    lon_sw, lat_sw = np.meshgrid(x0, y0)
    lon_se, lat_se = np.meshgrid(x1, y0)
    lon_nw, lat_nw = np.meshgrid(x0, y1)
    lon_ne, lat_ne = np.meshgrid(x1, y1)

    if proj is not None:
        lon_sw, lat_sw = proj(lon_sw, lat_sw, inverse=True)
        lon_se, lat_se = proj(lon_se, lat_se, inverse=True)
        lon_nw, lat_nw = proj(lon_nw, lat_nw, inverse=True)
        lon_ne, lat_ne = proj(lon_ne, lat_ne, inverse=True)

    lon_sw = (lon_sw + 180) % 360 - 180
    lon_se = (lon_se + 180) % 360 - 180
    lon_nw = (lon_nw + 180) % 360 - 180
    lon_ne = (lon_ne + 180) % 360 - 180

    if not pretty_print:
        lon_sw = lon_sw.round(6)
        lat_sw = lat_sw.round(6)
        lon_se = lon_se.round(6)
        lat_se = lat_se.round(6)
        lon_nw = lon_nw.round(6)
        lat_nw = lat_nw.round(6)
        lon_ne = lon_ne.round(6)
        lat_ne = lat_ne.round(6)

    # Colormap

    if cmap is not None and type(cmap) == str:
        cmap = mpl.cm.get_cmap(cmap, n)
        colors = None
    elif cmap is not None:
        cmap = mpl.colors.ListedColormap(cmap)
        colors = None
    elif cmap_file is None:
        cmap = None
    else:
        cmap = ncl_colors(cmap_file, n=n, rev=cmap_rev)

    # Asigna el nivel en que esta cada celda

    assign = np.ma.masked_all(values.shape, dtype=int)
    colors = []

    for nlevel, lolimit in enumerate(lolimits):
        mask = (values >= lolimit).filled(False)
        assign[mask] = nlevel

        if cmap:
            try:
                r, g, b = [int(color * 255) for color in cmap[nlevel]]
            except:
                r, g, b, a = [int(color * 255) for color in cmap(nlevel)]

            fill = '#{:02x}{:02x}{:02x}'.format(r, g, b)
            colors.append(fill)

    # Procesa el geojson

    nlat = len(y)
    nlon = len(x)

    features = []

    for j in range(nlat):
        for i in range(nlon):
            level = assign[j, i]

            if not np.ma.is_masked(level):
                valid = True

                coords = [
                    [float(lon_sw[j, i]), float(lat_sw[j, i])],
                    [float(lon_nw[j, i]), float(lat_nw[j, i])],
                    [float(lon_ne[j, i]), float(lat_ne[j, i])],
                    [float(lon_se[j, i]), float(lat_se[j, i])],
                    [float(lon_sw[j, i]), float(lat_sw[j, i])]
                ]
                if colors:
                    fill = colors[level]
                else:
                    fill = None
                hilimit = float(hilimits[level])
                lolimit = float(lolimits[level])

                if lolimit == -np.inf:
                    lolimit = '-inf'
                if hilimit == np.inf:
                    hilimit = 'inf'

                elem = {
                    'type': 'Feature',
                    'geometry':
                    {
                        'coordinates': [np.array(coords).round(6).tolist()],
                        'type': 'Polygon',
                    },
                    'properties':
                    {
#                         'title': '',
#                         'description': 'Level: {} to {}'.format(lolimit,
#                                                                 hilimit),
# 
#                         # Propiedades de estilo
#                         'stroke': '#555555',
#                         'stroke-opacity': 1.0,
#                         'stroke-width': 0.0,
#                         #'fill': fill,
#                         'fill-opacity': 0.6,
# 
#                         # Opcionales
#                         'hilimit': hilimit,
#                         'lolimit': lolimit,
                    }
                    }

                for k, v in gridded_metadata.items():
#                    print(k, v[..., j, i])
                    try:
                        newval = v[..., j, i].tolist()
                    except:
                        newval = v.data[..., j, i].tolist()

                    if isinstance(newval, float):
                        newval = round(newval, 2)

                        if np.isnan(newval):
                            valid = False
#                    try:
#                        newval = round(v[..., j, i].tolist(), 2)
#                    except:
#                        #newval = 0
#                        newval = round(v.data[..., j, i].tolist(), 2 )
#                    print(newval)

                    elem['properties'][k] = newval

                if not valid:
                    continue

                for k, v in properties.items():
                    elem['properties'][k] = v

                features.append(elem)

    geojson = {
        'type': 'FeatureCollection',
        'features': features
    }

    if pretty_print:
        res = json.dumps(geojson, indent=2)
    else:
        res = json.dumps(geojson, separators=(',', ':'))

    return res


def pointcoll(x, y, values, levels=12, proj=None, gridded_metadata={},
               cmap=None, cmap_file=None, cmap_rev=False, pretty_print=False, properties={}):
    """Representa celdas con metadatos.

        x, y -- Coordenadas del dominio (1D) correspondientes a la
                proyeccion de los datos.
        values -- Array 2D de valores para representar.
        levels -- Informacion de niveles de la escala de colores.
                  Valores posibles:
                  . Secuencia de floats -> Ej: np.linspace(-10,10,11)
                  . Si levels es int -> Representa ese numero de niveles
                  . Si levels es None -> Se toma levels=12
        proj -- Proyeccion geografica del dominio (pyproj). Si los datos
                estan en lat/lon (unidades: grados) seleccionar None.
                IMPORTANTE:
                . Proj=None ==> X, Y es lon/lat en GRADOS
                . Si Proj!=None y la proyeccion tiene unidades angulares
                  (rotated-pole, EPSG:4326), entonces las coordenadas
                  X, Y deben introducirse en RADIANES.
        gridded_metadata -- Dict de arrays 2D+.
                            {'property': array[..., ny, nx], ...}
                            A cada celda se le asignara el valor de XY
                            correspondiente. Si el array tiene 3D o mas,
                            el resultado sera una lista.
        cmap_file -- Fichero de colores de NCL.
        cmap_rev -- Invierte la secuencia de colores.
        pretty_print -- Si es True, el JSON estara tabulado
                        Se es False, el JSON no tiene espacio en blanco
        properties -- Metadata del JSON comun en todos los poligonos.

    """

    # Convierte datos a arrays

    values = np.ma.asarray(values, dtype=float)
    #print(values)
    for k, v in gridded_metadata.items():
        gridded_metadata[k] = np.ma.asarray(v)

    # Calculo de niveles automaticos

    if isinstance(levels, int):
        zmin = np.ma.fix_invalid(values).min()
        zmax = np.ma.fix_invalid(values).max()
        locator = ticker.MaxNLocator(levels, min_n_ticks=1)
        levels = locator.tick_values(zmin, zmax)

    n = len(levels) + 1

    levels = np.sort(levels)
    lolimits = levels[:-1]
    hilimits = levels[1:]

    # Colormap

    if cmap != None and type(cmap) == str:
        cmap = mpl.cm.get_cmap(cmap, n)
        colors = None
    elif cmap != None:
        cmap = mpl.colors.ListedColormap(cmap)
        colors = None
    elif cmap_file is None:
        cmap = None
    else:
        cmap = ncl_colors(cmap_file, n=n, rev=cmap_rev)

    # Asigna el nivel en que esta cada celda

    assign = np.ma.masked_all(values.shape, dtype=int)
    colors = []
#    print('VALUES', values)
#    print('VALUES.data', values.data)

    for nlevel, lolimit in enumerate(lolimits):
        mask = (values >= lolimit).filled(False)
        assign[mask] = nlevel

        if cmap:
            try:
                r, g, b = [int(color * 255) for color in cmap[nlevel]]
            except:
                r, g, b, a = [int(color * 255) for color in cmap(nlevel)]

            fill = '#{:02x}{:02x}{:02x}'.format(r, g, b)
            colors.append(fill)

#    print('ASSIGN', assign)
#    print('MASK', mask)
#    print('COLORS', colors)

    # Procesa el geojson

    nlat = len(y)
    nlon = len(x)

    features = []

    coords = [x[0], y[0]]
    level = assign[0]

    if colors:
        if np.ma.is_masked(level):
            fill = '#ffffff'
        else:
            fill = colors[level]

    if np.ma.is_masked(level):
        level = -1
        hilimit = lolimit = round(values.data[..., 0, 0].tolist(), 2)
    else:
        hilimit = float(hilimits[level])
        lolimit = float(lolimits[level])

#    print('LEVEL', level)

    elem = {
        'type': 'Feature',
        'geometry':
        {
            'coordinates': np.array(coords).round(6).tolist(),
            'type': 'Point',
        },
        'properties':
        {
            'title': '',
            'description': 'Level: {} to {}'.format(lolimit, hilimit),

            # Propiedades de estilo
            'stroke': '#555555',
            'stroke-opacity': 1.0,
            'stroke-width': 0.0,
#            'fill': fill,
            'fill-opacity': 0.6,

#            # Opcionales
            'hilimit': hilimit,
            'lolimit': lolimit,
        }
    }

    for k, v in properties.items():
        elem['properties'][k] = v

    for k, v in gridded_metadata.items():
        #print(k, v)
        try:
            newval = v[..., 0, 0].tolist()
        except:
            newval = v.data[..., 0, 0].tolist()

        if isinstance(newval, float):
            newval = round(newval, 2)

            if np.isnan(newval):
                valid = False
#                print(newval)
        elem['properties'][k] = newval

    features.append(elem)

    geojson = {
        'type': 'FeatureCollection',
        'features': features
    }

    #print(geojson)

    if pretty_print:
        res = json.dumps(geojson, indent=2)
    else:
        res = json.dumps(geojson, separators=(',', ':'))

    return res

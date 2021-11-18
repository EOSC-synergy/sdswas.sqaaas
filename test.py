import dash
import dash_leaflet as dl

app = dash.Dash()
app.layout = dl.Map([dl.TileLayer(), dl.GeoJSON(id='geojson', url='/assets/geojsons/NMMB-BSC/geojson/20211103/04_20211103_OD550_DUST.geojson')]
, style={'width': '1000px', 'height': '500px'})

if __name__ == '__main__':
    app.run_server(debug=True, processes=4, threaded=False,
                   host='bscesdust03.bsc.es', port=8050)

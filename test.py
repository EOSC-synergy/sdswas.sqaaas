#import dash
#import dash_leaflet as dl
#
#app = dash.Dash()
#app.layout = dl.Map([dl.TileLayer(), dl.GeoJSON(id='geojson', url='/assets/geojsons/NMMB-BSC/geojson/20211103/04_20211103_OD550_DUST.geojson')]
#, style={'width': '1000px', 'height': '500px'})

from dash import Dash, dcc, html, Input, Output
import io

app = Dash(__name__)
app.layout = html.Div([
    html.Button("Download Image", id="btn_image"),
    dcc.Download(
        id="download-image",
        )
])


@app.callback(
    Output("download-image", "data"),
    Input("btn_image", "n_clicks"),
    prevent_initial_call=True,
)
def func(n_clicks):
    filename = "/data/daily_dashboard/comparison/all/od550_dust/2022/01/20220116_all_01.png"
    output = io.BytesIO()
    output.write(open(filename, 'rb').read())
    data = output.getvalue()
    return dcc.send_bytes(data, filename='test.png')

#@app.server.route("/stage/<path:path>")
#def serve_static(path):
#    root_dir = os.getcwd()
#    return flask.send_from_directory(os.path.join(root_dir, "stage"), filename=path)


if __name__ == '__main__':
    app.run_server(debug=True, # processes=4, threaded=False,
                   host='bscesdust03.bsc.es', port=8050)

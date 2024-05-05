# Author: Piotr Krzysztof Lis - github.com/straightchlorine

import asyncio
import json
from threading import Thread
from dash import Dash, Input, Output, callback, dcc, html
import pandas as pd
import plotly
import pytest

from reads.interface import InfluxDBInterface

class DevelopmentDashboard:
    """
    A simple development server for testing purposes.
    """

    srv : Dash # The Flask server instance

    def __init__(self):
        """
        Setting up the server as well as the handle.
        """
        # initialize the dash application
        external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
        self.srv = Dash(__name__, external_stylesheets=external_stylesheets)

        # defining the layouts
        self.srv.layout = html.Div(
            [
                html.H1("InfluxDB Data Dashboard"),
                dcc.Graph(id='live-update-graph'),
                dcc.Interval(
                    id='interval-component',
                    interval=1*1000, # in milliseconds
                    n_intervals=0
                )
            ]
        )

    @callback(Output('live-update-graph', 'figure'),
                Input('interval-component', 'n_intervals'))
    def update_graph_live(n):
        # measurement = asyncio.run(update_data())

        # Create the graph with subplots
        fig = plotly.tools.make_subplots(rows=2, cols=1, vertical_spacing=0.2)
        fig['layout']['margin'] = {
            'l': 30, 'r': 10, 'b': 30, 't': 10
        }
        fig['layout']['legend'] = {'x': 0, 'y': 1, 'xanchor': 'left'}

        # fig.append_trace({
        #     'x': measurement['time'],
        #     'y': measurement['temperature'],
        #     'name': 'Altitude',
        #     'mode': 'lines+markers',
        #     'type': 'scatter'
        # }, 1, 1)
        # fig.append_trace({
        #     'x': measurement['time'],
        #     'y': measurement['pressure'],
        #     'text': measurement['time'],
        #     'name': 'Longitude vs Latitude',
        #     'mode': 'lines+markers',
        #     'type': 'scatter'
        # }, 2, 1)

        return fig
    
    def start_dashboard(self):
        self.srv.run_server(debug=True, host='localhost', port=8001)

    def run_dashboard(self):
        """
        Start the server on a separate thread.
        """
        server_thread = Thread(target=self.srv.start_dashboard)
        server_thread.start()

if __name__ == "__main__":
    srv = DevelopmentDashboard()
    srv.run_dashboard()




class Dashboard:

    # running the test server and specifying the IP and port
    test_dev_ip = 'localhost'
    test_dev_port = 5000

    # loading the secrets
    with open('secrets/secrets.json', 'r') as f:
        secrets = json.load(f)

    # list of attached sensors and their parameters
    sensors = {
        "bmp180": ["altitude", "pressure", "temperature", "seaLevelPressure"],
        "mq135": ["aceton", "alcohol", "co", "co2", "nh4", "toulen"]
    }

    # connecting to the InfluxDB instance via the InfluxDBInterface
    interface = InfluxDBInterface(secrets['host'],
                                secrets['port'],
                                secrets['token'],
                                secrets['organization'],
                                secrets['bucket'],
                                sensors,
                                test_dev_ip,
                                test_dev_port,
                                secrets['handle'])

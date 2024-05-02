#!/usr/bin/env python

from flask import Flask, jsonify

class TestServer:
    """A simple server to test the client with."""

    srv : Flask # The Flask server instance

    """The example JSON that the server will return when the /circumstances endpoint is called."""
    def __init__(self):
        self.srv = Flask(__name__)
        @self.srv.route('/circumstances', methods=['GET'])
        def get_circumstances():
            return jsonify(self.example_json)

    # Example JSON response from nodemcu
    example_json = {
        "nodemcu": {
            "bmp180": {
                "altitude": "149.56",
                "pressure": "998.42",
                "seaLevelPressure": "1016.34",
                "temperature": "26.00"
            },
            "mq135": {
                "aceton": "2.57",
                "alcohol": "6.62",
                "co": "28.88",
                "co2": "412.10",
                "nh4": "15.12",
                "toulen": "3.14"
            }
        }
    }

    """Start the server."""
    def run_testing_server(self):
        self.srv.run()

if __name__ == "__main__":
    srv = TestServer()
    srv.run_testing_server()

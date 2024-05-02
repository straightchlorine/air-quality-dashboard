#!/usr/bin/env python

from flask import Flask, jsonify

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


def server_setup():
    srv = Flask(__name__)

    @srv.route('/circumstances', methods=['GET'])
    def get_circumstance():
        return jsonify(data)



def run_srv():
    srv.run()

if __name__ == "__main__":
    run_srv()

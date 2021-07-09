import json
from pathlib import Path

from flask import jsonify, make_response
from flask_restx import Resource

from rm_reporting import api, app


@api.route("/info", methods=["GET"])
class Info(Resource):
    @staticmethod
    def get():
        _health_check = {}
        if Path("git_info").exists():
            with open("git_info") as io:
                _health_check = json.loads(io.read())

        info = {
            "name": "rm-reporting",
            "version": app.config["VERSION"],
        }
        info = dict(_health_check, **info)

        return make_response(jsonify(info), 200)

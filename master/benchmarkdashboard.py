from __future__ import absolute_import
from __future__ import print_function

import os
import time

import requests
from flask import Flask
from flask import render_template
from flask import render_template_string

from buildbot.process.results import statusToString
from twisted.python import log

import subprocess
import json

import config

benchmarkdashboard = Flask('test', root_path=os.path.dirname(__file__))
# this allows to work on the template without having to restart Buildbot
benchmarkdashboard.config['TEMPLATES_AUTO_RELOAD'] = True

@benchmarkdashboard.route("/index.html")
def main():
    benchmarksToRun = ["mail_query", "mail_query_threadleader"]
    charts = []

    for benchmark in benchmarksToRun:
        output = subprocess.check_output("{}/testenv.py srcbuild --noninteractive kube Sink hawd json {}".format(config.dockerdir, benchmark), shell=True, stderr=subprocess.STDOUT)
        # log.msg("Output: ", output)
        if output:
            hawdResult = json.loads(output)
            graph_data = []
            for i, row in enumerate(sorted(hawdResult['rows'], key=lambda row: row['timestamp'])):
                # commit = row['commit']
                graph_data.append(dict(x=i, y=row['queryResultPerMs']))

            charts.append({"name": hawdResult['dataset'],
                        "description": hawdResult['description'],
                        "foo": "bar",
                        "data": graph_data})

    if charts:
        return render_template('mydashboard.html', charts=charts)

    return render_template_string("No results available")

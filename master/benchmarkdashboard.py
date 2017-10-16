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
    benchmarksToRun = [{"name": "mail_query",
                        "render": ["simple", "threadleader"],
                        "absoluteAxis": False},
                       {"name": "mail_query_incremental",
                        "render": ["nonincremental", "incremental"],
                        "absoluteAxis": True}
                      ]
    charts = []

    for benchmark in benchmarksToRun:
        output = subprocess.check_output("{}/testenv.py srcbuild --noninteractive kube Sink hawd json {}".format(config.dockerdir, benchmark["name"]), shell=True, stderr=subprocess.STDOUT)
        # log.msg("Output: ", output)
        if output:
            hawdResult = json.loads(output)
            graph_data = {}
            units = {}
            names = {}
            for i, row in enumerate(sorted(hawdResult['rows'], key=lambda row: row['timestamp'])):
                skip = False
                # commit = row['commit']
                if 'filter' in benchmark:
                    f = benchmark['filter']
                    for c in row['columns']:
                        if c['name'] == f[0] and c['value'] != f[1]:
                            skip = True
                            break
                if skip:
                    continue

                for c in row['columns']:
                    name = c['name']
                    if name in benchmark["render"]:
                        #We aggregate by column name
                        if name in graph_data:
                            graph_data[name].append(dict(x=i, y=c['value']))
                        else:
                            graph_data[name]= [dict(x=i, y=c['value'])]
                        units[name] = c['unit']
                        names[name] = c['name']

            datasets=[]
            for name, data in graph_data.items():
                datasets.append({"name": names[name],
                    "data": data,
                    "unit": units[name]
                    })

            charts.append({"name": hawdResult['dataset'],
                        "description": hawdResult['description'],
                        "datasets": datasets,
                        "absoluteAxis": benchmark["absoluteAxis"]})

    if charts:
        return render_template('mydashboard.html', charts=charts)

    return render_template_string("No results available")

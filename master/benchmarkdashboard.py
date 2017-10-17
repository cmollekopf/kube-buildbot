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
    benchmarksToRun = [{"hawd_def": "mail_query",
                        "render": ["simple", "threadleader"],
                        "absoluteAxis": False},
                       {"hawd_def": "mail_query_incremental",
                        "render": ["nonincremental", "incremental"],
                        "absoluteAxis": True},
                       {"hawd_def": "dummy_write_memory",
                        "render": [
                            {"name" :"rss",
                             "filter": ("rows", 5000)
                            },
                            {"name" :"rssWithoutDb",
                             "filter": ("rows", 5000)
                            },
                        ],
                        "absoluteAxis": True},
                       {"hawd_def": "dummy_write_perf",
                        "render": [
                            {"name" :"append",
                             "filter": ("rows", 5000)
                            },
                            {"name" :"total",
                             "filter": ("rows", 5000)
                            },
                        ],
                        "absoluteAxis": True},
                       {"hawd_def": "dummy_write_disk",
                        "render": [
                            {"name" :"onDisk",
                             "filter": ("rows", 5000)
                            },
                            {"name" :"bufferSize",
                             "filter": ("rows", 5000)
                            },
                        ],
                        "absoluteAxis": True},
                       {"name": "Write amplification",
                        "hawd_def": "dummy_write_disk",
                        "render": [
                            {"name" :"writeAmplification",
                             "filter": ("rows", 2000)},
                            {"name" :"writeAmplification",
                             "filter": ("rows", 5000)},
                            {"name" :"writeAmplification",
                             "filter": ("rows", 20000)},
                        ],
                        "absoluteAxis": True},
                       {"hawd_def": "dummy_write_summary",
                        "render": ["rssStandardDeviation", "timeStandardDeviation"],
                        "absoluteAxis": True},
                      ]
    charts = []

    for benchmark in benchmarksToRun:
        output = subprocess.check_output("{}/testenv.py srcbuild --noninteractive kube Sink hawd json {}".format(config.dockerdir, benchmark["hawd_def"]), shell=True, stderr=subprocess.STDOUT)
        # log.msg("Output: ", output)
        if output:
            hawdResult = json.loads(output)
            graph_data = {}
            units = {}
            names = {}
            data = sorted(hawdResult['rows'], key=lambda row: row['timestamp'])
            for renderable in benchmark["render"]:
                for row in data:
                    skip = False
                    if isinstance(renderable, dict):
                        columnToRender = renderable["name"]
                        f = renderable["filter"]
                    else:
                        columnToRender = renderable
                        f = {}

                    if f:
                        for c in row['columns']:
                            if c['name'] == f[0] and c['value'] != f[1]:
                                skip = True
                                break
                    if skip:
                        continue

                    # log.msg("Columns: ", row['columns'])
                    for c in row['columns']:
                        name = c['name']
                        if f:
                            name = name + " f(%s=%s)" % (f[0], f[1])
                        if c['name'] == columnToRender:
                            #We aggregate by column name
                            if name not in graph_data:
                                graph_data[name] = []
                            graph_data[name].append(dict(x=len(graph_data[name]), y=c['value']))
                            units[name] = c['unit']
                            names[name] = name


            datasets=[]
            for name, data in graph_data.items():
                datasets.append({"name": names[name],
                    "data": data,
                    "unit": units[name]
                    })

            graphName = hawdResult['name']
            if 'name' in benchmark:
                graphName = benchmark['name']

            charts.append({"id": hawdResult['dataset'] + graphName,
                        "name": graphName,
                        "description": hawdResult['description'],
                        "datasets": datasets,
                        "absoluteAxis": benchmark["absoluteAxis"]})

    if charts:
        return render_template('mydashboard.html', charts=charts)

    return render_template_string("No results available")

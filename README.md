# Setup

## Install
    mkdir venv
    virtualenv venv
    source venv/bin/activate
    pip install 'buildbot[bundle]'
    pip install flask
    pip install buildbot-wsgi-dashboards
    pip install buildbot-worker

## Setup
    buildbot create-master master/
    buildbot-worker create-worker worker localhost:9989 example-worker pass
    cp master/master.cfg.sample master/master.cfg
    buildbot start master

    => check master/twisted.log for errors if it failed.

    buildbot-worker start worker


from . import benchmarkdashboard

def getWWW():
    www = {
            'port':8010,
            'plugins': {
                'waterfall_view':{},
                'console_view':{},
                'grid_view':{},
                'wsgi_dashboards': [  # This is a list of dashboards, you can create several
                    {
                        'name': 'benchmarks',  # as used in URLs
                        'caption': 'Benchmarks',  # Title displayed in the UI'
                        'app': benchmarkdashboard.benchmarkdashboard,
                        # priority of the dashboard in the left menu (lower is higher in the
                        # menu)
                        'order': 5,
                        # available icon list can be found at http://fontawesome.io/icons/
                        'icon': 'area-chart'
                    }
                ]
            }
        }
    return www

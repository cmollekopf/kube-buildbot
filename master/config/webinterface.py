from . import benchmarkdashboard
from buildbot.plugins import util

def getWWW():
    www = {
            'port':8010,
            'authz': util.Authz(
                allowRules=[
                    util.AnyEndpointMatcher(role="admins")
                ],
                roleMatchers=[util.RolesFromUsername(roles=["admins"], usernames=["kube"])]
            ),
            'plugins': {
                'waterfall_view':{},
                'console_view':{},
                'grid_view':{},
                'badges':{},
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

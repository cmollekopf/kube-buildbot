# The 'workers' list defines the set of recognized workers. Each element is
# a Worker object, specifying a unique worker name and password.  The same
# worker name and password must be configured on the worker.

from buildbot.plugins import worker

def get_workers(localworkerpool):
    workers = []
    for workername in localworkerpool:
        workers.append(worker.LocalWorker(workername))
    workers.append(worker.Worker('osx-worker', 'osxpw'))
    workers.append(worker.Worker('win-worker', 'winpw'))
    return workers

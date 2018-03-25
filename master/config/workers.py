# The 'workers' list defines the set of recognized workers. Each element is
# a Worker object, specifying a unique worker name and password.  The same
# worker name and password must be configured on the worker.

from buildbot.worker import LocalWorker

def get_workers(workerpool):
    workers = []
    for workername in workerpool:
        workers.append(LocalWorker(workername))
    return workers

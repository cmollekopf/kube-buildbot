# Configure the Schedulers, which decide how to react to incoming changes.

from buildbot.schedulers.basic import SingleBranchScheduler
from buildbot.schedulers.forcesched import ForceScheduler


def get_schedulers(builderNames, codebases):

    # sched_all = SingleBranchScheduler(name='all',
    #                                   branch='master',
    #                                   codebases=codebases,
    #                                   treeStableTimer=300,
    #                                   builderNames=[build])

    # sched_force = ForceScheduler(name='force',
    #                              codebases=codebases,
    #                              builderNames=[build])

    sched_all = SingleBranchScheduler(
                            name='all',
                            codebases=codebases,
                            change_filter=util.ChangeFilter(project='kube', branch=['master', 'develop']),
                            treeStableTimer=60,
                            builderNames = builderNames)

    sched_force = schedulers.ForceScheduler(
                            name = "force",
                            codebases = kube_codebases.keys(),
                            builderNames = builderNames)

    return [sched_all, sched_force]

# Build and run tests at 2 o'clock
# nightlyRebuildScheduler = schedulers.Nightly(name='nightly-rebuild',
#                                     builderNames=['debugbuild', 'releasebuild', 'asanbuild'],
#                                     hour=2, minute=0)
# c['schedulers'].append(nightlyRebuildScheduler)
# # Build a nightly flatpak if the test pass
# c['schedulers'].append(schedulers.Dependent(name='nightly-flatpak',
#                                             upstream=nightlyRebuildScheduler,
#                                             builderNames=['nightlyflatpak']))

#Run benchmarks ever night at 3 o'clock (let's hope the system isn't busy at that point)
# c['schedulers'].append(schedulers.Nightly(name='nightly-benchmark',
#                                     builderNames=['benchmarkkube'],
#                                     hour=3, minute=0))

# c['schedulers'].append(schedulers.Nightly(name='nightly-loadtest',
#                                     builderNames=['debugbuild-loadtest'],
#                                     hour=4, minute=0))

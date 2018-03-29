# Configure the Schedulers, which decide how to react to incoming changes.

from buildbot.plugins import util
from buildbot.plugins import schedulers


def get_schedulers(builderNames, codebases):
    schedulerList = []
    schedulerList.append(schedulers.SingleBranchScheduler(
                            name='all',
                            codebases=codebases,
                            change_filter=util.ChangeFilter(project='kube', branch=['master', 'develop']),
                            treeStableTimer=60,
                            builderNames = builderNames))

    schedulerList.append(schedulers.ForceScheduler(
                            name = "force",
                            codebases = list(codebases.keys()),
                            builderNames = builderNames,
                            properties=[
                                util.BooleanParameter(name="cleanbuild",
                                                    label="Clean build",
                                                    default=False)
                            ]
                            ))

    # Build and run tests at 2 o'clock
    nightlyRebuildScheduler = schedulers.Nightly(name='nightly-rebuild',
                                        builderNames=['debugbuild', 'releasebuild', 'asanbuild'],
                                        codebases=codebases,
                                        properties = {
                                            'cleanbuild': True
                                        },
                                        hour=2, minute=0)
    schedulerList.append(nightlyRebuildScheduler)
    # Build a nightly flatpak if the tests pass
    schedulerList.append(schedulers.Dependent(name='nightly-flatpak',
                                                upstream=nightlyRebuildScheduler,
                                                builderNames=['nightlyflatpak']))
    # Build a nightly osx image if the tests pass
    schedulerList.append(schedulers.Dependent(name='nightly-osx',
                                                upstream=nightlyRebuildScheduler,
                                                builderNames=['osxbuild']))

    #Run benchmarks ever night at 3 o'clock (let's hope the system isn't busy at that point)
    schedulerList.append(schedulers.Nightly(name='nightly-benchmark',
                                        builderNames=['benchmarkkube'],
                                        codebases=codebases,
                                        hour=3, minute=0))

    # schedulerList.append(schedulers.Nightly(name='nightly-loadtest',
    #                                     builderNames=['debugbuild-loadtest'],
    #                                     hour=4, minute=0))

    return schedulerList


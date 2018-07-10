# Configure the Schedulers, which decide how to react to incoming changes.

from buildbot.plugins import util
from buildbot.plugins import schedulers


def get_schedulers(builderNames, codebases):
    schedulerList = []
    schedulerList.append(schedulers.SingleBranchScheduler(
                            name='all',
                            codebases=codebases,
                            change_filter=util.ChangeFilter(branch=['master', 'develop']),
                            treeStableTimer=60,
                            properties = {
                                'cleanbuild': False,
                                'runtests': True,
                                'upload': False
                            },
                            builderNames = builderNames))

    schedulerList.append(schedulers.ForceScheduler(
                            name = "force",
                            codebases = list(codebases.keys()),
                            builderNames = builderNames,
                            properties=[
                                util.BooleanParameter(name="cleanbuild",
                                                    label="Clean build",
                                                    default=False),
                                util.BooleanParameter(name="runtests",
                                                    label="Run tests",
                                                    default=True),
                                util.BooleanParameter(name="upload",
                                                    label="Upload result",
                                                    default=False),
                            ]
                            ))

    # Build and run tests at 2 o'clock
    nightlyRebuildScheduler = schedulers.Nightly(name='nightly-rebuild',
                                        builderNames=['debugbuild', 'releasebuild', 'asanbuild'],
                                        codebases=codebases,
                                        properties = {
                                            'cleanbuild': True,
                                            'runtests': True
                                        },
                                        hour=2, minute=0)
    schedulerList.append(nightlyRebuildScheduler)
    # Build a nightly flatpak if the tests pass
    schedulerList.append(schedulers.Dependent(name='nightly-flatpak',
                                                upstream=nightlyRebuildScheduler,
                                                properties = {
                                                    'upload': True
                                                },
                                                builderNames=['nightlyflatpak', 'kolabnowflatpak']))
    # Build a nightly osx image if the tests pass
    schedulerList.append(schedulers.Dependent(name='nightly-osx',
                                                upstream=nightlyRebuildScheduler,
                                                properties = {
                                                    'upload': True
                                                },
                                                builderNames=['osxbuild', 'kolabnowosxbuild']))

    #Run benchmarks ever night at 3 o'clock (let's hope the system isn't busy at that point)
    schedulerList.append(schedulers.Nightly(name='nightly-benchmark',
                                        builderNames=['benchmarkkube'],
                                        codebases=codebases,
                                        properties = {
                                            'cleanbuild': True,
                                            'runtests': False
                                        },
                                        hour=3, minute=0))

    # schedulerList.append(schedulers.Nightly(name='nightly-loadtest',
    #                                     builderNames=['debugbuild-loadtest'],
    #                                     hour=4, minute=0))

    return schedulerList


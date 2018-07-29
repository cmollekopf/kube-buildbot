# The 'builders' list defines the Builders, which tell Buildbot how to perform a build:
# what steps, and which slaves can execute them. Note that any particular build will
# only take place on one slave.


import os
from buildbot.config import BuilderConfig
from buildbot.plugins import util
from buildbot.plugins import steps

def get_builders(codebases, workerpool):

    def kubeBuildFactory(buildConfig):
        f = util.BuildFactory()

        def dockerCommand(cmd, workdir, extra_args=""):
            return "docker run --rm {extra_args} -v $PWD/src:/src -v $PWD/build:/build -v $PWD/install:/install -w {workdir} kubedev bash -c '{cmd}'".format(
                    extra_args=extra_args,
                    workdir=workdir,
                    cmd=cmd)

        def dockerCmd(cmd, workdir, haltOnFailure=True):
            return util.ShellArg(command = dockerCommand(cmd, workdir), logfile='output', haltOnFailure=haltOnFailure)


        #The codebases argument is necessary to avoid inheriting the branch from the poller on the wrong repository.
        f.addStep(steps.Git(repourl=codebases['kasync']['repository'], codebase='kasync', branch='master', workdir='src/kasync'))
        f.addStep(steps.Git(repourl=codebases['kdav2']['repository'], codebase='kdav2', branch='master', workdir='src/kdav2'))
        f.addStep(steps.Git(repourl=codebases['kimap2']['repository'], codebase='kimap2', branch='master', workdir='src/kimap2'))
        f.addStep(steps.Git(repourl=codebases['sink']['repository'], codebase='sink', branch='develop', workdir='src/sink'))
        f.addStep(steps.Git(repourl=codebases['kube']['repository'], codebase='kube', branch='develop', workdir='src/kube'))

        f.addStep(steps.ShellSequence(name = 'buildDockerImage',
            commands = [
                util.ShellArg(
                    command = 'docker build -t kubedev .',
                    logfile = 'output',
                    haltOnFailure=True)
            ],
            workdir = 'src/kube/docker',
            haltOnFailure=True
            ))

        f.addStep(steps.ShellSequence(name = 'cleanup',
            commands = [
                util.ShellArg(
                    command = 'rm -R  $PWD/build;'
                            + 'rm -R $PWD/install;',
                    logfile='output',
                    haltOnFailure=False),
            ],
            workdir = './',
            haltOnFailure=False,
            doStepIf=lambda(step): step.getProperty('cleanbuild')
            ))
        f.addStep(steps.ShellSequence(name = 'prepare',
            commands = [
                util.ShellArg(
                    command = 'mkdir -p $PWD/build;'
                            + 'mkdir -p $PWD/install;',
                    logfile='output',
                    haltOnFailure=True),
            ],
            workdir = './',
            haltOnFailure=True
            ))

        #Setup buildsteps for all repos
        for repo in buildConfig['repos']:
            sourcedir="/src/{}".format(repo['name'])
            builddir="/build/{}".format(repo['name'])
            f.addStep(steps.ShellSequence(name = repo['name'],
                commands = [
                    dockerCmd("mkdir -p {}".format(builddir), "/"),
                    dockerCmd("cmake {options} {sourcedir}".format(options=repo['cmake'], sourcedir=sourcedir), builddir)
                ],
                haltOnFailure=True,
                workdir='./'
                ))
            f.addStep(steps.Compile(name = "compile {}".format(repo['name']),
                command=dockerCommand("make -j `nproc` && make install", builddir),
                haltOnFailure=True,
                workdir='./'
                ))

        if 'tests' in buildConfig:
            for test in buildConfig['tests']:
                name = "{}: {}".format(test['workdir'], test['command'])
                timeout = 1200
                if 'timeout' in test:
                    timeout = test['timeout']

                docker_options_x11 = '-t --security-opt seccomp:unconfined -v /tmp/.docker.xauth:/tmp/.docker.xauth -v /tmp/.X11-unix:/tmp/.X11-unix --device /dev/dri/card0:/dev/dri/card0 -e DISPLAY=:0 -e XAUTHORITY=/tmp/.docker.xauth'
                f.addStep(steps.Test(name=name,
                    command=dockerCommand(test['command'],
                        test['workdir'],
                        docker_options_x11),
                    timeout=timeout,
                    doStepIf=lambda(step): step.getProperty('runtests'),
                    workdir='./'))
        return f


    def buildConfigurations():
        cmake_options="-DCMAKE_PREFIX_PATH=/install -DCMAKE_INSTALL_PREFIX=/install -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DCMAKE_C_COMPILER=/usr/bin/clang -DCMAKE_CXX_COMPILER=/usr/bin/clang++"
        debug_cmake_options = cmake_options + ' -DCMAKE_BUILD_TYPE=debug'
        release_cmake_options = cmake_options + ' -DCMAKE_BUILD_TYPE=release'
        asan_options = "ASAN_OPTIONS=detect_odr_violation=0,symbolize=1,fast_unwind_on_malloc=0,check_initialization_order=1,detect_deadlocks=1"
        lsan_options = "LSAN_OPTIONS=suppressions=/src/sink/suppressions.lsan"
        builds = {
            'debugbuild': {
                        'repos': [{'name': 'kasync', 'cmake': debug_cmake_options},
                                    {'name': 'kdav2', 'cmake': debug_cmake_options},
                                    {'name': 'kimap2', 'cmake': debug_cmake_options},
                                    {'name': 'sink', 'cmake': debug_cmake_options + ' -DENABLE_MEMCHECK=OFF -DCATCH_ERRORS=ON'},
                                    {'name': 'kube', 'cmake': debug_cmake_options},
                        ],
                        'tests': [
                            {'command': '/home/developer/startimap.sh && ctest -V', 'workdir': '/build/sink'},
                            {'command': 'xvfb-run -s "-screen 0 640x480x24" ctest -V', 'workdir': '/build/kube'}
                        ]
            },
            # 'debugbuild-loadtest': {
            #                'sourcedir': "~/src",
            #                'builddir': "~/src/debug/build",
            #                'installdir': "~/src/debug/install",
            #                'repos': [],
            #                'tests': [
            #                    {'command': 'tests/sinkloadtest.py', 'workdir': '/src/sink', 'timeout': 35 * 60}
            #                ]
            # },
            'releasebuild': {
                            'repos': [{'name': 'kasync', 'cmake': release_cmake_options},
                                    {'name': 'kdav2', 'cmake': release_cmake_options},
                                    {'name': 'kimap2', 'cmake': release_cmake_options},
                                    {'name': 'sink', 'cmake': release_cmake_options},
                                    {'name': 'kube', 'cmake': release_cmake_options},
                            ]
            },
            'asanbuild': {
                        'repos': [{'name': 'kasync', 'cmake': debug_cmake_options},
                                    {'name': 'kdav2', 'cmake': debug_cmake_options},
                                    {'name': 'kimap2', 'cmake': debug_cmake_options},
                                    {'name': 'sink', 'cmake': debug_cmake_options + ' -DENABLE_ASAN=TRUE -DENABLE_MEMCHECK=OFF'}
                        ],
                        'tests': [
                            {'command': "{} {} /home/developer/startimap.sh && ctest -E \"modelinteractivity*\" -V".format(asan_options, lsan_options), 'workdir': '/build/sink'}
                        ]
            }
        }
        return builds



    def benchmarkkube():
        docker_options_x11 = '-t --security-opt seccomp:unconfined -v /tmp/.docker.xauth:/tmp/.docker.xauth -v /tmp/.X11-unix:/tmp/.X11-unix --device /dev/dri/card0:/dev/dri/card0 -e DISPLAY=:0 -e XAUTHORITY=/tmp/.docker.xauth'

        def dockerCommand(cmd, workdir, extra_args=""):
            return "docker run --rm {extra_args} -v ~/hawd:/home/developer/hawd -v $PWD/src:/src -v $PWD/build:/build -v $PWD/install:/install -w {workdir} kubedev bash -c '{cmd}'".format(
                    extra_args=extra_args,
                    workdir=workdir,
                    cmd=cmd)

        f = kubeBuildFactory(buildConfigurations()["releasebuild"])

        f.addStep(steps.ShellSequence(name = 'prepare hawd',
            commands = [
                util.ShellArg(
                    command = 'mkdir -p ~/hawd',
                    logfile='output',
                    haltOnFailure=True),
                util.ShellArg(
                    command = 'echo "{\\\"results\\\": \\\"~/hawd\\\", \\\"project\\\": \\\"$PWD/src/sink/hawd_defs\\\"}" > ~/hawd.conf',
                    logfile='output',
                    haltOnFailure=True),
            ],
            workdir = './',
            haltOnFailure=True
            ))

        def addSinkBenchmark(cmd):
            f.addStep(steps.ShellCommand(name=cmd, command=dockerCommand(cmd, '/build/sink', docker_options_x11), workdir='./'))

        addSinkBenchmark('tests/mailquerybenchmark')
        addSinkBenchmark('tests/dummyresourcebenchmark')
        addSinkBenchmark('tests/dummyresourcewritebenchmark')
        addSinkBenchmark('tests/dummyresourcebenchmark')
        addSinkBenchmark('tests/storagebenchmark')
        addSinkBenchmark('tests/pipelinebenchmark')
        addSinkBenchmark('/home/developer/startimap.sh && QTEST_FUNCTION_TIMEOUT=1800000 examples/imapresource/tests/imapmailsyncbenchmark')
        # addSinkBenchmark('tests/databasepopulationandfacadequerybenchmark')
        return f

    #FIXME
    flatpakdir = os.path.expanduser('~') + "/flatpak/"

    def kolabnowflatpak():
        f = util.BuildFactory()
        f.addStep(
            steps.ShellCommand(command="{}/rebuildkolabnow.sh".format(flatpakdir), haltOnFailure=True)
        )
        f.addStep(steps.ShellCommand(command="{}/uploadkolabnow.sh".format(flatpakdir),
            doStepIf=lambda(step): step.getProperty('upload')
        ))
        return f

    def nightlyflatpak():
        f = util.BuildFactory()
        f.addStep(
            steps.ShellCommand(command="{}/rebuild.sh".format(flatpakdir), haltOnFailure=True)
        )
        f.addStep(steps.ShellCommand(command="{}/upload.sh".format(flatpakdir),
            doStepIf=lambda(step): step.getProperty('upload')
        ))
        return f

    def osxbuild():
        f = util.BuildFactory()
        craftRoot = '/Users/kolab/CraftRoot'
        dmgName = 'kube.dmg'
        f.addStep(steps.ShellSequence(name = 'craft',
            commands = [
                util.ShellArg(command = [r'craft/bin/craft.py', '--install-deps', '--fetch', '--unpack', '--compile', '--install', 'extragear/sink'], logfile='output', haltOnFailure=True),
                util.ShellArg(command = [r'craft/bin/craft.py', '--install-deps', '--fetch', '--unpack', '--compile', '--install', '--package', 'extragear/kube'], logfile='output', haltOnFailure=True),
            ],
            haltOnFailure=True,
            workdir = craftRoot,
            env = {
                "MACOSX_DEPLOYMENT_TARGET": "10.9.0",
                "SDKROOT": "/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk/",
                "PATH": ["/usr/local/Cellar/gettext/0.19.8.1/bin", "${PATH}"],
                "CMAKE_LIBRARY_PATH": "/usr/local/Cellar/gettext/0.19.8.1/lib",
                "CMAKE_INCLUDE_PATH": "/usr/local/Cellar/gettext/0.19.8.1/include"
            }
            ))
        f.addStep(steps.ShellSequence(name = 'validate',
            commands = [
                util.ShellArg(command = ['mkdir', '-p', 'tmp/mountpoint'], logfile='output', haltOnFailure=False),
                util.ShellArg(command = ['hdiutil', 'attach', '-mountpoint', 'tmp/mountpoint', "tmp/%s" % dmgName], logfile='output', haltOnFailure=True),
                util.ShellArg(command = ['tmp/mountpoint/kube.app/Contents/MacOS/sinksh', 'selftest'], logfile='output', haltOnFailure=True),
                util.ShellArg(command = ['hdiutil', 'detach', 'tmp/mountpoint'], logfile='output', haltOnFailure=True),
            ],
            haltOnFailure = True,
            workdir = craftRoot,
            ))
        f.addStep(steps.FileUpload(workersrc="tmp/%s" % dmgName,
                           masterdest="/home/mollekopf/%s" % dmgName,
                           workdir = craftRoot
                           ))
        f.addStep(steps.MasterShellCommand(name = 'Upload to mirror',
            command = ["scp", "-B", "/home/mollekopf/%s" % dmgName, "kube-project@10.4.2.23:/var/www/vhosts/kube-project.com/files.kube-project.com/"],
            doStepIf=lambda(step): step.getProperty('upload')
            ))
        return f

    def kolabnowosxbuild():
        f = util.BuildFactory()
        craftRoot = '/Users/kolab/CraftRoot'
        dmgName = 'kube-kolabnow.dmg'
        f.addStep(steps.ShellSequence(name = 'craft',
            commands = [
                util.ShellArg(command = [r'craft/bin/craft.py', '--install-deps', '--fetch', '--unpack', '--compile', '--install', '--qmerge', 'extragear/sink'], logfile='output', haltOnFailure=True),
                util.ShellArg(command = [r'craft/bin/craft.py', '--install-deps', '--fetch', '--unpack', '--compile', '--install', '--qmerge', '--package', 'extragear/kube-kolabnow'], logfile='output', haltOnFailure=True),
            ],
            haltOnFailure=True,
            workdir = craftRoot,
            env = {
                "MACOSX_DEPLOYMENT_TARGET": "10.9.0",
                "SDKROOT": "/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX.sdk/",
                "PATH": ["/usr/local/Cellar/gettext/0.19.8.1/bin", "${PATH}"],
                "CMAKE_LIBRARY_PATH": "/usr/local/Cellar/gettext/0.19.8.1/lib",
                "CMAKE_INCLUDE_PATH": "/usr/local/Cellar/gettext/0.19.8.1/include"
            }
            ))
        f.addStep(steps.ShellSequence(name = 'validate',
            commands = [
                util.ShellArg(command = ['mkdir', '-p', 'tmp/mountpoint'], logfile='output', haltOnFailure=False),
                util.ShellArg(command = ['hdiutil', 'attach', '-mountpoint', 'tmp/mountpoint', "tmp/%s" % dmgName], logfile='output', haltOnFailure=True),
                util.ShellArg(command = ['tmp/mountpoint/kube-kolabnow.app/Contents/MacOS/sinksh', 'selftest'], logfile='output', haltOnFailure=True),
                util.ShellArg(command = ['hdiutil', 'detach', 'tmp/mountpoint'], logfile='output', haltOnFailure=True),
            ],
            haltOnFailure = True,
            workdir = craftRoot,
            ))
        f.addStep(steps.FileUpload(workersrc="tmp/%s" % dmgName,
                           masterdest="/home/mollekopf/%s" % dmgName,
                           workdir = craftRoot
                           ))
        f.addStep(steps.MasterShellCommand(name = 'Upload to mirror',
            command = ["scp", "-B", "/home/mollekopf/%s" % dmgName, "kube-project@10.4.2.23:/var/www/vhosts/kube-project.com/files.kube-project.com/"],
            doStepIf=lambda(step): step.getProperty('upload')
            ))
        return f

    def winbuild():
        f = util.BuildFactory()
        f.addStep(steps.ShellSequence(name = 'craft',
            commands = [
                util.ShellArg(command = [r'craft\bin\craft.py', '--install-deps', '--fetch', '--unpack', '--compile', '--install', 'extragear/sink'], logfile='output', haltOnFailure=True),
                util.ShellArg(command = [r'craft\bin\craft.py', '--install-deps', '--fetch', '--unpack', '--compile', '--install', '--package', 'extragear/kube'], logfile='output', haltOnFailure=True),
            ],
            haltOnFailure=True,
            workdir = 'C:\Users\User\CraftRoot'
            ))
        f.addStep(steps.FileUpload(workersrc='tmp/kube-latest-windows-msvc2017_64-clang.exe',
                           masterdest='/home/mollekopf/kube.exe',
                           workdir = 'C:\Users\User\CraftRoot'
                           ))
        f.addStep(steps.MasterShellCommand(name = 'Upload to mirror',
            command = ["scp", "-B", "/home/mollekopf/kube.exe", "kube-project@10.4.2.23:/var/www/vhosts/kube-project.com/files.kube-project.com/"],
            doStepIf=lambda(step): step.getProperty('upload')
            ))
        return f

    flatpak_lock = util.MasterLock("flatpak")
    osx_lock = util.MasterLock("osx")
    benchmark_lock = util.WorkerLock("benchmark", maxCount=99)

    builders = []
    #Setup all builders
    for name, buildConfig in buildConfigurations().items():
        builders.append(util.BuilderConfig(name=name, workernames=workerpool, factory=kubeBuildFactory(buildConfig), locks=[benchmark_lock.access('counting')]))

    builders.append(util.BuilderConfig(name="benchmarkkube", workernames=workerpool, factory=benchmarkkube(), locks=[benchmark_lock.access('exclusive')]))
    builders.append(util.BuilderConfig(name="kolabnowflatpak", workernames=workerpool, factory=kolabnowflatpak(), locks=[flatpak_lock.access('exclusive'), benchmark_lock.access('counting')]))
    builders.append(util.BuilderConfig(name="nightlyflatpak", workernames=workerpool, factory=nightlyflatpak(), locks=[flatpak_lock.access('exclusive'), benchmark_lock.access('counting')]))
    builders.append(util.BuilderConfig(name="osxbuild", workernames=["osx-worker"], factory=osxbuild(), locks=[osx_lock.access('exclusive'), benchmark_lock.access('counting')]))
    builders.append(util.BuilderConfig(name="kolabnowosxbuild", workernames=["osx-worker"], factory=kolabnowosxbuild(), locks=[osx_lock.access('exclusive'), benchmark_lock.access('counting')]))
    builders.append(util.BuilderConfig(name="winbuild", workernames=["win-worker"], factory=winbuild(), locks=[benchmark_lock.access('counting')]))
    return builders


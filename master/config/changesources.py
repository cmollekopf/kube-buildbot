# the 'change_source' setting tells the buildmaster how it should find out
# about source code changes.
# The default polliterval is 10 minutes which is sufficient.


from buildbot.changes.gitpoller import GitPoller
from buildbot.plugins import changes


def get_sources(codebases):
    sources = []
    # for k, v in codebases.items():
    #     sources.append(GitPoller(repourl=v["repository"], branch=v['branch']))
    sources.append(changes.PBChangeSource(port=9999, user='user', passwd='userpw'))
    sources.append(GitPoller(repourl='git://anongit.kde.org/sink', branches=['master', 'develop']))
    sources.append(GitPoller(repourl='git://anongit.kde.org/kube', branches=['master', 'develop']))

    return sources

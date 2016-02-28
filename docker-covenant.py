#!/usr/bin/python
import os.path
import sys
import syslog
import yaml
from docker import Client

confFile = 'docker-covenant.yml'
client = Client(base_url='unix://var/run/docker.sock', version='auto')
events = client.events(decode=True)
syslog.openlog(ident="docker-covenant")

if os.path.isfile(confFile):
    with open(confFile, 'r') as f:
        conf = yaml.safe_load(f)
else:
    print "Config file %s doesn't exist." % (confFile)
    sys.exit(1)

try:
    if conf["debug"]:
        print client.info()

except (NameError):
    pass

for container in events:
    try:
        containerStop = False
        if "create" in container['status']:
            try:
                containerEventID = container['Actor']['ID']
                containerInspect = client.inspect_container(containerEventID)
                containerId = containerInspect["Id"]
                containerName = containerInspect["Name"].replace('/', '')

                containerPrivileged = containerInspect["HostConfig"]["Privileged"]
                containerCapDrop = containerInspect["HostConfig"]["CapDrop"]
                containerCapAdd = containerInspect["HostConfig"]["CapAdd"]

                try:
                    if conf["debug"]:
                        print container['status']
                        print "containerEventID: %s" % (containerEventID)
                        print "containerInspect: %s" % (client.inspect_container(containerEventID))
                        print "containerID: %s" % (containerInspect["Id"])
                        print "containerPrivileged: %s" % (containerPrivileged)
                        print "containerCapDrop: %s" % (containerCapDrop)
                        print "containerCapAdd: %s" % (containerCapAd)
                        print "containerStop: %s" % (containerStop)
                except (NameError):
                    pass

                privNotAllowedLog = "%s: privileged set but not allowed" % (containerName)
                privNoPolicyLog = "%s: privileged set but no policy" % (containerName)
                capDropLog = "%s: all capabilities not dropped" % (containerName)
                capAddAllLog = "%s: capability ALL has been set" % (containerName)
                stopContainer = "%s: stopping container" % (containerName)

                try:
                    if containerPrivileged is not False:
                        if not conf[containerName]['privileged']:
                            syslog.syslog(privNotAllowedLog)
                            containerStop = True

                except (KeyError):
                    syslog.syslog(privNoPolicyLog)
                    containerStop = True

                try:
                    if containerCapDrop is not None:
                        for capDrop in containerCapDrop:
                            if "all" not in capDrop.lower() and conf[containerName]['cap_drop_required']:
                                print capDrop.lower()
                                print conf[containerName]['cap_drop_required']
                                syslog.syslog(capDropLog)
                                containerStop = True

                except (KeyError):
                    syslog.syslog(capDropLog)
                    containerStop = True

                try:
                    if containerCapDrop is None:
                        if conf[containerName]['cap_drop_required']:
                            syslog.syslog(capDropLog)
                            containerStop = True

                except (KeyError):
                    syslog.syslog(capDropLog)
                    containerStop = True

                if containerCapAdd is not None:
                    for capAdd in containerCapAdd:
                        if "all" in capAdd.lower():
                            syslog.syslog(capAddAllLog)
                            containerStop = True

                try:
                    if conf["debug"]:
                        print "containerStop: %s" % (containerStop)
                        print "client.stop(%s) sent" % (clientStop)

                except (NameError):
                    pass

                if containerStop and containerStop is not False:
                    clientStop = "%s" % (containerId)

                    try:
                        if conf["debug"]:
                            print "containerStop: %s" % (containerStop)
                            print "client.stop(%s) sent" % (clientStop)

                    except (NameError):
                        pass

                    try:
                        client.stop(clientStop)
                        syslog.syslog(stopContainer)

                    except Exception, e:
                        print str(e)

            except Exception, e:
                print str(e)

    except (KeyError):
        pass

#!/usr/bin/env python
import os.path
import sys
import syslog
import yaml
from docker import Client


def dockerClient():
    global client, events

    client = Client(base_url='unix://var/run/docker.sock', version='auto')
    events = client.events(decode=True)


def config():
    global conf

    confFile = 'docker-covenant.yml'

    if os.path.isfile(confFile):
        with open(confFile, 'r') as f:
            conf = yaml.safe_load(f)

            if conf["debug"]:
                print("configuration file: ", confFile)
    else:
        print("Config file ", confFile, " doesn't exist.")
        sys.exit(1)

    try:
        if not conf["syslog_ident"]:
            logident = "docker-covenant"
        else:
            logident = conf["syslog_ident"]

        syslog.openlog(ident=logident)

        if conf["debug"]:
            print("syslog_ident ", logident)

    except (NameError):
        pass

    try:
        if conf["debug"]:
            print("Docker daemon info:\n", client.info())

    except (NameError):
        pass


def main():
    for container in events:
        try:
            containerStop = False
            if "start" in container['status']:
                try:
                    containerEventID = container['Actor']['ID']
                    containerInspect = client.inspect_container(containerEventID)
                    containerId = containerInspect["Id"]
                    containerName = containerInspect["Name"].replace('/', '')

                    containerCapDrop = containerInspect["HostConfig"]["CapDrop"]
                    containerCapAdd = containerInspect["HostConfig"]["CapAdd"]
                    containerPrivileged = containerInspect["HostConfig"]["Privileged"]
                    containerSecurityOpt = containerInspect["HostConfig"]["SecurityOpt"]

                    noSecurityOpt = "%s: no security options has been set" % (containerName)
                    privNotAllowedLog = "%s: privileged set but not allowed" % (containerName)
                    privNoPolicyLog = "%s: privileged set but no policy" % (containerName)
                    capDropLog = "%s: all capabilities not dropped" % (containerName)
                    capAddAllLog = "%s: capability ALL has been set" % (containerName)
                    stopContainerLog = "%s: stopping container" % (containerName)

                    try:
                        if conf["debug"]:
                            print("containerName: ", containerName)
                            print("containerStatus: ", container['status'])
                            print("containerEventID: ", containerEventID)
                            print("containerInspect: ", client.inspect_container(containerEventID))
                            print("containerID: ", containerInspect["Id"])
                            print("containerCapDrop: ", containerCapDrop)
                            print("containerCapAdd: ", containerCapAdd)
                            print("containerSecurityOpt: ", containerSecurityOpt)
                            print("containerPrivileged: ", containerPrivileged)
                            print("containerStop: ", containerStop)

                    except (NameError):
                        pass

                    try:
                        if containerPrivileged is not False:
                            if not conf[containerName]['privileged']:
                                syslog.syslog(privNotAllowedLog)
                                containerStop = True

                    except (KeyError):
                        syslog.syslog(privNoPolicyLog)
                        containerStop = True

                    try:
                        if containerSecurityOpt is None:
                            if conf[containerName]['security_opt_required']:
                                syslog.syslog(noSecurityOpt)
                                containerStop = True

                                if conf["debug"]:
                                    print("containerSecurityOpt: ", containerSecurityOpt)

                    except (KeyError):
                        syslog.syslog(noSecurityOpt)
                        containerStop = True

                    try:
                        if containerCapDrop is not None:
                            for capDrop in containerCapDrop:
                                if "all" not in capDrop.lower() and not conf[containerName]['cap_drop_required']:
                                    syslog.syslog(capDropLog)
                                    containerStop = True

                                    if conf["debug"]:
                                        print("capDrop: ", capDrop.lower())
                                        print("capDropRequired: ", conf[containerName]['cap_drop_required'])

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
                            print("containerStop: ", containerStop)
                            print("client.stop(", clientStop, ")")

                    except (NameError):
                        pass

                    if containerStop and containerStop is not False:
                        clientStop = "%s" % (containerId)

                        try:
                            if conf["debug"]:
                                print("containerStop: ", containerStop)
                                print("client.stop sent to ", clientStop)

                        except (NameError):
                            pass

                        try:
                            client.stop(clientStop)
                            syslog.syslog(stopContainerLog)

                        except (Exception) as e:
                            print(e)

                except (Exception) as e:
                    print(e)

        except (KeyError):
            pass


if __name__ == "__main__":
    dockerClient()
    config()
    main()

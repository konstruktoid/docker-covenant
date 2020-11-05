#!/usr/bin/env python3
"""Enforces a basic container argument policy."""
import os.path
import sys
import syslog
import yaml
import docker

CLIENT = None
CONF = None
EVENTS = None


def docker_client():
    """Get Docker events."""
    global CLIENT, EVENTS

    CLIENT = docker.APIClient()
    EVENTS = CLIENT.events(decode=True)


def config():
    """Read the configuration file"""
    global CONF

    configuration_file = "docker-covenant.yml"

    if os.path.isfile(configuration_file):
        with open(configuration_file, "r") as conf_file:
            CONF = yaml.safe_load(conf_file)

            if CONF["debug"]:
                print(("configuration file: ", configuration_file))
    else:
        print(("Config file ", configuration_file, " doesn't exist."))
        sys.exit(1)

    try:
        if not CONF["syslog_ident"]:
            logident = "docker-covenant"
        else:
            logident = CONF["syslog_ident"]

        syslog.openlog(ident=logident)

        if CONF["debug"]:
            print(("syslog_ident ", logident))

    except NameError:
        pass

    try:
        if CONF["debug"]:
            print(("Docker daemon info:\n", CLIENT.info()))

    except NameError:
        pass


def main():
    """Get container information and act on it."""
    for container in EVENTS:
        try:
            container_stop = False
            if "start" in container["status"]:
                try:
                    container_event_id = container["Actor"]["ID"]
                    container_inspect = CLIENT.inspect_container(container_event_id)
                    container_id = container_inspect["Id"]
                    container_name = container_inspect["Name"].replace("/", "")

                    container_cap_drop = container_inspect["HostConfig"]["CapDrop"]
                    container_cap_add = container_inspect["HostConfig"]["CapAdd"]
                    container_privileged = container_inspect["HostConfig"]["Privileged"]
                    container_security_opt = container_inspect["HostConfig"][
                        "SecurityOpt"
                    ]

                    no_security_opt = "%s: no security options has been set" % (
                        container_name
                    )
                    priv_not_allowed_log = "%s: privileged set but not allowed" % (
                        container_name
                    )
                    priv_no_policy_log = "%s: privileged set but no policy" % (
                        container_name
                    )
                    cap_drop_log = "%s: all capabilities not dropped" % (container_name)
                    cap_add_all_log = "%s: capability ALL has been set" % (
                        container_name
                    )
                    stop_container_log = "%s: stopping container" % (container_name)

                    try:
                        if CONF["debug"]:
                            print(("container_name: ", container_name))
                            print(("containerStatus: ", container["status"]))
                            print(("container_event_id: ", container_event_id))
                            print(
                                (
                                    "container_inspect: ",
                                    CLIENT.inspect_container(container_event_id),
                                )
                            )
                            print(("containerID: ", container_inspect["Id"]))
                            print(("container_cap_drop: ", container_cap_drop))
                            print(("container_cap_add: ", container_cap_add))
                            print(("container_security_opt: ", container_security_opt))
                            print(("container_privileged: ", container_privileged))
                            print(("container_stop: ", container_stop))

                    except NameError:
                        pass

                    try:
                        if container_privileged is not False:
                            if not CONF[container_name]["privileged"]:
                                syslog.syslog(priv_not_allowed_log)
                                container_stop = True

                    except KeyError:
                        syslog.syslog(priv_no_policy_log)
                        container_stop = True

                    try:
                        if container_security_opt is None:
                            if CONF[container_name]["security_opt_required"]:
                                syslog.syslog(no_security_opt)
                                container_stop = True

                                if CONF["debug"]:
                                    print(
                                        (
                                            "container_security_opt: ",
                                            container_security_opt,
                                        )
                                    )

                    except KeyError:
                        syslog.syslog(no_security_opt)
                        container_stop = True

                    try:
                        if container_cap_drop is not None:
                            for cap_drop in container_cap_drop:
                                if (
                                    "all" not in cap_drop.lower()
                                    and not CONF[container_name]["cap_drop_required"]
                                ):
                                    syslog.syslog(cap_drop_log)
                                    container_stop = True

                                    if CONF["debug"]:
                                        print(("cap_drop: ", cap_drop.lower()))
                                        print(
                                            (
                                                "cap_dropRequired: ",
                                                CONF[container_name][
                                                    "cap_drop_required"
                                                ],
                                            )
                                        )

                    except KeyError:
                        syslog.syslog(cap_drop_log)
                        container_stop = True

                    try:
                        if container_cap_drop is None:
                            if CONF[container_name]["cap_drop_required"]:
                                syslog.syslog(cap_drop_log)
                                container_stop = True

                    except KeyError:
                        syslog.syslog(cap_drop_log)
                        container_stop = True

                    if container_cap_add is not None:
                        for cap_add in container_cap_add:
                            if "all" in cap_add.lower():
                                syslog.syslog(cap_add_all_log)
                                container_stop = True

                    if container_stop and container_stop is not False:
                        client_stop = "%s" % (container_id)

                        try:
                            if CONF["debug"]:
                                print(("container_stop: ", container_stop))
                                print(("CLIENT.stop sent to ", client_stop))

                        except NameError:
                            pass

                        try:
                            CLIENT.stop(client_stop)
                            syslog.syslog(stop_container_log)

                        except UnboundLocalError as exception:
                            print(exception)

                        except KeyError as exception:
                            print(exception)

                except UnboundLocalError as exception:
                    print(exception)

                except KeyError as exception:
                    print(exception)

        except KeyError:
            pass


if __name__ == "__main__":
    docker_client()
    config()
    main()

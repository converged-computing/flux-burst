# Copyright 2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

import base64
import os

import requests
from kubernetes import client as kubernetes_client

import fluxburst.defaults as defaults
import fluxburst.utils as utils


def get_minicluster(
    command,
    size=None,
    tasks=None,  # nodes * cpu per node, where cpu per node is vCPU / 2
    cpu_limit=None,
    memory_limit=None,
    flags=None,
    name=None,
    namespace=None,
    image=None,
    wrap=None,
    log_level=7,
    flux_user=None,
    lead_host=None,
    lead_port=None,
    broker_toml=None,
    munge_secret_name=None,
    curve_cert_secret_name=None,
    curve_cert=None,
    lead_size=None,
    lead_jobname=None,
    zeromq=False,
    quiet=False,
    strict=False,
):
    """
    Get a MiniCluster CRD as a dictionary

    Limits should be slightly below actual pod resources. The curve cert and broker config
    are required, since we need this external cluster to connect to ours!
    """
    flags = flags or "-ompi=openmpi@5 -c 1 -o cpu-affinity=per-task"
    image = image or "ghcr.io/flux-framework/flux-restful-api"
    container = {"image": image, "command": command, "resources": {}}

    # Are we bursting?
    doing_burst = lead_port and lead_size and lead_jobname
    if cpu_limit is None and memory_limit is None:
        del container["resources"]
    elif cpu_limit is not None or memory_limit is not None:
        container["resources"] = {"limits": {}, "requests": {}}
    if cpu_limit is not None:
        container["resources"]["limits"]["cpu"] = cpu_limit
        container["resources"]["requests"]["cpu"] = cpu_limit
    if memory_limit is not None:
        container["resources"]["limits"]["memory"] = memory_limit
        container["resources"]["requests"]["memory"] = memory_limit

    # Do we have a custom flux user for the container?
    if flux_user:
        container["flux_user"] = {"name": flux_user}

    # The MiniCluster has the added name and namespace
    mc = {
        "size": size,
        "namespace": namespace,
        "name": name,
        "interactive": False,
        "logging": {"zeromq": zeromq, "quiet": quiet, "strict": strict},
        "flux": {
            "option_flags": flags,
            "connect_timeout": "5s",
            "log_level": log_level,
        },
    }

    # Are we bursting?
    # Providing the lead broker and port points back to the parent
    if doing_burst:
        mc["flux"]["bursting"] = {
            "lead_broker": {
                "address": lead_host,
                "port": int(lead_port),
                "name": lead_jobname,
                "size": int(lead_size),
            },
            "clusters": [{"size": size, "name": name}],
        }

    if tasks is not None:
        mc["tasks"] = tasks

    # This is text directly in config
    if doing_burst and curve_cert:
        mc["flux"]["curve_cert"] = curve_cert

    # A provided secret will take precedence
    if doing_burst and curve_cert_secret_name:
        mc["flux"]["curve_cert_secret"] = curve_cert_secret_name

    # This is just the secret name
    if doing_burst and munge_secret_name:
        mc["flux"]["munge_secret"] = munge_secret_name
    if broker_toml:
        mc["flux"]["broker_config"] = broker_toml

    # eg., this would require strace "strace,-e,network,-tt"
    if wrap is not None:
        mc["flux"]["wrap"] = wrap
    return mc, container


def ensure_curve_cert(curve_cert):
    """
    Ensure we are provided with an existing curve certificate we can load.
    """
    if not curve_cert or not os.path.exists(curve_cert):
        raise ValueError(
            f"Curve cert (provided as {curve_cert}) needs to be defined and exist."
        )
    return utils.read_file(curve_cert)


def ensure_flux_operator_yaml(flux_operator_yaml):
    """
    Ensure we are provided with the installation yaml and it exists!
    """
    # flux operator yaml default is current from main
    if not flux_operator_yaml:
        flux_operator_yaml = utils.get_tmpfile(prefix="flux-operator") + ".yaml"
        r = requests.get(defaults.flux_operator_yaml, allow_redirects=True)
        utils.write_file(r.text, flux_operator_yaml)

    # Ensure it really really exists
    flux_operator_yaml = os.path.abspath(flux_operator_yaml)
    if not os.path.exists(flux_operator_yaml):
        raise ValueError(f"{flux_operator_yaml} does not exist.")
    return flux_operator_yaml


def create_secret(path, secret_path, name, namespace, mode="r"):
    """
    Create a secret
    """
    # Configureate ConfigMap metadata
    metadata = kubernetes_client.V1ObjectMeta(
        name=name,
        namespace=namespace,
    )
    # Get File Content
    with open(path, mode) as f:
        content = f.read()

    # base64 encoded string
    if mode == "rb":
        content = base64.b64encode(content).decode("utf-8")

    # Instantiate the configmap object
    return kubernetes_client.V1Secret(
        api_version="v1",
        kind="Secret",
        type="opaque",
        string_data={secret_path: content},
        metadata=metadata,
    )

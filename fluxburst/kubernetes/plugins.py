# Copyright 2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)


import os
import socket

from fluxoperator.client import FluxMiniCluster
from kubernetes import client as kubernetes_client
from kubernetes import utils as k8sutils
from kubernetes.client.rest import ApiException

import fluxburst.kubernetes.cluster as helpers
from fluxburst.logger import logger
from fluxburst.plugins import BurstPlugin


class KubernetesBurstPlugin(BurstPlugin):
    """
    An additional wrapper to the plugin that adds support for the Flux Operator
    """

    def ensure_namespace(self, kubectl):
        """
        Use the instantiated kubectl to ensure the cluster namespace exists.
        """
        try:
            kubectl.create_namespace(
                kubernetes_client.V1Namespace(
                    metadata=kubernetes_client.V1ObjectMeta(name=self.params.namespace)
                )
            )
        except Exception:
            logger.warning(
                f"🥵️ Issue creating namespace {self.params.namespace}, assuming already exists."
            )

    def validate(self):
        """
        Validate ensures that required conditions are met.

        This should return True/False to indicate if the plugin is valid or not.
        """
        # If we aren't doing an isolated burst, we require host names, configs, etc.
        if not self.params.isolated_burst:
            # Lead host and port are required. A custom broker.toml can be provided,
            # but we are having the operator create it for us
            if (
                not self.params.lead_port
                or not self.params.lead_host
                or not self.params.lead_size
            ):
                logger.warning(
                    "Parameteres lead_host, lead_size, and lead_port must be defined when not doing an isolated_burst."
                )
                return False

            print(
                f"Broker lead will be accessible on {self.params.lead_host}:{self.params.lead_port}"
            )

            # We also need to have the munge key and curve cert
            if self.params.munge_key and not os.path.exists(self.params.munge_key):
                logger.warning(
                    f"Provided munge key {self.params.munge_key} does not exist."
                )
                return False
        return True

    def check_configs(self):
        """
        Ensure we have required config files.
        """
        message = "does not exist or you don't have permissions to see it"
        if not os.path.exists(self.params.munge_key):
            raise ValueError(f"Provided munge key {self.params.munge_key} {message}.")

        if not os.path.exists(self.params.curve_cert):
            raise ValueError(f"Provided curve cert {self.params.munge_key} {message}.")

    def install_flux_operator(self, kubectl, flux_operator_yaml):
        """
        Install the flux operator yaml
        """
        try:
            k8sutils.create_from_yaml(kubectl.api_client, flux_operator_yaml)
            logger.info("Installed the operator.")
        except Exception as exc:
            logger.warning(
                f"Issue installing the operator: {exc}, assuming already exists"
            )

    def run(self, request_burst=False, nodes=None, tasks=None):
        """
        Given some set of scheduled jobs, run bursting.

        If request_burst is True, a specific number of tasks and size
        must be provided to request a cluster in advance (that jobs can
        be run on).
        """
        # Exit early if no jobs to burst
        if not self.jobs:
            logger.info(f"Plugin {self.name} has no jobs to burst.")
            return

        # If we have requested a burst, tasks and size are required
        if request_burst and (not tasks or not nodes):
            logger.warning("Burst requests require nodes and tasks.")
            return

        # Ensure we have a flux operator yaml file, fosho, foyaml!
        foyaml = helpers.ensure_flux_operator_yaml(self.params.flux_operator_yaml)

        # lead host / port / size / are required in the dataclass
        # But ONLY if this isnt' an isolated burst!
        # We check munge paths here, because could be permissions issue
        if not self.params.isolated_burst:
            self.check_configs()

        # This call registers the name of the cluster to self.clusters
        cli = self.create_cluster()
        kubectl = cli.get_k8s_client()

        # Install the operator!
        self.install_flux_operator(kubectl, foyaml)

        # Are we requesting or running jobs?
        if request_burst:
            self.create_minicluster(kubectl, "sleep infinity", nodes, tasks)
        else:
            self.run_jobs(kubectl)

    def run_jobs(self, kubectl):
        """
        Run jobs (creating MiniClusters), assuming that the burst has been done.
        """
        # Create a MiniCluster for each job
        for _, job in self.jobs.items():
            command = " ".join(job["spec"]["tasks"][0]["command"])
            self.create_minicluster(kubectl, command, job["nnodes"], job["ntasks"])

    def create_minicluster(self, kubectl, command, nodes, tasks):
        """
        Create the MiniCluster
        """
        logger.info(f"Preparing MiniCluster for {command}")

        # The plugin is assumed to be running from the lead broker
        # of the cluster it is bursting from, this we get info about it
        podname = socket.gethostname()
        hostname = podname.rsplit("-", 1)[0]

        # TODO: we are using defaults for now, but will update this to be likely
        # configured based on the algorithm that chooses the best spec
        minicluster, container = helpers.get_minicluster(
            command,
            name=self.params.name,
            memory_limit=self.params.memory_limit,
            cpu_limit=self.params.cpu_limit,
            namespace=self.params.namespace,
            broker_toml=self.params.broker_toml,
            tasks=tasks,
            size=nodes,
            image=self.params.image,
            wrap=self.params.wrap,
            log_level=self.params.log_level,
            flux_user=self.params.flux_user,
            lead_host=self.params.lead_host,
            lead_port=self.params.lead_port,
            munge_secret_name=self.params.munge_secret_name,
            curve_cert_secret_name=self.params.curve_cert_secret_name,
            lead_jobname=hostname,
            lead_size=self.params.lead_size,
        )
        # Create the namespace
        self.ensure_namespace(kubectl)

        # Let's assume there could be bugs applying this differently
        crd_api = kubernetes_client.CustomObjectsApi(kubectl.api_client)

        # These are not needed if we are doing an isolated burst
        if not self.params.isolated_burst:
            self.ensure_secrets(kubectl)

        # Create the MiniCluster! This also waits for it to be ready
        print(
            f"⭐️ Creating the minicluster {self.params.name} in {self.params.namespace}..."
        )

        # Make sure we provide the core_v1_api we've created
        operator = FluxMiniCluster(core_v1_api=kubectl)
        try:
            return operator.create(**minicluster, container=container, crd_api=crd_api)
        except Exception as e:
            print(f"Issue creating cluster, does it already exist?: {e}")
            return True

    def ensure_secrets(self, kubectl):
        """
        Ensure secrets (munge.key and curve.cert) are ready for a job
        """
        secrets = []

        # kubectl create secret --namespace flux-operator munge-key --from-file=/etc/munge/munge.key
        if self.params.curve_cert:
            secrets.append(
                helpers.create_secret(
                    self.params.curve_cert,
                    "curve.cert",
                    self.params.curve_cert_secret_name,
                    self.params.namespace,
                )
            )

        if self.params.munge_key:
            secrets.append(
                helpers.create_secret(
                    self.params.munge_key,
                    "munge.key",
                    self.params.munge_secret_name,
                    self.params.namespace,
                    mode="rb",
                )
            )

        for secret in secrets:
            try:
                logger.debug(f"Creating secret {secret.metadata.name}")
                kubectl.create_namespaced_secret(
                    namespace=self.params.namespace,
                    body=secret,
                )
            except ApiException as e:
                print(
                    "Exception when calling CoreV1Api->create_namespaced_config_map: %s\n"
                    % e
                )

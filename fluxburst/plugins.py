# Copyright 2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

import importlib
import os
import pkgutil
from dataclasses import dataclass

import fluxburst.defaults as defaults
from fluxburst.logger import logger

# Executor plugins are externally installed plugins named "snakemake_executor_<name>"
# They should follow the same convention if on pip, snakemake-executor-<name>
burstable_plugins = {
    name.replace(defaults.plugin_prefix, ""): importlib.import_module(name)
    for _, name, _ in pkgutil.iter_modules()
    if name.startswith(defaults.plugin_prefix)
}


@dataclass
class BurstParameters:
    pass


class BurstPlugin:
    """
    The base class for a burst plugin defines needed functions.
    """

    # Default dataclass is essentially empty
    _param_dataclass = BurstParameters

    def __init__(self, dataclass, **kwargs):
        self.set_params(dataclass)

        # Set of jobs assigned to be bursted, and bursted clusters
        self.jobs = {}
        self.clusters = {}

    def schedule(self, job):
        """
        Attempt to schedule a job, if possible.
        """
        raise NotImplementedError

    def run(self, *args, **kwargs):
        """
        Main function to run a plugin with the set of burstable jobs.
        """
        raise NotImplementedError

    def cleanup(self, name=None):
        pass

    def refresh_clusters(self, clusters):
        """
        Update known clusters from a list of those removed.
        """
        updated = {}
        for name in self.clusters:
            if name not in clusters:
                updated[name] = self.clusters[name]
        self.clusters = updated

    def set_params(self, dc):
        """
        Given known parameters, assert we have the correct dataclass
        and update from the environment, etc.

        The dc (dataclass) is used by the plugin as a generic strategy
        to select and move around custom arguments, if needed.
        """
        # The dataclass expected for the plugin must match what is provided
        if not isinstance(dc, self._param_dataclass):
            raise ValueError(
                f"Incorrect dataclass provided, found {dc} and want {self._param_dataclass}"
            )

        # Get params from the environment, which take precedence
        for key, value in os.environ.items():
            if not key.startswith("FLUXBURST_"):
                continue
            key = key.replace("FLUXBURST_", "").lower()
            if hasattr(dc, key):
                logger.debug(f"Found {key} in environment.")
                setattr(dc, key, value)

        # At this point we want to convert the args <dataclasses> back into dataclass
        self.params = dc

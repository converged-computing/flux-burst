# Copyright 2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

import importlib
import pkgutil
from dataclasses import dataclass

import fluxburst.defaults as defaults

# Executor plugins are externally installed plugins named "snakemake_executor_<name>"
# They should follow the same convention if on pip, snakemake-executor-<name>
executor_plugins = {
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

    _param_dataclass = BurstParameters

    def __init__(self, **kwargs):
        self.set_params(**kwargs)

        # Set of jobs assigned to be bursted
        self.jobs = {}

    def schedule(self, *args, **kwargs):
        """
        Attempt to schedule a job, if possible.
        """
        raise NotImplementedError

    def run(self, *args, **kwargs):
        """
        Main function to run a plugin with the set of burstable jobs.
        """
        raise NotImplementedError

    def set_params(self, **kwargs):
        """
        Given known parameters, set on dataclass.

        The dataclass is used by the plugin as a generic strategy
        to select and move around custom arguments, if needed.
        """
        params = {}

        # Only derive those provided by the dataclass
        for arg in dir(self._param_dataclass):
            if arg in kwargs:
                params[arg] = kwargs[arg]

        # At this point we want to convert the args <dataclasses> back into dataclass
        self.params = self._param_dataclass(**kwargs)

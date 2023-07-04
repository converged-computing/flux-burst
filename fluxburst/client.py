# Copyright 2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

import collections

import fluxburst.handles as handles
import fluxburst.selectors as selectors
import fluxburst.sorting as sorting
from fluxburst.logger import logger

from .plugins import burstable_plugins


class FluxBurst:
    """
    Flux Burst Client
    """

    def __init__(self, handle=None, mock=False, validate=True):
        """
        Create a new burst client.

        Selectors: Process the current queue and add flags/filter jobs for plugins.
        Plugins: take jobs that need bursting, and burst some subset.
        A filter can (on the simplest terms) just look for a job flagged as
        burstable. For more complex cases, it can perform it's own logic and
        flag some subset as burstable instead. Validation is always done for
        the top level module, howevert the validate boolean here determines
        if the plugin should run its own validation function.
        """
        self.reset_selector()
        self.reset_plugins()
        self.flux = handles.FluxMock(handle) if mock else handles.FluxHandle(handle)
        self.set_ordering(sorting.in_order)
        self.validate = validate

    @property
    def choices(self):
        return "|".join(list(self.plugins))

    def load(self, name, dataclass, **kwargs):
        """
        Register a bursting plugin manually.

        We assume a setup does not always want all plugins available.
        The dataclass argument should be for the BurstParameters
        specific to the plugin.
        """
        if name not in burstable_plugins:
            raise ValueError(f"Plugin {name} is not known. Choices are {self.choices}")

        # Validate the plugin, first plugin module then loaded class
        self.validate_module(name)
        plugin = burstable_plugins[name].init(dataclass)

        # We set the name attribute so it's always matched to the module
        plugin.name = name
        self.check_plugin_integrity(plugin)

        # If the plugin does it's own validation, do here
        if not self.validate_plugin(plugin):
            logger.warning(f"Plugin {name} did not validate and cannot be added.")
            return

        self.plugins[name] = plugin

    def validate_module(self, name):
        """
        Validate the structure of the module.

        We currently just require the init function to import and return the class
        """
        if not hasattr(burstable_plugins[name], "init"):
            raise ValueError(
                f"Plugin {name} is missing required init attribute to return BurstPlugin class."
            )

    def validate_plugin(self, plugin):
        """
        Validate a plugin, and if valid, load into module.
        """
        # This should return a boolean for valid or not
        if hasattr(plugin, "validate") and self.validate:
            return plugin.validate()
        return True

    def check_plugin_integrity(self, plugin):
        """
        Validate a plugin, and if valid, load into module.
        """
        required_attributes = ["schedule", "run", "_param_dataclass", "set_params"]
        for required in required_attributes:
            if not hasattr(plugin, required):
                raise ValueError(
                    f"Plugin {plugin.name} is not valid, missing attribute or function {required}"
                )

    def set_selector(self, func):
        """
        Register a job filter or selector for select_jobs.
        """
        self._job_selector = func

    def reset_plugins(self):
        self.plugins = collections.OrderedDict()

    def reset_selector(self):
        self._job_selector = selectors.is_burstable

    def run_burst(self, request_burst=False, nodes=None, tasks=None):
        """
        A full run burst includes:

        1. Selecting jobs using the client filter(s)
        2. In the order of plugins desired, schedule jobs
        3. Return back lookup of scheduled (by plugin)

        If request_burst with nodes and tasks are required, each plugin
        will simply request creation for the size/tasks needed.
        """
        # TODO what to do with unmatched jobs?
        unmatched = self.process_queue()

        # When we get here, run the bursts
        for _, plugin in self.iter_plugins():
            plugin.run(request_burst=request_burst, nodes=nodes, tasks=tasks)
        return unmatched

    def request_burst(self, name, nodes, tasks):
        """
        Request burst is a direct handle to get a plugin and request a burst.

        In this case, we do not create MiniClusters to launch jobs to, but instead
        create a connected cluster anticipating receiving jobs.
        """
        plugin = self.plugins.get(name)
        if not plugin:
            logger.warning(f"Plugin {plugin} is not known.")
            return
        return plugin.run(request_burst=True, nodes=nodes, tasks=tasks)

    def set_ordering(self, func):
        """
        Set a custom function that knows how to yield names, plugins.
        """
        self._iter_func = func

    def iter_plugins(self):
        """
        Custom function to iterate over plugins
        """
        if not self._iter_func:
            self._iter_func = sorting.in_order

        for name, plugin in self._iter_func(self.plugins):
            yield name, plugin

    def process_queue(self):
        """
        Process queue is the entrypoint to run one burst cycle.

        We first apply any selectors to the queue, and then hand the
        resulting filtered jobs off to burstable plugins. There could be
        more fine-tuned logic for directing jobs to plugins.
        """
        # Run filters across queue to select jobs
        # This is a dict, keys with job id, values jobinfo
        jobs = self.select_jobs()

        # Going through plugins, determine if matches and can run
        unmatched = []
        for _, job in jobs.items():
            scheduled = False
            for _, plugin in self.iter_plugins():
                # Give to first burstable plugin that can accept
                if plugin.schedule(job):
                    # Remove the burstable attribute so it isn't assigned to another
                    # This is more for development - we could likely use a better way
                    self.mark_as_scheduled(job, plugin.name)
                    scheduled = True
                    break

            # But if we cannot match, return to caller
            if not scheduled:
                unmatched.append(job)

        if unmatched:
            logger.warning(f"There are {len(unmatched)} jobs that cannot be bursted.")
        return unmatched

    def mark_as_scheduled(self, job, plugin_name):
        """
        Mark a job as scheduled.

        For now, we just remove the burstable attribute to indicate
        that it's been scheduled. We also add the plugin it was scheduled
        with, in case we somehow need to regenerate/remember a burst.
        """
        # Add an attribute that says "this job is assigned to burstable plugin X"
        job["spec"]["attributes"]["system"]["burst-scheduled"] = plugin_name

        # The job is no longer marked as burstable for other plugins
        if "burstable" in job["spec"]["attributes"]["system"]:
            del job["spec"]["attributes"]["system"]["burstable"]

        # Update the KVS (is this possible)?
        # This doesn't currently work, so not doing anything :)
        self.flux.update_jobspec(job)

    def select_jobs(self):
        """
        Use filters to select jobs.

        This step is agnostic to the burstable plugins - it is simply
        deducing (via our selector function) what jobs are contenders
        for bursting. See the README / documentation for example info.
        """
        # Keep track of selected burstable jobs by id
        listing = self.flux.list_jobs()
        selected = {}

        for job in listing.get("jobs", []):
            info = self.flux.get_job_info(job["id"])
            if not self._job_selector(info):
                continue
            print(f"🧋️  Job {job['id']} is marked for bursting.")
            selected[job["id"]] = info

        # We don't give a warning here, because likely there aren't
        # jobs that are burstable (it's a more rare event)
        return selected

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "[flux-burst-client]"

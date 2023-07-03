# Copyright 2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)


# We define a FluxHandle class to also provide a mock handle,
# meaning we aren't running flux, but can provide fake jobs


class FluxMock:
    """
    A mock flux handle that will return fake jobs, etc.

    This class does not require importing Flux and can be used
    for testing cases or similar.
    """

    def __init__(self, *args, **kwargs):
        pass

    def update_jobspec(self, job):
        """
        Update a jobspec via the kvs
        """
        pass

    def list_jobs(self):
        """
        List one fake, burstable job.

        Generated via:
        flux submit -N 4 --cwd /tmp --setattr=burstable hostname
        in the fluxrm/flux-sched:focal container on July 2nd 2023. Note that we
        only use the high level attributes so hosts, etc. do not matter.
        """
        return {
            "jobs": [
                {
                    "id": 17839985524736,
                    "userid": 1002,
                    "urgency": 16,
                    "priority": 16,
                    "t_submit": 1688329701.680035,
                    "t_depend": 1688329701.693167,
                    "t_run": 1688329701.709494,
                    "t_cleanup": 1688329701.7517478,
                    "t_inactive": 1688329701.753637,
                    "state": 64,
                    "name": "hostname",
                    "cwd": "/tmp",
                    "ntasks": 4,
                    "ncores": 16,
                    "duration": 0.0,
                    "nnodes": 4,
                    "ranks": "[0-3]",
                    "nodelist": "84bd2c990b[15,15,15,15]",
                    "success": True,
                    "exception_occurred": False,
                    "result": 1,
                    "expiration": 4841929701.0,
                    "waitstatus": 0,
                }
            ]
        }

    def get_job_info(self, jobid):
        """
        Get job info. This is job info (the same function called on the container)
        job returned above) in the fluxrm/flux-sched:focal container.
        """
        return {
            "id": 17839985524736,
            "userid": 1002,
            "urgency": 16,
            "priority": 16,
            "t_submit": 1688329701.680035,
            "t_depend": 1688329701.693167,
            "t_run": 1688329701.709494,
            "t_cleanup": 1688329701.7517478,
            "t_inactive": 1688329701.753637,
            "state": 64,
            "name": "hostname",
            "cwd": "/tmp",
            "ntasks": 4,
            "ncores": 16,
            "duration": 0.0,
            "nnodes": 4,
            "ranks": "[0-3]",
            "nodelist": "84bd2c990b[15,15,15,15]",
            "success": True,
            "exception_occurred": False,
            "result": 1,
            "expiration": 4841929701.0,
            "waitstatus": 0,
            "info": {
                "_t_depend": 1688329701.693167,
                "_t_run": 1688329701.709494,
                "_t_cleanup": 1688329701.7517478,
                "_t_inactive": 1688329701.753637,
                "_duration": 0.0,
                "_expiration": 4841929701.0,
                "_name": "hostname",
                "_cwd": "/tmp",
                "_queue": "",
                "_ntasks": 4,
                "_ncores": 16,
                "_nnodes": 4,
                "_priority": 16,
                "_ranks": "[0-3]",
                "_nodelist": "84bd2c990b[15,15,15,15]",
                "_success": True,
                "_waitstatus": 0,
                "_id": 17839985524736,
                "_userid": 1002,
                "_urgency": 16,
                "_t_submit": 1688329701.680035,
                "_exception_occurred": False,
                "_state_id": 64,
                "_result_id": 1,
                "_exception": {
                    "occurred": False,
                    "severity": "",
                    "type": "",
                    "note": "",
                },
                "_annotations": {"annotationsDict": {}, "atuple": ()},
                "_sched": None,
                "_user": None,
                "_dependencies": [],
            },
            "spec": {
                "resources": [
                    {
                        "type": "node",
                        "count": 4,
                        "exclusive": True,
                        "with": [
                            {
                                "type": "slot",
                                "count": 1,
                                "with": [{"type": "core", "count": 1}],
                                "label": "task",
                            }
                        ],
                    }
                ],
                "tasks": [
                    {"command": ["hostname"], "slot": "task", "count": {"per_slot": 1}}
                ],
                "attributes": {
                    "system": {
                        "duration": 0,
                        "cwd": "/tmp",
                        "shell": {
                            "options": {
                                "rlimit": {
                                    "cpu": -1,
                                    "fsize": -1,
                                    "data": -1,
                                    "stack": 8388608,
                                    "core": -1,
                                    "nofile": 1048576,
                                    "as": -1,
                                    "rss": -1,
                                    "nproc": -1,
                                }
                            }
                        },
                        "burstable": 1,
                    }
                },
                "version": 1,
            },
        }


class FluxHandle:
    def __init__(self, handle=None):
        import flux

        self.handle = handle or flux.Flux()

    def update_jobspec(self, job):
        """
        Update a jobspec via the kvs
        """
        import flux.job

        # Update the KVS (is this possible)?
        # This doesn't currently work, so not doing anything :)
        kvs = flux.job.job_kvs(self.handle, job["id"])
        kvs["jobspec"] = job["spec"]
        kvs.commit()
        return kvs

    def list_jobs(self):
        """
        List actual jobs from the flux.job module
        """
        import flux.job

        return flux.job.job_list(self.handle).get()

    def get_job_info(self, jobid):
        """
        Get job info based on an id

        Also retrieve the full job info and jobspec.
        This is not yet currently perfectly json serializable, need to
        handle EmptyObject if that is desired.
        """
        import flux.job

        fluxjob = flux.job.JobID(jobid)
        payload = {"id": fluxjob, "attrs": ["all"]}
        rpc = flux.job.list.JobListIdRPC(self.handle, "job-list.list-id", payload)
        job = rpc.get_job()

        # Job info, timing, priority, etc.
        job["info"] = rpc.get_jobinfo().__dict__
        job["info"]["_exception"] = job["info"]["_exception"].__dict__
        job["info"]["_annotations"] = job["info"]["_annotations"].__dict__

        # the KVS will have annotations!
        kvs = flux.job.job_kvs(self.handle, jobid)
        job["spec"] = kvs.get("jobspec")
        return job

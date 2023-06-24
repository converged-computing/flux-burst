# Copyright 2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)


def is_burstable(jobinfo):
    """
    Determine if a job is burstable if:

    1. It is flagged as burstable
    """
    return "burstable" in jobinfo["spec"]["attributes"]["system"]

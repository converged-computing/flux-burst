# Copyright 2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)


def in_order(plugins):
    """
    Plugins is expected to be an ordered dict, return in order

    This is designed intending to be flexible. We can add
    additional metadata if needed
    """
    for name, plugin in plugins.items():
        yield name, plugin

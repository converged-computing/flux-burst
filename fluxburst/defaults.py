# Copyright 2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)


import os

import fluxburst.utils as utils

install_dir = utils.get_installdir()
reps = {"$install_dir": install_dir, "$root_dir": os.path.dirname(install_dir)}

# Default plugin prefix
plugin_prefix = "fluxburst_"

# User home
userhome = os.path.expanduser("~/.fluxburst")

# The default GitHub registry with recipes (for docgen)
github_url = "https://github.com/converged-computing/flux-burst"

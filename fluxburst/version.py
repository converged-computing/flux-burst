# Copyright 2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

__version__ = "0.0.12"
AUTHOR = "Vanessa Sochat"
EMAIL = "vsoch@users.noreply.github.com"
NAME = "flux-burst"
PACKAGE_URL = "https://github.com/converged-computing/flux-burst"
KEYWORDS = "cloud, flux-framework, flux, bursting"
DESCRIPTION = "Flux module that enables burstable plugins."
LICENSE = "LICENSE"

################################################################################
# Global requirements

INSTALL_REQUIRES = (
    ("ruamel.yaml", {"min_version": None}),
    ("jsonschema", {"min_version": None}),
    ("rich", {"min_version": None}),
    ("oras", {"min_version": None}),
    ("requests", {"min_version": None}),
    ("pick", {"min_version": None}),
)

INSTALL_REQUIRES_KUBERNETES = (
    ("kubernetes", {"min_version": None}),
    ("fluxoperator", {"min_version": None}),
)

TESTS_REQUIRES = (("pytest", {"min_version": "4.6.2"}),)

################################################################################
# Submodule Requirements (versions that include database)

INSTALL_REQUIRES_ALL = INSTALL_REQUIRES + INSTALL_REQUIRES_KUBERNETES + TESTS_REQUIRES

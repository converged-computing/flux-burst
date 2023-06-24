# Copyright 2023 Lawrence Livermore National Security, LLC and other
# HPCIC DevTools Developers. See the top-level COPYRIGHT file for details.
#
# SPDX-License-Identifier: (MIT)

import copy

from pick import pick


def chunks(listing, chunk_size):
    """
    Yield successive chunks from listing. Chunkify!
    """
    for i in range(0, len(listing), chunk_size):
        yield listing[i : i + chunk_size]


def slugify(name):
    """
    Slugify a name, replacing spaces with - and lowercase.
    """
    for char in [" ", ":", "/", "\\"]:
        name = name.replace(char, "-")
    return name.lower()


def print_bytes(byt, suffix="B"):
    """
    Pretty format size in bytes
    """
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(byt) < 1024.0:
            return f"{byt:3.1f} {unit}{suffix}"
        byt /= 1024.0
    return f"{byt:.1f} Yi{suffix}"


def mb_to_bytes(mb):
    """
    Convert mb to bytes, usually so we can derive a better format.
    """
    return mb * (1048576)


def choose(options, prompt, default_index=0):
    """
    Use pick to choose one of a few options, return the chosen option.
    """
    return pick(options, prompt, indicator="=>", default_index=default_index)


def get_hash(obj):
    """
    Get a hash for a random object (set, tuple, list, dict)

    All nested attributes must at least be hashable!
    """
    if isinstance(obj, (set, tuple, list)):
        return tuple([get_hash(o) for o in obj])
    if not isinstance(obj, dict):
        return hash(obj)
    copied = copy.deepcopy(obj)
    for k, v in copied.items():
        copied[k] = get_hash(v)
    return hash(tuple(frozenset(sorted(copied.items()))))

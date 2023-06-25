# Flux Burst

<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-1-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->
[![PyPI](https://img.shields.io/pypi/v/flux-burst)](https://pypi.org/project/flux-burst/)

<!--<a target="_blank" rel="noopener noreferrer" href="https://github.com/converged-computing/flux-burst/blob/main/docs/assets/img/logo-transparent.png">
    <img align="right" style="width: 250px; float: right; padding-left: 20px;" src="https://github.com/converged-computing/flux-burst/raw/main/docs/assets/img/logo-transparent.png" alt="Cloud Select Logo">
</a>-->

This will be a plugin (somewhere) that controls Flux bursting. 🧋️

## Frequently Asked Questions

> What is a burst?

A traditional burst means extening some local Flux Cluster with a remote. That "remote" can actually be:

- a cloud cluster (existing or not)
- a second cluster
- a mocked cluster

The main idea is that the main Flux Cluster is not just creating additional resources, but connecting
the local broker to the new external one. This is different from what we might consider an isolated
burst, where a first cluster creates an entirely new second cluster.

> How does the design here work?

This library uses a plugin architecture, meaning that if you want to add a new kind of burstable,
you do so by way of writing a plugin. Instructions for writing a plugin are included below.

## Usage

### Tutorial

For this tutorial you will need Docker installer.

[Flux-framework](https://flux-framework.org/) is a flexible resource scheduler that can work on both high performance computing systems and cloud (e.g., Kubernetes).
Since it is more modern (e.g., has an official Python API) we define it under a cloud resource. For this example, we will show you how to set up a "single node" local
Flux container to interact with the bursting plugin here. You can use the [Dockerfile](examples/Dockerfile) that will provide a container with Flux and flux burst
First, build the container and shell in:

```bash
$ docker build -f examples/Dockerfile -t flux-burst .
$ docker run -it flux-snake bash
```

And start a flux instance:

```bash
$ flux start --test-size=4
```

**under development**

### Customization

The Flux burst module does the following:

 1. Discovers burstable plugins on the system that start with `fluxburst_<name>`
 2. Load one or more plugins of your choosing with `client.load(...)`
 3. On a call to run:
   a. We call the filter function to select jobs that are candidates for bursting (via any plugin)
   b. We use a default (or customized) bursting selection function (e.g., controlling logic for how to choose a plugin)
   c. We iterate through our plugins, and assign matched jobs to burst
   d. We run the bursts

From the above, this means that you can customize the following:

- The plugins discovered as available on the system
- The plugins you choose to load for a particular instance
- The filter or selection function to select a subset of burstable jobs
- The iterable that chooses the ordering of plugins

Each of the above will be discussed further in detail in the sections below.

#### Bursting Plugins

Bursting plugins are customized by way of installing a plugin with prefix `fluxburst_<name>` and then
loading them with your client:

```python
from fluxburst.client import FluxBurst

client = FluxBurst()

# Let's say we did pip install fluxburst_gke
# **kwargs would be any specific keyword arguments for GKE
client.load("gke", **kwargs)
```

For the above, we might have installed the `fluxburst_gke` plugin, and then `**kwargs`
might include Google Cloud specific arguments for it. If we don't want to customize
anything else (and use the defaults) we would then proceed to use the client to
run a burst:

```python
client.run_burst()
```

The above is assumed to be running in a Python environment that can connect to the main
Flux broker instance.

#### Selectors

Before any bursting is done, the queue needs to be filtered. Selection means
using some algorithm to separate the jobs that are indicated to be burstable
vs those that are not.  For the simple default implementation, we simply choose
to pass through jobs that have the attribute "burstable" and ignore the rest.
Here is an example of our function that knows how to do that - it will expect
a single job info (in json) as the only argument:

```python
def is_burstable(jobinfo):
    """
    Determine if a job is burstable if:

    1. It is flagged as burstable
    """
    return "burstable" in jobinfo["spec"]["attributes"]["system"]
```

Here is what the `jobinfo` variable looks like that the function has access to.
This means that your function should take this as input, and return a boolean
to indicate if it's burstable (or not). Note that this is not currently json serializable:

```python
{'id': 12420793761792,
 'userid': 1000,
 'urgency': 16,
 'priority': 16,
 't_submit': 1687638917.9938345,
 't_depend': 1687638918.005533,
 'state': 8,
 'name': 'hostname',
 'ntasks': 4,
 'duration': 0.0,
 'nnodes': 4,
 'info': {'_t_depend': 1687638918.005533,
  '_t_run': 0.0,
  '_t_cleanup': 0.0,
  '_t_inactive': 0.0,
  '_duration': 0.0,
  '_expiration': 0.0,
  '_name': 'hostname',
  '_queue': '',
  '_ntasks': 4,
  '_ncores': '',
  '_nnodes': 4,
  '_priority': 16,
  '_ranks': '',
  '_nodelist': '',
  '_success': '',
  '_waitstatus': '',
  '_id': JobID(12420793761792),
  '_userid': 1000,
  '_urgency': 16,
  '_t_submit': 1687638917.9938345,
  '_state_id': 8,
  '_result_id': '',
  '_exception': {'occurred': '', 'severity': '', 'type': '', 'note': ''},
  '_annotations': {'annotationsDict': {}, 'atuple': X()},
  '_sched': ,
  '_user': ,
  '_dependencies': []},
 'spec': {'resources': [{'type': 'node',
    'count': 4,
    'exclusive': True,
    'with': [{'type': 'slot',
      'count': 1,
      'with': [{'type': 'core', 'count': 1}],
      'label': 'task'}]}],
  'tasks': [{'command': ['hostname'],
    'slot': 'task',
    'count': {'per_slot': 1}}],
  'attributes': {'system': {'duration': 0,
    'cwd': '/tmp/workflow/gke',
    'shell': {'options': {'rlimit': {'cpu': -1,
       'fsize': -1,
       'data': -1,
       'stack': 8388608,
       'core': 0,
       'nofile': 1048576,
       'as': -1,
       'rss': -1,
       'nproc': -1}}},
    'burstable': 1}},
  'version': 1}}
```

For now, we just allow one selection function - the idea being if you want to combine
logic, just do that in one function! Here is how you'd provide your custom function to the class:

```python
from fluxburst.client import FluxBurst

client = FluxBurst()
client.set_selector(func)
```

Of course this is just an example - you don't have to set this function because the default
is expecting the "burstable=True" attribute to be set.

#### Plugin Ordering

By default, the set of plugins added are added as an ordered dictionary,
meaning they are yielded back in the order added. However, it could be the case
that you want to order the logic of your plugins (or filter them down specifically
to a subset) before running the burst. This is where you might want a custom function.
Here is an example of writing a function (actually, this is the default)!

```python
def in_order(plugins):
    """
    Plugins is expected to be an ordered dict, return in order

    This is designed intending to be flexible. We can add
    additional metadata if needed
    """
    for name, plugin in plugins.items():
        yield name, plugin
```

And then how to add the function to your client:

```python
from fluxburst.client import FluxBurst

client = FluxBurst()
client.set_ordering(in_order)
```

Note that the function is expected to take the dictionary (ordered dict)
of plugins that are known to the client. If we need to extend this
to add custom variables that is possible, however you plugin subclass
already has support for this customization in being a class that you write!

## Development

### Local Development

Setup your environment, and install local:

```bash
$ python -m venv env
$ source env/bin/activate
$ pip install -e .
```

You'll want to also install at least one plugin.

### Writing a Plugin

We [discover plugins](fluxburst/plugins.py) via a simple approach
that looks for modules that start with the prefix "fluxburst_<name>" as mentioned above.
While there are several [design approaches](https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/)
for implementing plugins, this one was chose for its simplicity. Our setup supports:

 - Install of any custom number of burstable plugins
 - Defining a custom data class that is added to support additional parameters
 - Customizing original queue selection of jobs, and ordering of plugins chosen

Each plugin is expected to have, at the top level of the module (e.g., `fluxburst_<name>.<func>`), the following functions or attributes for flux-burst:

 - *init* a basic function that does checks / imports the main plugin class, and returns it instantiated with the dataclass as the only argument.

More detail on the above is provided below.

#### dataclasses.dataclass

Your plugin is driven by the custom dataclass. We chose this design because it needs to be possible
to interact with the executor from within Python (in which case you would create the dataclass) or from
the command line (in which case we convert from the dataclass to argparse and back again)! As an example,
here is a very basic way to define custom arguments for your plugin via a dataclass:

```python
import fluxburst.plugins as plugins
from typing import Optional
from dataclasses import dataclass

@dataclass
class BurstParameters:
    cluster_name: Optional[str] = "flux-cluster"
    namespace: Optional[str] = "flux-operator"
```

#### BurstPlugin class

We provide a `fluxburst.plugins.BurstPlugin` class that you can subclass for your plugin
that defines the required functions, and provides the structure and shared logic for all plugins.
We will write more here when we develop the first prototype!

🚧️ **under development** 🚧️

This tool is under development and is not ready for production use.

## TODO

Desired plugins are:

 - [local mock](https://github.com/flux-framework/flux-sched/issues/1009#issuecomment-1603636498)
 - [Google Cloud](https://github.com/converged-computing/flux-burst-gke)
 - AWS (not written yet)


## Questions

- How should the plugins manage checking when to create / destroy clusters?
- Can we have a better strategy for namespacing different bursts (e.g., beyond burst-0, burst-1, ..., burst-N)
- We need a reasonable default for what a plugin should do if something fails (e.g., setup/config)
- How should each plugin decide what size cluster to make? Right now I'm just taking the max size of the job, and we are assuming the jobs need the same node type.
- We will eventually want to use namespaces in a meaningful way (e.g., users)
- We will eventually want a specific burst for a job to be able to customize in more detail, e.g., the namespace or other attribute that comes from a jobspec (right now they are global to the plugin)
- Who controls cleanup? It can be done by the flux-burst global controller or a plugin, automated or manual, either way.

## 😁️ Contributors 😁️

We use the [all-contributors](https://github.com/all-contributors/all-contributors)
tool to generate a contributors graphic below.

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://vsoch.github.io"><img src="https://avatars.githubusercontent.com/u/814322?v=4?s=100" width="100px;" alt="Vanessasaurus"/><br /><sub><b>Vanessasaurus</b></sub></a><br /><a href="https://github.com/converged-computing/flux-burst/commits?author=vsoch" title="Code">💻</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

## License

HPCIC DevTools is distributed under the terms of the MIT license.
All new contributions must be made under this license.

See [LICENSE](https://github.com/converged-computing/flux-burst/blob/main/LICENSE),
[COPYRIGHT](https://github.com/converged-computing/flux-burst/blob/main/COPYRIGHT), and
[NOTICE](https://github.com/converged-computing/flux-burst/blob/main/NOTICE) for details.

SPDX-License-Identifier: (MIT)

LLNL-CODE- 842614

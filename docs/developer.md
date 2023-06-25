# Developer Guide

This is a short guide to help with development of plugins. If you are interested
in using Flux Burst, you likely want our [User Guide](user-guide.md).
We will expand it as we work on automation for testing, developer environments, etc.

## Local Development

Your development environment will vary based on what you are developing for.
In the case of bursting to a cloud, for example, you likely need a setup that
allows one cluster to talk to another, and a good example is the [Flux Burst GKE](https://github.com/flux-framework/flux-operator/blob/main/examples/experimental/bursting/broker/README.md)
tutorial. For a mock plugin (not developed yet) you likely can use a local Flux cluster.
At a high level, you'll want:

1. To be connected to the main or lead Flux broker
2. To have Flux Python bindings installed alongside it
3. To install the core `flux-burst` (e.g., `python3 -m pip install flux-burst`)
4. To have your local plugin installed in development mode (e.g., `pip install -e .`)

And then to iteratively develop until you get it working. The rest of this guide will walk
through the logic of writing a plugin, and some brief design for how it works.

## Writing a Plugin

We [discover plugins](https://github.com/converged-computing/flux-burst/blob/main/fluxburst/plugins.py) via a simple approach
that looks for modules that start with the prefix `fluxburst_<name>`.
While there are several [design approaches](https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/)
for implementing plugins, this one was chose for its simplicity. Our setup supports:

 - Install of any custom number of burstable plugins
 - Defining a custom dataclass that is added to support custom parameters and requirements
 - Customizing original queue selection of jobs, and ordering of plugins chosen

More detail on the above is provided below.

### Organization

Here is an example organization for a plugin. Note that we have not included
tests here, and mostly because we haven't figured out a common way to write per plugin,
but you can imagine having a "tests" directory with your setup.
Each file will be described in more detail.

```console
├── CHANGELOG.md
├── COPYRIGHT
├── Dockerfile
├── docs
...
├── fluxburst_gke        (- The main plugin module
│   ├── cluster.py       (- Additional functions for Google Cloud and MiniClusters
│   ├── defaults.py      (- Plugin defaults (if applicable)
│   ├── __init__.py      (- Init file that is required to have "init"
│   ├── plugin.py        (- Main plugin module with BurstParameters and plugin class
│   └── version.py       (- Metadata / version information for setuptools
├── LICENSE
├── MANIFEST.in
├── NOTICE
├── pyproject.toml
├── README.md
├── setup.cfg
└── setup.py
```

#### Init

The only requirement for your plugin main `__init__.py` is a function that can be called
to return the instantiated plugin with the dataclass parameters added. It might look like this:

```python
def init(dataclass, **kwargs):
    """
    Parse custom arguments and return the Burst client.

    We use a function based import here in case additional checks are
    needed, or things that aren't available when the module is loaded
    (but are later when this function is called)
    """
    from .plugin import FluxBurstGKE

    return FluxBurstGKE(dataclass, **kwargs)
```

We don't currently do anything with the `kwargs` but we allow them anticipating
some extra needs for parameters that go beyond the dataclass.
The plugin would be discovered as a module, and then when a user loads it
by name, and includes a dataclass (dc) with parameters:

```
from fluxburst.client import FluxBurst

client = FluxBurst()
client.load("gke", dc)
```

Under the hood, the FluxBurst main client is:

1. Asserting that the plugin is known
2. Doing basic validation of the structure
3. Initializing it, and added to the set of active plugins (below)

```python
plugin = burstable_plugins[name].init(dataclass)
...
self.plugins[name] = plugin
```

Thus, each plugin is expected to have, at the top level of the module (e.g., `fluxburst_<name>.<func>`), the following function:

 - **init** a basic function that returns the plugin main class instantiated with the dataclass as the only argument.

Your init function might also do other system checks or setup that is necessary.
In the above, although it's not technically required, we do the import of our
custom plugin class within the function, being more conservative and assuming there
might be something we should not import until we are ready to use it.

#### The plugin

Within `plugin.py` is where you might expect to implement:

1. Your custom dataclass
2. You custom plugin class

Both will be described more below.

##### dataclasses.dataclass

Your plugin is driven by the custom dataclass. We chose this design because it needs to be possible
to interact with the plugin from within Python (in which case you would create the dataclass) or from
a config file or the command line, in which case we can easily adopt the dataclass to serve those purposes.
As an example, here is a very basic way to define custom arguments for your plugin via a dataclass:

```python
import fluxburst.plugins as plugins
from typing import Optional
from dataclasses import dataclass

@dataclass
class BurstParameters:
    required_arg: str
    cluster_name: Optional[str] = "flux-cluster"
    namespace: Optional[str] = "flux-operator"
```

The first arguments in the list are required (they don't have optional types nor defaults).
It works the same as it does for a Python function - if you put a required arguments
after those with defaults you will get an error. You will also get an error instantiating
the dataclass if a required argument is missing, which is what we want!

##### BurstPlugin class

We provide a `fluxburst.plugins.BurstPlugin` class that you can subclass for your plugin
that defines the required functions, and provides the structure and shared logic for all plugins.
There are functions provided in the base class for parsing your dataclass, including:

 - *the init*: on init, we take the dataclass provided by the user and parse it (set_params) and create an empty `self.jobs` for the class
 - *set_params*: we validate that the dataclass provided is the one expected, and then also derive params from the environment.

Any variable defined by the dataclass can be set in the environment, as long as it is prefixed with `FLUXBURST_`.
In addition, all letters are expected to be lowercase and use underscores. As an example, if our dataclass
has the variable `cluster_name` we could set it in the environment as:

```bash
export FLUXBURST_CLUSTER_NAME=myname
```

If needed, we can adopt this approach to better handle namespacing by the plugin (e.g., `FLUXBURST_GKE_` as a prefix instead)
or type checking. For the time being, we aren't doing that yet. As a plugin writer, you can
expect to write two functions:

 - **schedule**: takes one parameter, a job, and returns a boolean to indicate if it can be scheduled. If so, you should also add the job metadata to `self.jobs` to retrieve later. In the future this will also include assigning the right instance, etc.
 - **run**: burst to your plugin for the self.jobs that are there. The logic here is up to you.

What we don't have structure for (or requirements around) is deciding how to do the burst,
or, for example, when to bring up or down a cluster. As an example, the current GKE plugin
currently just stores clusters by name, and creates each cluster that is needed for the
user, and it's a "proceed at your own risk" sort of deal because we don't place constraints on that.
It also is required for the running client to decide when to cleanup. As an example,
here is how we would get the GKE plugin handle and do the cleanup:

```bash
handle = client.plugins["gke"]

# Take down all remote clusters
handle.cleanup()

# Take down the flux-bursted-cluster
handle.cleanup("flux-bursted-cluster")
```

Cleanup is currently not a required plugin function, but likely will be.


## Documentation

The main documentation for the repository is in the [docs](https://github.com/converged-computing/flux-burst/tree/main/docs) directory,
and the interface itself is static and generated from the markdown with
javascript. The only programmatically generated docs are in the [docs/api](https://github.com/converged-computing/flux-burst/tree/main/docs/api)
folder, which are currently done manually (and could be automated if desired). To update the api docs:

```bash
python -m venv env
source env/bin/activate
pip install -e .
cd apigen
```

Install dependencies to build the docs:

```bash
$ pip install -r requirements.txt
```

If you need to generate new source documents (given new structure):

```bash
$ sphinx-apidoc -o source/ ../fluxburst
```

And then to generate:

```bash
./apidoc.sh
```

And that's it! That script will build the docs, and then remove the old `docs/api`
folder to replace with the new one. If you want to test the build beforehand
(and look for errors or preview) you can do:

```bash
$ make html
$ cd _build/html
$ python -m http.server 9999
```

Then open your browser to [http://localhost:9999](http://localhost:9999)
to see the API docs You can use this same strategy of starting a local
server from within the docs folder to also preview the site.

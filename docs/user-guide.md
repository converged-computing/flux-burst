# User Guide

To get started, you are likely running from inside of a Flux instance where you have
access to Flux Python bindings.

## Install

You can install both Flux Burst and any associated plugins from pip:

```bash
$ pip install flux-burst

# an example plugin for gke
$ pip install flux-burst-gke
```

Or the repository here:

```bash
$ git clone https://github.com/converged-computing/flux-burst
$ cd flux-burst
$ pip install .
```

It's up to you how you want to manage your Python environments. If you are using
a Python installed next to Flux, you likely want to use that one, or ensure that you
are grabbing any pip associated with the system Python, e.g.,:

```bash
$ python3 -m pip install flux-burst
```

## Bursting Plugins

Bursting plugins are customized by way of installing a plugin with prefix `fluxburst_<name>` and then
loading them with your client. The following plugins have been developed:

 - [flux-burst-local](https://github.com/converged-computing/flux-burst-local) to "burst" on a local HPC system
 - [flux-burst-gke](https://github.com/converged-computing/flux-burst-gke) to burst to Google Kubernetes Engine
 - [flux-burst-eks](https://github.com/converged-computing/flux-burst-eks) to burst to Amazon EKS
 - [flux-burst-compute-engine](https://github.com/converged-computing/flux-burst-compute-engine) to burst to Google Cloud Compute Engine


We would idealistically like to develop the following:

 - Amazon EKS
 - Mock

### Loading a Plugin

Plugins are discovered automatically by Flux Burst by way of their naming.
An example loading the GKE plugin looks like the following, which would be run by the Flux lead broker:

```python
from fluxburst.client import FluxBurst

# This is the main client to run bursts
client = FluxBurst()

# Let's say we did pip install fluxburst_gke
# dc would be a custom dataclass for our plugin that it provides.
# The plugins also read from FLUXBURST_ environment variables
client.load("gke", dc)
```

For the above, we might have installed the `fluxburst_gke` plugin, and then "dc"
might include Google Cloud specific arguments for it. The "dc" is a custom dataclass
that holds the plugin parameters, and we might have instantiated it like this:

```python
from fluxburst_gke.plugin import BurstParameters

dc = BurstParameters(
    project=args.project,
    munge_key=args.munge_key,
    munge_secret_name=args.munge_secret_name,
    curve_cert_secret_name=args.curve_cert_secret_name,
    flux_operator_yaml=args.flux_operator_yaml,
    lead_host=args.lead_host,
    lead_port=args.lead_port,
    lead_size=args.lead_size,
    name=args.name,
)

# Setup the flux-burst-gke plugin with the above settings
client.load("gke", dc)
```

The parameter names above might make sense when you consider that the GKE
burst plugin is going to create a second cluster on Google Kubernetes Engine
(why we need a project, and a spec for the Flux Operator) and then tell it how
to connect to the first (the lead broker variables and munge/curve secrets).
Every broker will be a little different in terms of the requirements, and
this approach allows flexibility for that.

Since every plugin might vary in the specific parameters or arguments it has or requires,
we scope this to a [dataclass](https://www.dataquest.io/blog/how-to-use-python-data-classes/),
where it is possible to control the arguments required and defaults.

### Running Bursting

The way that the above is initialized and then a burst is run is totally
dictated by the plugin. For example, we might start some kind of cron or event
driven process that initializes the plugin once, as shown above, and then has the inner logic of
the plugin determine when to create and destroy clusters, and how to assign
burstable jobs to them. It could also be that the above is done via a manual request.
Regardless of how you choose to implement this, when you want to run one iteration
of a burst, you would do the following:

```python
client.run_burst()
```

The above is assumed to be running in a Python environment that can connect to the main
Flux broker instance, and in this process there are several steps, which are also
dictated by the client:

1. **Job Selection**: Decide from the entire queue which jobs to burst, regardless of any plugins
2. **Plugin Ordering**: Decide the ordering of your plugins (if more than one is loaded) to allow scheduling burstable jobs.
3. **Scheduling**: The plugin deciding if it is able and willing to do a burst!

Each of the above will be described in more detail in the following sections.

#### Job Selection

Before any bursting is done, the queue needs to be filtered. Selection means
using some algorithm to separate the jobs that are indicated to be burstable
vs those that are not.  For the simple default implementation, we simply choose
to pass through jobs that have the attribute "burstable" and ignore the rest.
For the time being, this is a manual attribute that can be applied by a user
or developer:

```bash
$ flux submit -N 4 --setattr=burstable hostname
```

Here is an example of our function that knows how to do that - it will expect
a single job info (a Python dictionary) as the only argument:

```python
def is_burstable(jobinfo):
    """
    Determine if a job is burstable if:

    1. It is flagged as burstable
    """
    return "burstable" in jobinfo["spec"]["attributes"]["system"]
```

Here is what the `jobinfo` variable looks like that the function has access to.
This is a standard output of Flux info in Python, but we add the spec from the KVS store
to expose attributes and more metadata.

<details>

<summary>Flux Job Info</summary>

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

</details>

This means that your function should take this as input, and return a boolean
to indicate if it's burstable (or not). Note that the above is not currently json serializable.
For now, we just allow the `FluxBurst` client to have one selection function.
If you want to combine logic, just do that in one function! If you use the default, it
will look for this `burstable` flag.  But here is how you'd provide your custom function to the class:

```python
from fluxburst.client import FluxBurst

def func(jobinfo):
    """
    This is an example function to always burst!
    """
    return True

client = FluxBurst()
client.set_selector(func)
```

Of course this is just an example - likely the algorithm you write here would
be more sophisticated to possibly look at:

1. Request for resources vs. resources locally available
2. Time in the queue
3. Accounting for the user


#### Plugin Ordering

By default, the set of plugins added are added as an ordered dictionary,
meaning they are yielded back in the order added. The reason this matters is because
plugins that are given the option to schedule a job to burst can claim it first!
However, it could be the case that you want to order the logic of your plugins (or filter them down specifically
to a subset) before running the burst. This is where you might want a custom function.
Here is an example of writing a function that returns the exact order in the
OrderedDict (actually, this is the default)!

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

#### Scheduling

Scheduling is handled on the level of the plugin, more specifically the `schedule`
function of the plugin class. This is where the client will present jobs to the plugin,
and the plugin can decide if it can handle bursting it (and if yes, schedule it to burst).
When the client runs `run_burst` the plugin `run` function will then be called to perform
bursting for the jobs selected for scheduling. You can [read more about writing plugins](developer.md) in the
Developer documentation. As a user, you only need to worry about the above:

1. Loading your plugins
2. Choosing parameters that control plugin logiuc
3. Deciding on a custom selection function
4. Deciding on a custom ordering function

[home](/README.md#flux-burst)

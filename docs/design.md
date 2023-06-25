# Design

## Overview

The Flux burst module does the following:

 1. Discovers burstable plugins on the system that start with `fluxburst_<name>`
 2. Loads one or more plugins of your choosing with `client.load(name, dataclass)`
 3. On a call to run:
   a. We call the filter function to select jobs that are candidates for bursting (via any plugin)
   b. We use a default (or customized) bursting selection function (e.g., controlling logic for how to choose a plugin)
   c. We iterate through our plugins, and assign matched jobs to burst
   d. We run the bursts

The main controller running the client is currently responsible for cleanup and deciding
on frequency to run. From the above, this means that you can customize the following:

- The plugins discovered as available on the system
- The plugins you choose to load for a particular instance
- The filter or selection function to select a subset of burstable jobs
- The iterable that chooses the ordering of plugins

[home](/README.md#flux-burst)

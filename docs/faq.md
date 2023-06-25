# Clouds

Cloud Select supports the following clouds. Note that currently, to generate your own updated cache of
data you'll need to provide credentials for each. We are hoping to provide automation at some point
## Frequently Asked Questions

### What is a burst?

A traditional burst means extending some local Flux Cluster with a remote. That "remote" can actually be:

- a cloud cluster (existing or not)
- a second cluster
- a mocked cluster

The main idea is that the main Flux Cluster is not just creating additional resources, but connecting
the local broker to the new external one. This is different from what we might consider an isolated
burst or external job submission, where a first cluster creates an entirely new second cluster
that is disconnected but handles some amount of scoped work.

### How does the design here work?

This library uses a plugin architecture, meaning that if you want to add a new kind of burstable,
you do so by way of writing a plugin. Instructions for writing a plugin are included [here](developer.md#writing-a-plugin).

[home](/README.md#flux-burst)

# Flux Burst

<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-1-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->
[![PyPI](https://img.shields.io/pypi/v/flux-burst)](https://pypi.org/project/flux-burst/)

<!--<a target="_blank" rel="noopener noreferrer" href="https://github.com/converged-computing/flux-burst/blob/main/docs/assets/img/logo-transparent.png">
    <img align="right" style="width: 250px; float: right; padding-left: 20px;" src="https://github.com/converged-computing/flux-burst/raw/main/docs/assets/img/logo-transparent.png" alt="Cloud Select Logo">
</a>-->

![https://raw.githubusercontent.com/converged-computing/flux-burst/main/docs/assets/img/logo.png](https://raw.githubusercontent.com/converged-computing/flux-burst/main/docs/assets/img/logo.png)

This is a Python module to coordinate Flux bursting. 🧋️

 - ⭐️ [Documentation](https://converged-computing.github.io/flux-burst/) ⭐️
 - 📦️ [Pypi Package](https://pypi.org/project/flux-burst/) 📦️


## Plugins

Current and desired plugins are:

 - [local mock](https://github.com/flux-framework/flux-sched/issues/1009#issuecomment-1603636498)
 - [Google Cloud](https://github.com/converged-computing/flux-burst-gke)
 - AWS (not written yet)

## Questions

- How should the plugins (or client) manage checking when to create / destroy clusters?
- Can we have a better strategy for namespacing different bursts (e.g., beyond burst-0, burst-1, ..., burst-N)
- We need a reasonable default for what a plugin should do if something fails (e.g., setup/config)
- How should each plugin decide what size cluster to make? Right now I'm just taking the max size of the job, and we are assuming the jobs need the same node type.
- We will eventually want to use namespaces in a meaningful way (e.g., users)
- We will eventually want a specific burst for a job to be able to customize in more detail, e.g., the namespace or other attribute that comes from a jobspec (right now they are global to the plugin)
- Who controls cleanup? It can be done by the flux-burst global controller or a plugin, automated or manual, either way.
- All plugins should have support to read in YAML parameters (some spec for bursting)
- All plugins should be able to match a resource request to, for example, instance types.
- Should the plugin "local queue" (self.jobs) assume to be associated with one burst, where the size is the max job size?
- Should we derive names based on provided name + size so clusters are unique by name and size?

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

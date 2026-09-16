# Components

Only the components that the built variant actually contains appear below.
Each component's design document is mounted by sphinx-mounts under the KConfig
feature that owns it, so this page needs no templating: the declarations live
in `[[source.mounts]]` in `ubproject.toml`, and sphinx-mounts appends each
mounted entry to the empty toctree below.

Each entry is a group. A component's own document is the entry point of its
bundle and carries the toctree for its verification pages, so unit test results
and coverage appear underneath the component they belong to rather than in one
flat list.

```{toctree}
:maxdepth: 2

```

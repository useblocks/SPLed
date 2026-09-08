# Components

Only the components that the built variant actually contains appear below.
Each component's design document is mounted by sphinx-mounts under the KConfig
feature that owns it, so the table of contents follows the variant without any
templating in this file. The declarations live in `[[source.mounts]]` in
`ubproject.toml`, and sphinx-mounts appends each mounted entry to the empty
toctree below.

```{toctree}
:maxdepth: 2

```

````{if} var.build_config.target == "reports"

```{toctree}
:caption: Unit test results
:maxdepth: 1
:glob:

/build/**/components/*/reports/unit_test_spec
/build/**/components/*/reports/unit_test_results
/build/**/components/*/reports/coverage
```

````

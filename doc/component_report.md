# Software Component Report

**Variant:** {variant}`build_config.variant`<br/>
**Component:** {variant}`build_config.component_info.long_name`

This is the root document of the per-component report that spl-core builds for
a single component. The build configuration restricts the source set to that
one component, so the glob below resolves to exactly its design document.

```{toctree}
:maxdepth: 2
:glob:

/components/*/doc/index
```

````{if} var.build_config.target == "reports"

```{toctree}
:caption: Unit test results
:maxdepth: 1
:glob:

/build/**/reports/unit_test_spec
/build/**/reports/unit_test_results
/build/**/reports/coverage
```

````

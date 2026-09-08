# Software Component Report

**Variant:** {variant}`build_config.variant`<br/>
**Component:** {variant}`build_config.component_info.long_name`

This is the root document of the per-component report that spl-core builds for
a single component. The build configuration restricts the source set to that
one component, so the glob below resolves to exactly its design document, which
in turn groups that component's verification pages.

```{toctree}
:maxdepth: 2
:glob:

/**/doc/index
```

# Software Component Report

**Variant:** {variant}`build_config.variant` · **Component:** {variant}`build_config.component`

This is the root document of the per-component report that spl-core builds for
a single component. Its variant data has `build_config.scope = "component"`, and
the rules in ubproject.variants.toml leave that component's documents only, so
the glob below resolves to exactly its design document, which in turn groups the
component's verification pages. ubCode builds the same report from the same
files (build/selection.toml, or the build's `selection/<component>/reports.toml`).

```{toctree}
:maxdepth: 2
:glob:

/**/doc/index
```

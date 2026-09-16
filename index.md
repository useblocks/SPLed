# Variant Report

**Variant:** {variant}`build_config.variant`

```{toctree}
:maxdepth: 1
:caption: Contents

doc/customer_requirements/index
doc/software_architecture/index
doc/sw_requirements/index
doc/components/index
```

````{if} var.build_config.target == "reports"

`generated` is the build directory of the configured variant, maintained by
`tools/variant_data.py`. Naming it directly is what lets this be one entry
rather than a glob over every variant and build type that happens to be on
disk -- a glob that only ever resolved to one page because `conf.py` narrowed
the source set behind the scenes.

```{toctree}
:caption: Code Coverage
:maxdepth: 1

/generated/reports/coverage
```

````

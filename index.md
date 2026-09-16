# Variant Report

**Variant:** {variant}`build_config.variant`
**Timestamp:** {{ timestamp }}

```{toctree}
:maxdepth: 1
:caption: Contents

doc/customer_requirements/index
doc/software_architecture/index
doc/sw_requirements/index
doc/components/index
```

````{if} var.build_config.target == "reports"

The glob below matches the variant-wide coverage page for any variant name and
any build type, and does not match a component's own coverage page, because the
directory in front of `reports` is the build type there and the component name
here.

```{toctree}
:caption: Code Coverage
:maxdepth: 1
:glob:

/build/**/[A-Z]*/reports/coverage
```

````

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

The glob matches the variant-wide coverage page for any variant name and build
type, and not a component's own, because the directory in front of `reports` is
the build type there and the component name here. It resolves to exactly one
page because the source set is the configured variant's build directory.

A fixed path would be better, and `generated` exists for it, but spl-core writes
the gcovr tree next to the build-relative page path and its report artifacts are
looked up there too -- so the stable path needs the spl-core change, and is
deferred with it.

```{toctree}
:caption: Code Coverage
:maxdepth: 1
:glob:

/build/**/[A-Z]*/reports/coverage
```

````

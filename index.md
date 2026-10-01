---
orphan: true
---

# Variant Report

**Variant:** {variant}`build_config.variant`

```{toctree}
:maxdepth: 1
:caption: Contents

doc/customer_requirements/index
doc/software_architecture/index
doc/sw_requirements/index
doc/components/index
doc/results/index
```

% The variant's coverage page, in the one build whose pages the selection reads:
% build/<variant>/<kit>/<build type>/reports/coverage. A variant's name has one
% segment (Disco) or two (Base/Dev), so the page is one level deeper for the
% latter. `*` stays within one segment, while `**` would match every
% component's coverage page as well.

````{if} var.build_config.target == "reports" and var.build_config.scope == "variant" and "/" not in var.build_config.variant

```{toctree}
:caption: Code Coverage
:maxdepth: 1
:glob:

/build/*/*/*/reports/coverage
```

````

````{if} var.build_config.target == "reports" and var.build_config.scope == "variant" and "/" in var.build_config.variant

```{toctree}
:caption: Code Coverage
:maxdepth: 1
:glob:

/build/*/*/*/*/reports/coverage
```

````

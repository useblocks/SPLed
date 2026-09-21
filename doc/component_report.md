# Software Component Report

**Variant:** {variant}`build_config.variant`

This is the root document of the per-component report that spl-core builds for
a single component. The build configuration restricts the source set to that
one component, so the glob below resolves to exactly its design document, which
in turn groups that component's verification pages -- and names the component,
which is why this page does not.

The component name is deliberately not read from `build_config.component_info`.
That key is written per BUILD, by spl-core, for one component; the variant data
every other reader has cannot contain it, because the generator does not know
which component a per-component report is for. A role naming it resolves inside
that one build and nowhere else, which is the divergence between readers this
project's configuration exists to prevent.

```{toctree}
:maxdepth: 2
:glob:

/**/doc/index
```

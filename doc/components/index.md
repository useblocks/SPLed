# Components

This page lists the components of the variant. The toctree globs every
component's documentation, and the rules in `ubproject.variants.toml` remove the
ones the variant does not contain, each gated on membership of that variant's
component list. `tools/variant_data.py` derives the rules from where each
component's documentation lives, so adding a component means adding it to a
variant's `parts.cmake` and writing its documentation: nothing to edit here,
and nothing under `build/`.

Each entry is a group. A component's own document is the entry point and
carries the toctree for its verification pages, so unit test results and
coverage appear underneath the component they belong to rather than in one flat
list.

```{toctree}
:maxdepth: 2
:glob:

/components/*/doc/index
/components/examples/*/doc/index
/test/*/doc/index
```

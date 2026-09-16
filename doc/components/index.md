# Components

This page lists every component the product line has. It is a 150% view: the
entries are always all of them, and the ones the built variant does not contain
are removed from the build by the `[[source.variant_sources]]` rules in
`ubproject.toml`, each gated on membership of that variant's component list.

So this page needs no templating and no generated content. Adding a component
to the report means adding it to a variant's `parts.cmake` and adding one rule
plus one line here — never editing a loop, and never editing anything under
`build/`.

An entry naming a document the current variant excludes is reported as INFO by
both Sphinx and ubCode, by design: the 150% tree is the source of truth, and a
variant showing less of it is the normal case rather than an error.

Each entry is a group. A component's own document is the entry point and
carries the toctree for its verification pages, so unit test results and
coverage appear underneath the component they belong to rather than in one flat
list.

```{toctree}
:maxdepth: 2

/components/light_controller/doc/index
/components/main_control_knob/doc/index
/components/power_button/doc/index
/components/power_signal_processing/doc/index
/components/brightness_controller/doc/index
/components/auto_off/doc/index
/components/examples/hello_gmock/doc/index
/components/examples/flight_controller/doc/index
/test/spled_integration/doc/index
```

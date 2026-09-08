# -*- coding: utf-8 -*-
"""Configuration"""
import datetime
import json
import os

from pathlib import Path

from importlib.resources import files
from spl_core.report_generation.spl_sphinx import SplSphinx
from spl_core.report_generation.spl_html_settings import html_theme, html_show_sourcelink, html_theme_options, html_sidebars, html_last_updated_fmt  # noqa: F401

day = datetime.date.today()
# meta data #################################################################

project = "SPLed"
copyright = f"{day.year}, RMT and Friends"
release = f"{day}"

# file handling #############################################################
# @see https://www.sphinx-doc.org/en/master/usage/configuration.html

templates_path = [
    "doc/_tmpl",
]

exclude_patterns = [
    "README.md",
    "build/modules",
    "build/deps",
    ".venv",
    ".git",
    "**/test_results.rst",  # We renamed this file, but nobody deletes it.
]

include_patterns = ["index.md", "doc/**"]

# configuration of built-in stuff ###########################################
# @see https://www.sphinx-doc.org/en/master/usage/configuration.html

numfig = True

# html config ###############################################################
# @see https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

# Omit "documentation" in title
html_title = f"{project} {release}"

html_logo = "doc/_figures/SPLED_logo.png"

# Get default SPL extensions and their configurations
extensions = [*SplSphinx.default_extensions, "sphinx_codelinks", "sphinx_mounts"]
extension_configs = SplSphinx.default_extension_configs

# sphinx-codelinks: extract one-line need definitions from source code comments
src_trace_config_from_toml = "ubproject.toml"

# Apply extension-specific configurations
tr_report_template = extension_configs["tr_report_template"]
myst_enable_extensions = extension_configs["myst_enable_extensions"]
source_suffix = extension_configs["source_suffix"]

# Import default SPL sphinx-needs configuration
needs_from_toml = str(files("spl_core.report_generation").joinpath("ubproject.toml"))

needs_fields = {
    "image": {
        "description": "Image associated with the need",
        "schema": {
            "type": "string"
        },
        "nullable": True,
    },
}

# Additional import required because the configuration references custom functions defined in this module
needs_functions = SplSphinx.default_needs_functions
needs_global_options = SplSphinx.default_needs_global_options

# Always write the merged needs.json (all needs, after import/resolution) to the build output dir.
needs_build_json = True

# Expose KConfig feature values (e.g. CUSTOMER) as `var.features.*`.
# Used by the {if} directive in the documents and by the `if` conditions of
# [[source.mounts]] in ubproject.toml. CMake exports AUTOCONF_JSON_FILE for the
# variant it is building; the mirrored copy written by CMakeLists.txt is the
# fallback so a bare `sphinx-build` (or the IDE) resolves the same variant
# instead of silently dropping every variant-gated document.
_autoconf_json_file = os.environ.get("AUTOCONF_JSON_FILE", "build/autoconf.json")
if os.path.exists(_autoconf_json_file):
    needs_variant_data_file = _autoconf_json_file


def _feature_defaults() -> dict:
    """Every boolean the feature model declares, defaulted to False.

    KConfig writes a boolean into autoconf.json only when it has a prompt or
    evaluates to y. A helper symbol such as BRIGHTNESS_ADJUSTMENT_ENABLED is
    therefore simply absent from the variants where it is off, and a document
    or a mount condition naming it would fail to evaluate for exactly those
    variants. Reading the model once and defaulting its booleans keeps the
    variant data complete without anyone having to maintain a list by hand.
    """
    try:
        import kconfiglib
        import spl_core

        os.environ.setdefault("SPL_CORE_DIR", str(Path(spl_core.__file__).parent))
        os.environ.setdefault("srctree", str(Path(__file__).parent))
        model = kconfiglib.Kconfig("KConfig", warn=False)
    except Exception:  # noqa: BLE001 - the feature model is optional context here
        return {}
    return {
        name: False
        for name, symbol in model.syms.items()
        if name and symbol.orig_type == kconfiglib.BOOL
    }


_features = _feature_defaults()
if os.path.exists(_autoconf_json_file):
    with open(_autoconf_json_file) as _handle:
        _features.update(json.load(_handle)["features"])

html_context = SplSphinx.get_default_html_context()

build_config = html_context["build_config"].copy()
build_config.pop("components_info", None)

# Two shapes of build use this configuration: the variant-wide report, and the
# per-component report that spl-core builds for a single component. Normalize
# the difference into plain keys so a document or a mount condition can test it
# without having to know which keys CMake happens to write. CMake writes
# `target` only for the variant-wide builds; for a per-component build it is the
# name of the directory holding the configuration file CMake pointed us at.
_build_config_file = os.environ.get("SPHINX_BUILD_CONFIGURATION_FILE", "")
build_config.setdefault(
    "target", "reports" if Path(_build_config_file).parent.name == "reports" else "docs"
)
build_config["scope"] = "component" if build_config.get("component_info") else "variant"

_extra_include_patterns = html_context["build_config"].get("include_patterns", [])
if build_config["scope"] == "variant":
    # Component design documents are mounted per feature by sphinx-mounts, see
    # [[source.mounts]] in ubproject.toml. Reading them as ordinary sources as
    # well would parse every need in them a second time under a second docname.
    _extra_include_patterns = [
        pattern
        for pattern in _extra_include_patterns
        if not (pattern.startswith("components/") and pattern.endswith("/doc/**"))
    ]
    root_doc = "index"
    exclude_patterns.append("doc/component_report.md")
else:
    root_doc = "doc/component_report"
    exclude_patterns.append("index.md")
include_patterns.extend(_extra_include_patterns)

needs_variant_data = {
    "features": _features,
    "build_config": build_config,
}


def rstjinja(app, docname, source):
    """Render every source file as a Jinja template before Sphinx parses it.

    No hand-written document in this project uses Jinja any more: variant
    dependent content is selected by the {if} directive of Sphinx-Needs inside
    a document, and by [[source.mounts]] conditions in ubproject.toml for whole
    documents. The hook still has to run, because the source listings that
    spl-core generates under `__source_docs` wrap their code blocks in
    `{% raw %}` and depend on this pass to strip those markers.
    """
    # Make sure we're outputting HTML
    if app.builder.format != "html":
        return
    src = source[0]
    rendered = app.builder.templates.render_string(src, app.config.html_context)
    source[0] = rendered


def setup(app):
    app.connect("source-read", rstjinja)

# -*- coding: utf-8 -*-
"""Configuration"""
import datetime
import os

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

# Omit "documentation" in title. Include the variant, so that a browser tab or
# the sidebar logo tells two variants' builds apart -- both otherwise render the
# same generic title and are indistinguishable when opened side by side.
_html_title_variant = os.environ.get("VARIANT", "")
html_title = f"{project} {_html_title_variant} {release}".strip() if _html_title_variant else f"{project} {release}"

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

# variant data ##############################################################
#
# ONE file, and nothing computed here.
#
# Everything a document's {if} directive or a condition in ubproject.toml may
# name -- the complete feature vector, the variant, the build kit, the build
# target, the component list -- is written by tools/variant_data.py and read
# from here verbatim. That is the whole point: ubCode, ubc and a reviewer's
# editor cannot execute this file, so anything synthesized here would be
# invisible to them and their view of the project would silently disagree with
# the build. The rule is "everything a condition may name has to be IN the
# file", and it only holds if this file adds nothing.
#
# CMake exports VARIANT_DATA_FILE for the build shape it is building. The
# fallback is the "current" pointer that tools/variant_data.py maintains, which
# is also what ubproject.toml names -- so a bare `sphinx-build`, the IDE and the
# docs target all resolve byte-identical data.
needs_variant_data_file = os.environ.get("VARIANT_DATA_FILE", "build/autoconf.json")

# build shape ###############################################################
#
# The rest of this file is Sphinx plumbing, not variant data: which documents
# are in the source set and which one is the root. No other tool needs to
# decide these, and none of it may leak into `var.*`.

_build_config = SplSphinx.get_default_html_context()["build_config"]
_extra_include_patterns = _build_config.get("include_patterns", [])

# Two shapes of build use this configuration: the variant-wide one, and the
# per-component report that spl-core builds for a single component.
if _build_config.get("component_info"):
    root_doc = "doc/component_report"
    exclude_patterns.append("index.md")
    # A per-component report builds one component and stitches its own table of
    # contents, so none of the mounts apply. Switching TOML reading off here is
    # what lets every `if` in ubproject.toml speak only about the variant, which
    # is the only way a reader that never runs Sphinx can decide them too.
    sources_from_toml = None
else:
    root_doc = "index"
    exclude_patterns.append("doc/component_report.md")
    # Component design documents are mounted by sphinx-mounts, see
    # [[source.mounts]] in ubproject.toml. Reading them as ordinary sources as
    # well would parse every need in them a second time under a second docname.
    # Only the hand-written trees are dropped; the generated ones under build/
    # stay, because they are not mounted.
    _extra_include_patterns = [
        pattern
        for pattern in _extra_include_patterns
        if not (pattern.endswith("/doc/**") and not pattern.startswith("build/"))
        # The generated report pages are only ever shown by the reports target.
        # The docs target used to read them anyway and then leave them out of
        # every toctree, which is 15 orphan warnings for pages nobody sees.
        and not (
            _build_config.get("target") != "reports"
            and pattern.startswith("build/")
            and pattern.endswith("/reports/**")
        )
    ]

include_patterns.extend(_extra_include_patterns)

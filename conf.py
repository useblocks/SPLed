# -*- coding: utf-8 -*-
"""Configuration"""
import datetime
import os

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

# The 150% source set: every hand-written document the product line has.
#
# Which of them the build actually contains is decided by the
# [[source.variant_sources]] rules in ubproject.toml, against the variant data.
# Narrowing the set here as well would put a second, invisible gate in front of
# the declared one -- and an invisible gate is the thing this whole design
# exists to remove.
include_patterns = [
    "index.md",
    "doc/**",
    "components/**/doc/**",
    "test/**/doc/**",
]

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

# The needs model -- types, link types, fields, and the build_json switch --
# lives in ubproject.toml, which ubCode and ubc read directly. sphinx-needs
# reads exactly one TOML file and does not implement ubCode's `extend`, so the
# only way both readers can agree is for that one file to be complete. It is;
# spl-core's base configuration is vendored into it.
needs_from_toml = "ubproject.toml"

# The same file, named again for the other extension that reads it. sphinx-mounts
# already defaults to this path; naming it makes the coupling visible in conf.py
# rather than resting on a library default.
sources_from_toml = "ubproject.toml"

# Registers project Python that the configuration references by name. This is
# the last thing in the needs model that ubCode cannot see, because it cannot
# run project functions; it goes away with sple_tr_link.
needs_functions = SplSphinx.default_needs_functions
needs_global_options = SplSphinx.default_needs_global_options

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
# CMake exports VARIANT_DATA_FILE for the build shape it is building. Without
# it -- a bare `sphinx-build`, or the IDE -- the "current" pointer applies,
# which is also what ubproject.toml names, so the two readers see byte-identical
# data by default.
#
# It has to be applied after sphinx-needs has read ubproject.toml, which happens
# on `config-inited` and would otherwise put the pointer back. For the docs
# target that is the same file; for the reports target the pointer would quietly
# supply the docs data and every report fence would evaluate false.
_variant_data_file = os.environ.get("VARIANT_DATA_FILE")

# build shape ###############################################################
#
# The rest of this file is Sphinx plumbing, not variant data: which documents
# are in the source set and which one is the root. No other tool needs to
# decide these, and none of it may leak into `var.*`.

_build_config = SplSphinx.get_default_html_context()["build_config"]

# Two shapes of build use this configuration: the variant-wide one, and the
# per-component report that spl-core builds for a single component. This is the
# only build-shape decision left here, and it is a Sphinx one -- which document
# is the root -- not variant data. No other reader has to decide it.
if _build_config.get("component_info"):
    root_doc = "doc/component_report"
    exclude_patterns.append("index.md")
    # A per-component report builds one component and stitches its own table of
    # contents, so the project-wide variant rules do not apply to it.
    sources_from_toml = None
    include_patterns.extend(_build_config.get("include_patterns", []))
else:
    root_doc = "index"
    exclude_patterns.append("doc/component_report.md")
    # The generated report pages of the CONFIGURED variant, reached through the
    # stable `generated` path rather than by globbing every build directory on
    # disk. spl-core's own include patterns are deliberately not used here: they
    # name the real build/<Variant>/<kit>/<type> paths, so the same file would
    # enter the build under a second docname and every need in it would be
    # parsed twice.
    include_patterns.extend(
        [
            "generated/reports/**",
            "generated/components/**/reports/**",
            "generated/test/**/reports/**",
            "generated/components/**/__source_docs/**",
        ]
    )


def setup(app):
    """Apply the per-build-shape variant data file, after the TOML is read."""
    if not _variant_data_file:
        return

    def _select_variant_data(app, config):
        config.needs_variant_data_file = _variant_data_file

    app.connect("config-inited", _select_variant_data, priority=20)

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
    ".venv",
    ".git",
    "**/test_results.rst",  # We renamed this file, but nobody deletes it.
    # Build output is never read where it lies. The one build a Sphinx run
    # documents is reached through `generated`, the link tools/variant_data.py
    # points at the configured build directory, and spl-core names every page
    # it generates through that link (SPL_SPHINX_BINARY_DIR in CMakeLists.txt).
    # Pruning `build` keeps every other variant's output out of the walk and
    # leaves exactly one route to each generated page, which is the invariant
    # test_ubproject_config.py guards: with two, every page exists twice.
    #
    # get_matching_files applies these to directories as well as files, so each
    # entry prunes the walk rather than filtering its result.
    "build",
    # ...and, inside the configured build, the directories that hold no
    # documents: CMake's own state and the HTML the builds write.
    "generated/CMakeFiles",
    "generated/**/CMakeFiles",
    "generated/**/html",
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
# Which cell of the matrix a build reads is not decided here either. It is the
# sphinx-needs option `needs_variant_data_file`, and ubproject.toml sets it to
# the pointer `build/autoconf.json`, which is what the IDE and a bare
# `sphinx-build` read. A build that needs another cell overrides the option on
# the command line:
#
#     sphinx-build -D needs_variant_data_file=build/variants/Sleep/test/docs.json ...
#
# spl-core does exactly that for the shape it is building
# (SPL_VARIANT_DATA_FILE_DOCS and _REPORTS in CMakeLists.txt), and so do the
# tests. sphinx-needs keeps a command-line override even though needs_from_toml
# names the pointer, and it is the same key `ubc check -c` overrides, so both
# readers select a variant the same way. Nothing in this file could do it as
# robustly: sphinx-needs replaces conf.py's values with the TOML's and resolves
# the variant data in the very next config-inited handler, so an assignment is
# lost and a handler would have to slot in between the two.

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
    # The pages spl-core generated for the configured build, under the
    # `generated/` names it gave them. Only those: the hand-written component
    # trees are in the source set already, and admitting them a second time would
    # parse every need in them twice.
    #
    # Nothing here decides which of them a build reads. spl-core lists the report
    # pages for the docs shape too, and the `generated/**` rule in ubproject.toml
    # removes them there -- declared once, where ubCode reads it as well.
    include_patterns.extend(pattern for pattern in _build_config.get("include_patterns", []) if pattern.startswith("generated/"))

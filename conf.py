# -*- coding: utf-8 -*-
"""Configuration"""
import datetime
import os

from pathlib import Path

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
    # `generated` is a symlink to the configured variant's build directory, and
    # Sphinx walks with followlinks=True -- so without this it descends the
    # whole build tree a second time, under a second set of paths that the
    # `build/...` exclusions above do not match. Excluding it prunes the walk
    # (get_matching_files applies exclude_patterns to directories, not just
    # files), which halves the scan on a small build directory and more on a
    # real one.
    #
    # It also means Sphinx CANNOT discover anything through `generated`, which
    # is the invariant test_ubproject_config.py guards: the report pages are
    # discovered through spl-core's `build/` patterns instead, and exactly one
    # of those two routes may ever be live or every page exists twice.
    "generated",
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
# Which cell of the matrix this build reads. Selecting a file is not the same as
# synthesizing data: the file is complete and generated, and nothing here adds a
# key to it.
#
# Three sources, in order. VARIANT_DATA_FILE if something passed one -- spl-core
# does from 8.9, and the tests do. Otherwise the fixed-name cell that CMake
# publishes for this build shape, which spl-core tells us via the directory its
# per-target configuration file sits in. Otherwise nothing, and the pointer named
# in ubproject.toml applies, which is what a bare `sphinx-build` and the IDE get.
#
# Without the middle step the reports build would quietly read the docs cell and
# every report fence would evaluate false -- a reports target with no reports in
# it, and no error anywhere.
# spl-core names the build shape by the directory holding the per-target
# configuration file it points us at. Derived once: the variant data file and
# the source set both depend on it, and two derivations of one fact drift.
_shape = "reports" if Path(os.environ.get("SPHINX_BUILD_CONFIGURATION_FILE", "")).parent.name == "reports" else "docs"

_variant_data_file = os.environ.get("VARIANT_DATA_FILE")
if not _variant_data_file:
    _published = Path(__file__).parent / "build" / f"variant-data-{_shape}.json"
    if _published.is_file():
        _variant_data_file = str(_published)

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
    # The generated pages of the CONFIGURED variant, named by spl-core for the
    # build it is running. This is what makes the `/build/**` globs in the report
    # sections resolve to one page each rather than one per variant on disk.
    #
    # A stable path would be better and `generated` exists for it, but spl-core
    # writes the gcovr tree at `reports/html/<build-relative page path>/coverage`
    # and looks its report artifacts up there too. Moving the page without moving
    # those breaks the coverage link, so the stable path waits for the spl-core
    # change. Only the hand-written component trees are dropped, because the
    # variant rules already own those; keeping them here would parse every need
    # in them a second time under a second docname.
    #
    # The report pages are admitted ONLY by the reports shape. spl-core writes
    # unit_test_spec.rst, unit_test_results.rst and coverage.rst at configure
    # time and lists them for both shapes, so a docs build would read all three
    # per component and reference none of them -- the fences that would have
    # linked them are false in a docs build. That is three orphan warnings per
    # component, fifteen on Spa, and no reader is better off for it.
    include_patterns.extend(
        pattern
        for pattern in _build_config.get("include_patterns", [])
        if pattern.startswith("build/")
        and (_shape == "reports" or not pattern.endswith("/reports/**"))
    )


# generated source listings ##################################################
#
# COMPATIBILITY SHIM, not a return of the Jinja pass.
#
# spl-core passes --jinja-raw-tags to clanguru, so every generated listing under
# __source_docs wraps its code-block in `{% raw %}` / `{% endraw %}` lines. The
# only thing that ever consumed those markers was the global Jinja `source-read`
# hook this project deleted, so without this they render as two literal
# paragraphs on every listing page in a reports build.
#
# This is a line filter, not a template render. Nothing is evaluated; no brace
# anywhere else in the project is touched; hand-written documents are not seen
# at all. The markers are replaced by EMPTY LINES rather than removed, so the
# file keeps its line count and a warning about a generated page still points at
# the right line -- the source-mapping breakage was one of the reasons the Jinja
# pass had to go, and re-creating it here would be missing the point.
#
# REMOVE THIS once pyproject.toml pins an spl-core that lets the flag be turned
# off (`SPL_SOURCE_DOCS_JINJA_RAW_TAGS`). No released version does today: 8.8.0
# is the newest stable and 9.0.1rc4 the newest prerelease, and both hardcode it.
# Until then this is load-bearing, not a TODO.
_JINJA_RAW_MARKERS = frozenset({"{% raw %}", "{% endraw %}"})


def _strip_jinja_raw_markers(app, docname, source):
    if "__source_docs/" not in f"{docname}/":
        return
    lines = source[0].splitlines(keepends=True)
    if not any(line.strip() in _JINJA_RAW_MARKERS for line in lines):
        return
    source[0] = "".join(
        ("\n" if line.endswith("\n") else "") if line.strip() in _JINJA_RAW_MARKERS else line
        for line in lines
    )


def setup(app):
    """Register the two handlers this configuration needs."""
    app.connect("source-read", _strip_jinja_raw_markers)

    if not _variant_data_file:
        return

    def _select_variant_data(app, config):
        config.needs_variant_data_file = _variant_data_file

    app.connect("config-inited", _select_variant_data, priority=20)

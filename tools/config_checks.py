"""Checks that the configuration both readers read is still intact.

conf.py runs them whenever Sphinx reads its configuration and reports each
finding as a warning, so a drift fails the build under `-W` instead of waiting
for someone to run the tests; test_ubproject_config.py calls the same functions.
needs-config-writer does the same for the configuration it writes
(`needscfg_warn_on_diff`).

Each check returns a list of findings, one sentence each, and nothing when all
is well.
"""

from __future__ import annotations

import tomllib
from importlib.resources import files
from pathlib import Path
from typing import Any

import variant_data

#: The Markdown documents both readers read: ubCode's md parser include, and the
#: trees conf.py names in `include_patterns`.
MARKDOWN_INCLUDES = ["index.md", "doc/**/*.md", "components/**/doc/**/*.md", "test/**/doc/**/*.md"]
MARKDOWN_TREES = ["index.md", "doc/**", "components/**/doc/**", "test/**/doc/**"]


def spl_core_config() -> dict[str, Any]:
    """The base configuration spl-core ships, as installed."""
    with files("spl_core.report_generation").joinpath("ubproject.toml").open("rb") as handle:
        return tomllib.load(handle)


def vendored_needs_model(project: dict[str, Any], spl_core: dict[str, Any]) -> list[str]:
    """spl-core's needs model is vendored into ubproject.toml; a copy has to stay a copy."""
    findings: list[str] = []
    expected_links = {link["option"]: {"incoming": link["incoming"], "outgoing": link["outgoing"]} for link in spl_core["needs"]["extra_links"]}
    if project["needs"].get("links") != expected_links:
        findings.append("the link types in ubproject.toml differ from spl-core's extra_links")
    fields = project["needs"].get("fields", {})
    for option in spl_core["needs"]["extra_options"]:
        if option not in fields:
            findings.append(f"spl-core declares the field {option!r}, ubproject.toml does not")
    ours = {need_type["directive"]: need_type for need_type in project["needs"].get("types", [])}
    for need_type in spl_core["needs"]["types"]:
        if ours.get(need_type["directive"]) != need_type:
            findings.append(f"the need type {need_type['directive']!r} differs from spl-core's, or is missing")
    for key in ("exclude", "respect_gitignore"):
        if project["source"].get(key) != spl_core["source"].get(key):
            findings.append(f"[source] {key} differs from spl-core's")
    return findings


def document_sets(project: dict[str, Any], include_patterns: list[str]) -> list[str]:
    """ubCode's parser includes and conf.py's include_patterns name the same documents."""
    findings: list[str] = []
    parsers = project.get("parse", {}).get("parsers", {})
    if parsers.get("md", {}).get("include") != MARKDOWN_INCLUDES:
        findings.append(f"the md parser include is not {MARKDOWN_INCLUDES}")
    for tree in MARKDOWN_TREES:
        if tree not in include_patterns:
            findings.append(f"conf.py does not include {tree!r}, which the md parser reads")
    return findings


def generated_half(project: dict[str, Any]) -> list[str]:
    """What the generated files decide, ubproject.toml must not decide as well.

    `extend` merges tables key by key but replaces arrays, and the extending
    file wins: a rule or an rst parser include in ubproject.toml would replace
    every generated one, silently. Excluding build/ would hide the selected
    build's pages, which the selection reads where spl-core writes them.
    """
    findings: list[str] = []
    if project.get("extend") != variant_data.RULES_FILE:
        findings.append(f"ubproject.toml has to extend {variant_data.RULES_FILE}, the generated rules")
    if project.get("source", {}).get("variant_sources"):
        findings.append(f"ubproject.toml declares rules; they would replace the generated ones (use {variant_data.HAND_WRITTEN_RULES})")
    if "include" in project.get("parse", {}).get("parsers", {}).get("rst", {}):
        findings.append("ubproject.toml declares the rst parser include; it would replace the selection's generated pages")
    hidden = [pattern for pattern in project.get("source", {}).get("extend_exclude", []) if pattern.rstrip("/*") == "build"]
    if hidden:
        findings.append(f"ubproject.toml excludes {hidden}, and with it the generated pages the selection reads")
    if "variant_data_file" in project.get("needs", {}):
        findings.append("ubproject.toml names a variant data file; the selection names it")
    return findings


def rule_grammar(project_root: Path) -> list[str]:
    """Every generated rule is inside the grammar both engines share."""
    rules_file = project_root / variant_data.RULES_FILE
    if not rules_file.is_file():
        return []
    from sphinx_mounts import variants

    findings: list[str] = []
    for rule in tomllib.loads(rules_file.read_text(encoding="utf-8")).get("source", {}).get("variant_sources", []):
        try:
            variants.validate(rule["if"])
        except Exception as error:  # noqa: BLE001 - the finding names whatever the grammar refused
            findings.append(f"the rule {rule['if']!r} is outside the shared grammar: {error}")
    return findings


def run_all(project_root: Path, include_patterns: list[str]) -> list[str]:
    project = tomllib.loads((project_root / "ubproject.toml").read_text(encoding="utf-8"))
    return [
        *vendored_needs_model(project, spl_core_config()),
        *document_sets(project, include_patterns),
        *generated_half(project),
        *rule_grammar(project_root),
    ]

# Variant management in SPLed

A guide by use case: how to look at a variant, how to see what a change does, and how to write
documentation that depends on the variant.

SPLed builds five product variants from one code base, and its documentation works the same way.
One set of documents describes every variant, and **data decides what one variant shows**. No
document is a template, and nothing in `conf.py` or CMake decides what a page contains:

- a **variant data file** per variant says which features are on and which components are in;
- **conditions** read that file: in the documents, and in **rules** that `tools/variant_data.py`
  generates from where each component's documentation lives, so no rule is written by hand;
- a **selection** file says which variant data file, and which build's generated pages, the editor
  and a plain build show;
- **Sphinx** and **ubCode**, with its command-line tool `ubc`, read the same files, so the editor
  shows what the build produces.

| I want to … | Use case |
| --- | --- |
| set up and generate the variant data | [1](#1-set-up-a-documentation-environment), [2](#2-generate-the-variant-data) |
| know which variant I am looking at | [3](#3-see-which-variant-you-are-working-on) |
| switch the variant my editor shows | [4](#4-switch-the-variant-your-editor-shows) |
| look at another variant without switching | [5](#5-look-at-another-variant-without-switching) |
| see what differs between two variants | [6](#6-see-what-differs-between-two-variants) |
| try a change without touching the product | [7](#7-try-a-change-without-touching-the-product) |
| understand what ubCode shows me | [8](#8-know-what-ubcode-shows-you) |
| make a paragraph, requirement or diagram depend on a feature | [9](#9-make-content-depend-on-a-feature) |
| print a variant value in the text | [10](#10-print-a-variant-value-in-the-text) |
| show a section only in the reports build | [11](#11-show-a-section-only-in-the-reports-build) |
| include a document only when its component is in the variant | [12](#12-include-a-document-only-when-its-component-is-in-the-variant) |
| put one document in different places per variant | [13](#13-place-one-document-differently-per-variant) |
| add a component, a feature or a variant | [14](#14-add-a-component), [15](#15-add-or-change-a-feature), [16](#16-add-a-variant) |
| link code to the design, per variant | [17](#17-trace-code-to-the-design-per-variant) |
| check my work, or find out why something is missing | [18](#18-run-the-checks), [19](#19-when-something-looks-wrong) |

New to SPLed? Go through use cases 1 to 8 once, in order.

## The idea in one picture

```mermaid
flowchart LR
    subgraph edit["You edit"]
        K["KConfig<br/>the feature model"]
        C["variants/Sleep/config.txt<br/>the features of a variant"]
        P["variants/Sleep/parts.cmake<br/>the components of a variant"]
    end
    G(["tools/variant_data.py<br/>run by CMake configure"])
    subgraph gen["Generated, never edited"]
        V["build/variants/Sleep/test/docs.json<br/>one file per variant, kit and target"]
        RU["ubproject.variants.toml<br/>one rule per component"]
        A["build/selection.toml<br/>the build you work on"]
    end
    R["documents<br/>hold the {if} conditions"]
    U["ubCode and ubc"]
    S["sphinx-build"]
    K --> G
    C --> G
    P --> G
    G --> V
    G --> RU
    G --> A
    A -->|names| V
    RU --> U
    RU --> S
    A --> U
    A --> S
    R --> U
    R --> S
    V -.->|"-c override"| U
    V -.->|"-D override"| S
```

## Words you will meet

| Word | Meaning in SPLed |
| --- | --- |
| **Variant** | A product configuration: `Disco`, `Sleep`, `Spa`, `IDEA/Sloemada` or `Base/Dev`. Each is a folder under `variants/`. |
| **Feature** | A switch or value of the feature model `KConfig`, such as `BLINKING` or `CUSTOMER`. A variant sets its features in its `config.txt`. |
| **Component** | A folder under `components/`, plus the integration suite `test/spled_integration`. A variant lists its components in its `parts.cmake`. |
| **Kit** | `prod`, the product, or `test`, which adds unit tests, coverage and, for Disco, the integration suite. |
| **Target** | `docs`, the documents, or `reports`, the documents plus test results and coverage. |
| **Variant data file** | `build/variants/<variant>/<kit>/<target>.json`, one per combination: 5 variants × 2 kits × 2 targets = 20 files, plus one per component report under `<kit>/<component>/`. |
| **Rules** | `ubproject.variants.toml`, generated: one rule per component, which leaves the component's documents out of a variant that does not contain it. |
| **Selection** | `build/selection.toml`, generated when a variant is selected: which variant data file the editor and a plain `sphinx-build` read, and, for a CMake build's reports, that build's generated pages, read where the build writes them. |
| **150 % documentation** | Every document of every variant lives in the tree. Conditions remove what one variant does not have. |
| **`var.*`** | How a condition reads the variant data: `var.features.BLINKING`, `var.build_config.components`. |

## What a variant data file contains

`build/variants/Sleep/test/docs.json`, shortened:

```json
{
  "build_config": {
    "components": ["components/platform_types", "components/rte", "…", "components/brightness_controller", "components/auto_off"],
    "component": "",
    "kit": "test",
    "scope": "variant",
    "target": "docs",
    "variant": "Sleep"
  },
  "features": {
    "AUTO_OFF": true,
    "AUTO_OFF_PERIOD_SECONDS": 10,
    "BLINKING": false,
    "BRIGHTNESS_ADJUSTMENT_MANUAL": true,
    "CUSTOMER": "B"
  }
}
```

- `features` holds every symbol of the feature model with this variant's value. Booleans are
  `true` or `false`, numbers are numbers, strings are strings. Every boolean is present, also
  the ones that are off, so a condition on it always has an answer.
- `build_config.components` is the variant's component list, read from its `parts.cmake`.
- `build_config.variant`, `kit` and `target` say which combination the file describes.
- `build_config.scope` is `variant`, or `component` in the file of a per-component report, whose
  `build_config.component` names the component.

Everything under `build/` is generated, and nobody edits it; VS Code opens it read-only. To change
a variant, change its sources ([15](#15-add-or-change-a-feature), [16](#16-add-a-variant)), or
try a change on a copy ([7](#7-try-a-change-without-touching-the-product)).

## Setup

**The quickest way in** is the guided tour, which works the same on Linux, macOS and Windows.
It needs only Python 3.11+ and [uv](https://docs.astral.sh/uv/); `ubc` for the ubCode side, and
CMake, Ninja and a C/C++ compiler for the build cases. Each step says what it is about to do, runs
it, and then says what to look at and what to expect:

```bash
python tools/try_variants.py                                  # the cases, and what each needs
python tools/try_variants.py setup                            # .venv, the variant data, the rules
python tools/try_variants.py docs -v Sleep                    # one variant's documents in Sphinx and ubc
python tools/try_variants.py build -v Disco                   # a CMake build: reports, test results
python tools/try_variants.py component light_controller       # one component's report
python tools/try_variants.py compare Disco Spa                # the needs that differ ([6](#6-see-what-differs-between-two-variants))
python tools/try_variants.py check                            # the tests and the CI gate ([18](#18-run-the-checks))
python tools/try_variants.py all                              # all of it, in that order
```

Its output goes to `build/try/`. The rest of this guide is the same steps by hand.

### 1. Set up a documentation environment

You need Python 3.12 and the locked Python dependencies. Nothing in this guide needs a compiler.

- **Full toolchain**, to build the firmware as well: follow [Start developing](README.md#start-developing).
- **Documentation only**, the same steps the CI documentation job runs:

  ```bash
  pipx install poetry==2.4.1
  POETRY_VIRTUALENVS_IN_PROJECT=true poetry install --no-root   # creates .venv
  source .venv/bin/activate
  ```

  On Windows, run `$env:POETRY_VIRTUALENVS_IN_PROJECT = "true"` before `poetry install --no-root`,
  and activate with `.venv\Scripts\Activate.ps1`.

For the editor, install the **ubCode** extension (`useblocks.ubcode`) in VS Code and open the
repository folder. ubCode reads `ubproject.toml`; there is nothing else to configure. The
command-line tool `ubc` ships inside the extension, in `server/cli/` under the extension's folder
in `~/.vscode/extensions/`. Put that folder on your `PATH`.

All commands below run from the repository root, with the virtualenv activated.

### 2. Generate the variant data

```bash
python tools/variant_data.py --all
```

- This writes the variant data files under `build/variants/`, from `KConfig`, each variant's
  `config.txt` and each variant's `parts.cmake`, and the rules file `ubproject.variants.toml`.
  KConfig is pure Python, so it needs neither a compiler nor CMake.
- Run it again whenever `KConfig`, a `config.txt` or a `parts.cmake` changes.
  `python tools/variant_data.py --all --check` tells you whether the files are up to date; CI runs
  it.
- Configuring a CMake build, with the build scripts or the CMake extension, writes the files of the
  variant it configures, and selects that build ([4](#4-switch-the-variant-your-editor-shows)).

## Explore

### 3. See which variant you are working on

The selection says it:

```bash
python -c "import tomllib; print(tomllib.load(open('build/selection.toml', 'rb'))['needs']['variant_data_file'])"
```

```text
/home/you/SPLed/build/variants/Disco/test/reports.json
```

If the selection also reads a build's generated pages, its `[parse.parsers.rst]` entry names
them, below the build directory, and `build/selected_build.txt` names the directory.

The documentation says it as well: its start page shows **Variant: Disco**. The page takes that
from the variant data file ([10](#10-print-a-variant-value-in-the-text)).

### 4. Switch the variant your editor shows

- **In VS Code:** *Terminal → Run Task… → Select documentation variant*, then pick the variant
  and the kit.
- **On the command line:**

  ```bash
  python tools/variant_data.py --variant Sleep --kit test --current
  ```

Both write `build/selection.toml`, which names the chosen variant's `docs` file, so ubCode and a
plain `sphinx-build` now read Sleep. If the editor still shows the previous variant, reload the
window (*Command Palette → Developer: Reload Window*).

- The kit defaults to `prod`. Give `--kit test` for the test kit.
- Configuring a CMake build selects that build: a `test` kit build its `reports` file and its
  generated pages, where the build writes them; a `prod` kit build its `docs` file.

### 5. Look at another variant without switching

You do not have to switch to look at a variant. Point the reader at its file instead.

- **The rendered documentation (Sphinx):**

  ```bash
  python -m sphinx -b html -D needs_variant_data_file=build/variants/Sleep/test/docs.json . build/docs/Sleep
  ```

  Then open `build/docs/Sleep/index.html`. A build takes a few seconds. In VS Code, the task
  *Build documentation for a variant* does the same, and also puts the variant's name in the page
  title.
- **ubCode's view (ubc):**

  ```bash
  ubc check -c "needs.variant_data_file = 'build/variants/Sleep/test/docs.json'"
  ```

  Each `info[toctree.variant_excluded]` line names a document this variant leaves out, and the
  rule that removed it. `ubc check` also lists the project's other warnings, so its exit code says
  nothing about the variant.

`-D` for Sphinx and `-c` for ubc override the same setting, `variant_data_file`.

To look at another **build**, with its generated pages, hand the readers that build's own
selection file. CMake writes one per documentation run into the build directory:

```bash
python -m sphinx -b html -D spl_selection=build/Spa/test/Debug/selection/reports.toml . build/docs/Spa
ubc check -c "$(cat build/Spa/test/Debug/selection/reports.toml)"
```

spl-core does the same for every `docs` and `reports` run it starts, so the reports of two builds
can be built side by side.

### 6. See what differs between two variants

Build both variants as in [5](#5-look-at-another-variant-without-switching), then compare them.

- **Pages.** Sleep has pages for `auto_off` and `brightness_controller`, and Disco does not. On
  the light controller page, Disco shows the blinking state diagram and Sleep does not.
- **Needs.** Every HTML build also writes a `needs.json` next to its `index.html`. `ubc diff`
  compares two of them:

  ```bash
  ubc diff -n build/docs/Disco/needs.json -n build/docs/Sleep/needs.json
  ```

  Or skip the builds and compare the current variant with another one directly:

  ```bash
  ubc diff -c "needs.variant_data_file = 'build/variants/Sleep/test/docs.json'"
  ```

  The output lists every need that is new, removed or changed. For Disco against Sleep, it starts
  with `New need SWDD_AO-100`, the first of the auto-off requirements that only Sleep has.
- **Builds.** Every build keeps its own report pages and `needs.json`
  (`build/<variant>/<kit>/<type>/reports/html/needs.json`), so two builds compare with `ubc diff -n`,
  or directly with the other build's selection file:

  ```bash
  ubc diff -c "$(cat build/Spa/test/Debug/selection/reports.toml)"
  ```

### 7. Try a change without touching the product

Do not edit a variant data file. It is generated, and the next run overwrites it. For a what-if,
use one of these, from the quickest to the most complete:

1. **One value, in ubc.** Override the value on the command line:

   ```bash
   ubc diff -c "needs.variant_data.features.BLINKING = false"
   ```

   With Disco as the current variant this prints `Removed need SWDD_LC-101` and
   `Removed need SWDD_LC-203`, the two blinking requirements. The same `-c` works with `ubc check`
   and `ubc build needs`.
2. **Any change, in both readers.** Copy a variant data file to a folder outside `build/`, edit
   the copy, and point the readers at it:

   ```bash
   cp build/variants/Disco/test/docs.json /tmp/what-if.json   # now edit /tmp/what-if.json
   python -m sphinx -b html -D needs_variant_data_file=/tmp/what-if.json . build/docs/what-if
   ubc check -c "needs.variant_data_file = '/tmp/what-if.json'"
   ```

   On Windows, use any folder outside `build/` instead of `/tmp`.
3. **The real change.** Change the variant itself, in its `config.txt` or `parts.cmake`
   ([15](#15-add-or-change-a-feature), [16](#16-add-a-variant)), regenerate with
   `python tools/variant_data.py --all`, and look again. This changes the product, so revert it if
   it was only an experiment.

### 8. Know what ubCode shows you

- **Inactive blocks are faded, not hidden.** The editor fades the source of an `{if}` block whose
  condition is false, the way a C editor fades code under a false `#if`. The preview shows the
  block collapsed and greyed, labelled with its condition. Its needs are still left out of the
  index, as in the Sphinx build.
- **Left-out documents are information, not errors.** The components page lists every component
  ([12](#12-include-a-document-only-when-its-component-is-in-the-variant)). An entry for a
  component the variant does not have is reported as `toctree.variant_excluded`, with the rule
  that removed the document.
- **Generated pages after a build.** Test results, test specifications and source listings exist
  after a CMake build of the test kit, under its build directory. The selection names them, so
  ubCode reads exactly the pages Sphinx reads, of that one build. Before the build they do not
  exist, and the editor shows the documents without them.

ubCode's side is described in [ubCode's guide to variants](https://ubcode.useblocks.com/usage/variants.html).

## Write

### 9. Make content depend on a feature

Wrap the content in the `if` directive of Sphinx-Needs. Its condition is a Python expression over
`var.*`.

In Markdown, use a fence of four backticks, so that the block can hold directives with three:

`````markdown
````{if} var.features.BLINKING
```{spec} Blinking Behavior
:id: SWDD_LC-101

...
```
````
`````

In reStructuredText:

```rst
.. if:: var.features.BLINKING

   This paragraph exists only in variants with blinking.
```

- There is no `else`. Write a second block with the opposite condition,
  `not var.features.BLINKING`; the light controller page does this for its two state diagrams.
- Strings and numbers compare as in Python: `var.features.CUSTOMER == "A"`, as in
  `doc/customer_requirements/index.md`, or `var.features.AUTO_OFF_PERIOD_SECONDS > 5`.
- Content behind a false condition is never read, so its needs do not exist in that variant, in
  Sphinx and in ubCode alike.
- A condition that names a key the variant data file does not have gives the warning
  `'if' directive expression failed`, and the block is left out.

### 10. Print a variant value in the text

The `variant` role puts a value where it stands:

- in Markdown: `` {variant}`features.CUSTOMER` `` prints `B` in Sleep;
- in reStructuredText: `` :variant:`features.CUSTOMER` ``.

The path starts below `var`, so it is `features.CUSTOMER`, not `var.features.CUSTOMER`. A list is
printed comma-separated, for example `` {variant}`build_config.components` ``. An unknown key gives
a warning and prints nothing. The start page uses `` {variant}`build_config.variant` ``.

### 11. Show a section only in the reports build

A `reports` build adds test results and coverage. Gate the section on the target:

`````markdown
````{if} var.build_config.target == "reports"
## Verification

```{toctree}
:maxdepth: 1
:glob:

/build/**/components/light_controller/reports/unit_test_results
/build/**/components/light_controller/reports/coverage
```
````
`````

The component pages end with a block like this one. The pages are where the build writes them,
`build/<variant>/<kit>/<build type>/components/…`, and the glob finds exactly one of each: a
reader reads the pages of one build only, the selected one. Always name the component's own path
in the entry; a bare `/build/**/reports/coverage` would also find every other component's.

### 12. Include a document only when its component is in the variant

You do not write anything for it. `tools/variant_data.py` generates one rule per component that has
a `doc/index` page, into `ubproject.variants.toml`:

```toml
[[source.variant_sources]]
if = "'components/auto_off' in var.build_config.components and (var.build_config.scope == 'variant' or var.build_config.component == 'components/auto_off')"
files = ["components/auto_off/**"]
```

- When the condition is false, the files are left out before anything is read: no page, no needs,
  and no warning about a page that no toctree lists.
- The components page, `doc/components/index.md`, globs every component's documentation, so it
  lists exactly the variant's components.
- The second half of the condition is for the per-component report, which shows one component.
- **Gate on the component list, never on the variant name.** The list comes from the variant's
  `parts.cmake`, so the product structure is written down once.
  `test_no_rule_names_a_variant_by_name` fails if a rule names a variant.
- Rule conditions, such as those of use case 13, use a smaller grammar than `{if}`. A boolean needs `== True`, as in
  `if = "var.features.AUTO_OFF == True"`. `and`, `or`, `not`, `==`, `!=`, `<`, `>`, `in` and
  `not in` work. A condition outside the grammar stops the Sphinx build. A condition that names an
  unknown key is reported, and removes its files.

### 13. Place one document differently per variant

Toctrees in SPLed carry no conditions. Sphinx reads every document it finds, whether a toctree lists
it or not, so a condition on a toctree entry could only take the entry away: the document would stay
in the build, with its needs, but without a place in the navigation. SPLed has no document that
changes its place per variant. If one ever has to:

1. Put the content where neither reader looks for documents, for example `doc/_shared/safety_concept.md`,
   and exclude that folder in `conf.py` (`exclude_patterns`) and in `ubproject.toml`
   (`[source] extend_exclude`).
2. Write two thin pages at the two places. Each one pulls the content in:

   ````markdown
   ```{include} /doc/_shared/safety_concept.md
   ```
   ````
3. Gate the two pages with a rule and its **negation**, so that every variant has exactly one of
   them. Hand-written rules go into `doc/variant_rules.toml`, which `tools/variant_data.py` adds to
   the generated ones; `ubproject.toml` cannot hold rules, because `extend` replaces an array:

   ```toml
   [[source.variant_sources]]
   if = "var.features.BLINKING == True"
   files = ["doc/chapter_x/safety_concept.md"]

   [[source.variant_sources]]
   if = "not (var.features.BLINKING == True)"
   files = ["doc/chapter_y/safety_concept.md"]
   ```

Two independent conditions could both be false for a variant, and the content would disappear
without a warning.

## Extend

### 14. Add a component

1. Add `spl_add_component(components/<name>)` to the `parts.cmake` of every variant that has it.
2. Write its documentation in `components/<name>/doc/index.md`. If its sources implement design
   needs, give that page a `## Traceability` section with a `src-trace` block
   ([17](#17-trace-code-to-the-design-per-variant)), and end it with a `## Verification` section
   for the reports, as the other components do ([11](#11-show-a-section-only-in-the-reports-build)).
3. Regenerate: `python tools/variant_data.py --all`, or configure a build.

That is all. The generator writes the component's rule, and the glob toctree in
`doc/components/index.md` lists its page. No rule and no toctree line is written by hand, and
nothing under `build/` is touched. To have the report tasks in VS Code offer the component, add it to the `component` input in `.vscode/tasks.json`. For
the code side of a component, see [AGENTS.md](AGENTS.md#spl-specific-cmake-patterns).

### 15. Add or change a feature

1. Declare the feature in `KConfig`, for example:

   ```text
   config NIGHT_MODE
       bool "Night mode"
       default n
   ```

2. Switch it on where it applies: `CONFIG_NIGHT_MODE=y` in `variants/<variant>/config.txt`. The VS
   Code task *Configure variant* opens KConfig's graphical editor for the same file.
3. Regenerate: `python tools/variant_data.py --all`. Every variant data file now has
   `"NIGHT_MODE": true` or `"NIGHT_MODE": false`.
4. Use it: `var.features.NIGHT_MODE` in an `{if}` block, `var.features.NIGHT_MODE == True` in a
   rule.

CMake sees the same symbol as `NIGHT_MODE="True"` for conditional components; see
[AGENTS.md](AGENTS.md#kconfig-feature-system).

### 16. Add a variant

1. Create `variants/<Name>/` with a `config.cmake`, copied from an existing variant, a
   `parts.cmake` with its components, and a `config.txt` with its feature values, which the VS Code
   task *Configure variant* can write. `tools/variant_data.py` finds every folder that holds a
   `config.cmake`.
   `Base/Dev` shows that a variant may sit two levels deep and may have no `config.txt`.
2. Regenerate: `python tools/variant_data.py --all`. This adds the four files
   `build/variants/<Name>/{prod,test}/{docs,reports}.json`.
3. Add the name where tools and tests list the variants: `.vscode/cmake-variants.json`, the
   `variant` input in `.vscode/tasks.json`, `VARIANTS` in `test/test_documentation.py`,
   `known_variants` and the expected documents in `test/test_ubproject_config.py`, and the lists in
   `test/test_variant_data.py`. Build tests for the variant go into `test/<Name>/`.

No rule and no document has to change. The rules gate on components, so the new variant gets its
documents from its `parts.cmake`.

### 17. Trace code to the design, per variant

An implementation need lives in the source file, as a one-line comment right above the code it
describes:

```c
// @need Periodic Brightness Adjustment, SWIMPL_BC-001c, impl, [SWDD_BC-100, SWDD_BC-102], [REQ_46, REQ_48]
```

The fields are the title, the ID, the type, the design needs it implements and the requirements it
fulfills. Each component's page shows its needs with one `src-trace` block, in a `## Traceability`
section:

````text
```{src-trace}
:project: components
:directory: brightness_controller
```
````

Both readers read the same comments, so the needs are part of the `docs` build, and ubCode shows
them without building anything. Each need links to its line on GitHub. Test specifications stay in
`@rst` blocks in the test sources.

**The preprocessor decides per variant.** A need inside an `#ifdef` branch exists only in the
variants that compile that branch. A link that holds only in some variants therefore belongs to a
need inside that branch. `SWDD_BC-203` exists only with automatic brightness adjustment, so the
runnable's automatic branch carries `SWIMPL_BC-004c` for it, and the runnable's own need
`SWIMPL_BC-003c` does not link it.

codelinks takes the branches from `build/compile_commands.json`. Every build of the selected CMake
build copies its compile database there (`tools/compile_commands.py`), without the `-save-temps`
option of the `test` kit, which libclang rejects. After configuring without building, run
`cmake --build <build dir> --target spled_codelinks_compile_commands`. Without the file, codelinks
treats every `#ifdef` as false, and Sphinx warns.

## Check

### 18. Run the checks

```bash
python -m pytest -m docs                                                   # the documentation gate
python -m pytest test/test_ubproject_config.py test/test_variant_data.py   # rules and variant data
```

- `-m docs` builds every variant's documents. Among other things, it checks that each variant has
  exactly its components' documents, that no document uses Jinja, and that ubc and Sphinx leave out
  the same documents. In VS Code, the tasks *Documentation gate (all variants)* and
  *Check documentation with ubc (all variants)* run it.
- The ubc tests find `ubc` through the `UBC` environment variable, on the `PATH` or in the ubCode
  extension folder, and are skipped when it is not there. CI installs ubc and fails instead of
  skipping.
- The tests regenerate `build/variants/` and the rules, and restore `build/selection.toml` when
  they have selected another cell.

### 19. When something looks wrong

| What you see | What to do |
| --- | --- |
| A block or a page is missing in one variant | Its condition is false there, or it names a key that is not in the variant data file. Look the key up in `build/variants/<variant>/<kit>/docs.json`, check the spelling, and look for `'if' directive expression failed` or a rule warning in the build output. In a rule, a boolean needs `== True`. |
| The editor shows another variant than you expect | Look at the selection ([3](#3-see-which-variant-you-are-working-on)). Configuring a CMake build selects that build. Switch back ([4](#4-switch-the-variant-your-editor-shows)) and reload the window. |
| Sphinx stops with `No variant is selected` | `build/selection.toml` does not exist yet. Configure a build, or select a cell ([4](#4-switch-the-variant-your-editor-shows)). ubc stops for the same reason, with `Configuration file could not be loaded`. |
| A change to a file under `build/` is gone | `build/` is generated and rewritten on every run. Change `KConfig`, a `config.txt` or a `parts.cmake` instead, or try the change on a copy ([7](#7-try-a-change-without-touching-the-product)). |
| `python tools/variant_data.py --all --check` fails | The variant data is older than its sources. Run `python tools/variant_data.py --all`. |
| A link from a need in the code is dead in one variant | The need sits outside the `#ifdef` that decides the link. Give the link to a need inside the branch that implements it ([17](#17-trace-code-to-the-design-per-variant)). |
| Sphinx warns `compile_commands … is not a readable file` | codelinks has no compile database and treats every `#ifdef` as false. Build the selected build, or its `spled_codelinks_compile_commands` target ([17](#17-trace-code-to-the-design-per-variant)). |
| ubCode shows no test results or listings | The selected build has not been built yet, or the selection names a `docs` shape. Build the test kit's `reports` target ([8](#8-know-what-ubcode-shows-you)). |
| A listing shows the code of the wrong `#ifdef` branch | A known clanguru issue: it drops the `-isystem` directory of the feature header, so every feature reads as undefined in the listings. The gate's reports shape fails on it; it is fixed in clanguru. |

## Rules of thumb

- Everything a condition names has to be in the variant data file. If a condition needs a new
  fact, add it to `KConfig`, a `config.txt` or a `parts.cmake`, never to `conf.py`.
- Gate whole documents on components, blocks on features, and report sections on the target. Never
  gate on the variant name.
- No Jinja in documents, no conditions in toctree entries, and no variant selection in `conf.py`.
  Select a variant by configuring a build or with `tools/variant_data.py --current`; look at
  another one with `-D` for Sphinx and `-c` for ubc.
- A link that holds only in some variants belongs to a need inside the `#ifdef` branch that
  implements it.
- Do not edit `build/` or `ubproject.variants.toml`.
- After changing a variant's sources, regenerate and run `python -m pytest -m docs`.

The design behind all this is described under
[Variant-Dependent Documentation in AGENTS.md](AGENTS.md#variant-dependent-documentation).

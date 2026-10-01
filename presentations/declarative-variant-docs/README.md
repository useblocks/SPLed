# Variant documentation without templates

A [Marp](https://marp.app) deck in the useblocks theme. It covers how avengineers'
SPLed and spl-core build variant documentation today, why static readers such
as ubCode and ubc cannot read it, how the useblocks forks fix it, and what is
still open.

- `slides.md` is the deck. Speaker notes are the HTML comments under each slide.
- `images/` holds the two pipeline diagrams as SVG, drawn in the theme's colours.
- `ub_Logo.svg` is the logo the theme puts on every slide.

## Theme

The front matter and the whole `style: |` block come verbatim from
[`assets/marp/useblocks-marp-template.md`](https://github.com/useblocks/team/blob/main/assets/marp/useblocks-marp-template.md)
in the useblocks team repository (private). To pick up a newer template, replace
the CSS between `style: |` and the closing `---` of the front matter with the
template's, and copy its `ub_Logo.svg` next to the deck.

## Present or export

The theme's badges, notes, cards and tiles are HTML, so every export needs
`--html`. Without it, Marp escapes part of that markup and stray tags show up on
the slides. With Node.js and
a Chromium-based browser (`CHROME_PATH` points marp-cli at one):

```bash
npx @marp-team/marp-cli@4.5.1 --no-stdin slides.md --html --allow-local-files -o slides.html
npx @marp-team/marp-cli@4.5.1 --no-stdin slides.md --html --allow-local-files --pdf -o slides.pdf
```

`--allow-local-files` lets the export read the diagrams and the logo. In the
HTML export, press `p` for the presenter view with the speaker notes.
`slides.html` and `slides.pdf` are ignored by git.

In VS Code, the Marp extension renders the theme only when `markdown.marp.html`
is set to `all` and the workspace is trusted.

## Sources

Every reference on the slides is a link. The numbers and quotes come from
avengineers/SPLed `develop` at
[f5ba89e](https://github.com/avengineers/SPLed/commit/f5ba89efcabb494ccc66a7619943260444c497de),
avengineers/spl-core 8.9.0 at
[95a6347](https://github.com/avengineers/spl-core/commit/95a634771491f7c649566b06e3e1fed3f422d86b),
and the useblocks forks after merging
[useblocks/SPLed#4](https://github.com/useblocks/SPLed/pull/4) (`develop` at e79a759),
[useblocks/spl-core#5](https://github.com/useblocks/spl-core/pull/5) (ce62088) and
[useblocks/clanguru#1](https://github.com/useblocks/clanguru/pull/1) (50a25d7), with
[CI run 36923824832](https://github.com/useblocks/SPLed/actions/runs/36923824832).

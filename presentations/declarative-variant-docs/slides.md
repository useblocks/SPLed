---
marp: true
theme: default
class: invert
paginate: true
title: Variant documentation without templates
description: How SPLed and spl-core build variant documentation, why static readers such as ubCode and ubc cannot read it, and how the useblocks forks fix it.
style: |
  /* ═══════════════════════════════════════════════════════════════════════
     useblocks — Marp Presentation Template
     ═══════════════════════════════════════════════════════════════════════ */

  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');

  /* ── Base Section ────────────────────────────────────────────────────── */
  section {
    font-family: 'Inter', sans-serif;
    font-size: 26px;
    font-weight: 400;
    color: #CECECE;
    padding-top: 90px;
    padding-left: 40px;
    padding-right: 40px;
    background-color: #1C1C1C;
    background-image: url(ub_Logo.svg);
    background-repeat: no-repeat;
    background-position: top 30px right 30px;
    background-size: 160px;
    justify-content: flex-start;
    position: relative;
  }
  section > :first-child {
    margin-top: 0;
  }

  /* ── Typography ──────────────────────────────────────────────────────── */
  h1 {
    font-family: 'Inter', sans-serif;
    font-weight: 900;
    color: #FFFFFF;
    position: absolute;
    top: 35px;
    left: 40px;
    margin: 0;
    padding: 0;
  }
  h2 {
    font-family: 'Inter', sans-serif;
    font-weight: 900;
    color: #CECECE;
    margin-top: 0;
    padding-top: 0;
  }
  h3 {
    font-family: 'Inter', sans-serif;
    font-weight: 900;
    color: #656565;
    margin-top: 0;
    padding-top: 0;
  }
  strong {
    color: #E4FF3D;
  }
  /* PR titles tagged as highlights override the brand-yellow strong color
     with a contrasting light purple so they pop against the surrounding
     yellow bold titles. */
  strong.pr-highlight {
    color: #B59AFF;
  }
  a {
    color: #E4FF3D;
    text-decoration: underline;
    text-decoration-thickness: 1px;
    text-underline-offset: 3px;
  }

  /* Repo-class block on the title slide. Centered flex layout so the
     columns hug their content instead of spreading edge-to-edge like
     `.columns-3` does (each 1fr track of which would expand to fill 1/N
     of the slide width). Defined here (not inline) because Marpit strips
     raw `style` attributes from HTML. */
  .title-repo-grid {
    display: flex;
    justify-content: center;
    gap: 2.5rem;
    margin-top: 1.5rem;
    text-align: left;
    font-size: 0.85em;
  }

  /* Contributors list below the KPI tiles on the At-a-glance slide.
     Vertical stack, centered, slightly muted so it sits as a footer-row
     rather than competing with the big KPI numbers. */
  .contributors-line {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
    font-size: 0.75em;
    color: #A0A0A0;
    margin-top: 1.5rem;
  }
  .contributors-line .contributors-label {
    color: #656565;
    font-size: 0.85em;
    margin-bottom: 0.3rem;
  }

  /* ── Badge ───────────────────────────────────────────────────────────── */
  .badge {
    position: absolute;
    top: 0;
    left: 40px;
    display: inline-block;
    background-color: #E4FF3D;
    color: #1C1C1C;
    font-size: 18px;
    font-weight: 700;
    padding: 3px 48px;
    border-radius: 0 0 10px 10px;
    z-index: 10;
    min-width: 140px;
    text-align: center;
  }

  /* ── Tables ──────────────────────────────────────────────────────────── */
  table {
    font-size: 20px;
    width: 85%;
    margin: 0 auto;
    border-collapse: collapse;
  }
  th {
    background-color: #292929;
    color: #E4FF3D;
    font-weight: 900;
    text-align: left;
    padding: 12px 20px;
    border-bottom: 2px solid #E4FF3D;
  }
  td {
    background-color: #1C1C1C;
    border-color: #404040;
    padding: 10px 20px;
    border-bottom: 1px solid #333;
  }
  tr:hover td {
    background-color: #252525;
  }
  .compact-table td, .compact-table th {
    padding: 10px 24px;
  }
  .compact-table {
    font-size: 19px;
    width: 100%;
  }
  .compact-table table {
    width: 70% !important;
    margin-left: auto !important;
    margin-right: auto !important;
  }

  /* ── Code ─────────────────────────────────────────────────────────────── */
  code {
    font-size: 20px;
    background-color: #292929;
    color: #E4FF3D;
  }
  pre {
    font-size: 18px;
    background-color: #292929;
  }
  pre code {
    color: #CECECE;
  }

  /* ── Blockquotes ─────────────────────────────────────────────────────── */
  blockquote {
    border-left: 4px solid #404040;
    color: #656565;
  }

  /* ── Images ──────────────────────────────────────────────────────────── */
  section img {
    max-height: 420px;
    width: auto;
    object-fit: contain;
  }

  /* ── Note / Footnote ─────────────────────────────────────────────────── */
  .note {
    font-size: 14px;
    color: #656565;
    text-align: center;
    margin-top: 12px;
  }

  /* ═══════════════════════════════════════════════════════════════════════
     TITLE SLIDE
     ═══════════════════════════════════════════════════════════════════════ */
  section.title-slide {
    justify-content: center;
    padding-top: 0;
    padding-bottom: 60px;
  }
  section.title-slide h1 {
    position: static;
    text-align: center;
    width: 100%;
    font-size: 48px;
    margin-bottom: 8px;
    letter-spacing: -0.5px;
  }
  section.title-slide h2 {
    text-align: center;
    font-size: 28px;
    color: #E4FF3D;
    font-weight: 700;
    margin-bottom: 4px;
  }
  section.title-slide h3 {
    text-align: center;
    font-size: 18px;
    color: #656565;
    font-weight: 400;
    margin-top: 24px;
  }
  .title-divider {
    width: 80px;
    height: 4px;
    background-color: #E4FF3D;
    margin: 16px auto;
    border: none;
    border-radius: 2px;
  }
  .title-date {
    text-align: center;
    font-size: 16px;
    color: #656565;
    margin-top: 8px;
  }

  /* ═══════════════════════════════════════════════════════════════════════
     SECTION DIVIDER
     ═══════════════════════════════════════════════════════════════════════ */
  section.section-divider {
    justify-content: center;
    padding-top: 0;
    text-align: center;
  }
  section.section-divider h1 {
    position: static;
    text-align: center;
    width: 100%;
    font-size: 44px;
    margin-bottom: 12px;
  }
  section.section-divider h3 {
    text-align: center;
    font-size: 22px;
    font-weight: 400;
    margin-top: 0;
  }
  .section-number {
    display: inline-block;
    font-size: 64px;
    font-weight: 900;
    color: #E4FF3D;
    margin-bottom: 8px;
  }

  /* ═══════════════════════════════════════════════════════════════════════
     STATEMENT SLIDE — Full-screen bold message
     ═══════════════════════════════════════════════════════════════════════ */
  section.statement-slide {
    justify-content: center;
    padding-top: 0;
    text-align: center;
  }
  section.statement-slide h1 {
    position: static;
    text-align: center;
    width: 100%;
    font-size: 44px;
    line-height: 1.25;
  }
  section.statement-slide h3 {
    text-align: center;
    font-size: 22px;
    font-weight: 400;
    margin-top: 16px;
  }

  /* ═══════════════════════════════════════════════════════════════════════
     CALLOUT BOXES
     ═══════════════════════════════════════════════════════════════════════ */
  .highlight,
  .warn,
  .success,
  .danger {
    background: #292929;
    padding: 0.6rem 1rem;
    border-radius: 4px;
    margin-top: 1.5rem;
  }
  .highlight { border-left: 4px solid #E4FF3D; }
  .warn      { border-left: 4px solid #656565; }
  .success   { border-left: 4px solid #4ADE80; }
  .danger    { border-left: 4px solid #F87171; }

  /* ═══════════════════════════════════════════════════════════════════════
     COLUMNS
     ═══════════════════════════════════════════════════════════════════════ */
  .columns {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
  }
  .columns-3 {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 1.5rem;
  }
  .columns-70-30 {
    display: grid;
    grid-template-columns: 7fr 3fr;
    gap: 1.5rem;
  }
  .columns-30-70 {
    display: grid;
    grid-template-columns: 3fr 7fr;
    gap: 1.5rem;
  }

  /* ═══════════════════════════════════════════════════════════════════════
     CARDS
     ═══════════════════════════════════════════════════════════════════════ */
  .card-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-top: 8px;
  }
  .card-grid-3 {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 16px;
    margin-top: 8px;
  }
  .card {
    background: #292929;
    border-top: 3px solid #E4FF3D;
    border-radius: 8px;
    padding: 16px 18px;
  }
  .card h4 {
    margin: 0 0 6px 0;
    color: #FFFFFF;
    font-size: 20px;
    font-weight: 900;
  }
  .card p {
    margin: 0;
    color: #999;
    font-size: 18px;
    line-height: 1.4;
  }
  .card .card-icon {
    font-size: 28px;
    margin-bottom: 6px;
  }

  /* ═══════════════════════════════════════════════════════════════════════
     LICENSE / INFO GRID
     ═══════════════════════════════════════════════════════════════════════ */
  .license-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px 24px;
    font-size: 22px;
    margin-top: 8px;
  }
  .license-box {
    background: #292929;
    border-left: 3px solid #E4FF3D;
    padding: 8px 12px;
    border-radius: 4px;
  }
  .license-box strong {
    font-size: 21px;
  }
  .license-box p {
    margin: 2px 0 0 0;
    color: #999;
    font-size: 19px;
  }

  /* ═══════════════════════════════════════════════════════════════════════
     FLOW CHART — Horizontal process steps
     ═══════════════════════════════════════════════════════════════════════ */
  .flow {
    display: flex;
    align-items: stretch;
    justify-content: center;
    gap: 0;
    margin-top: 32px;
    width: 100%;
    position: relative;
  }
  .flow-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1;
    position: relative;
    z-index: 2;
  }
  .flow-num {
    width: 52px;
    height: 52px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 900;
    font-size: 22px;
    color: #1C1C1C;
    background: #E4FF3D;
    border: 3px solid #1C1C1C;
    position: relative;
    z-index: 3;
  }
  .flow-connector {
    position: absolute;
    top: 26px;
    left: 50%;
    right: -50%;
    height: 2px;
    background: #E4FF3D;
    z-index: 1;
  }
  .flow-step:last-child .flow-connector {
    display: none;
  }
  .flow-card {
    margin-top: 14px;
    background: #292929;
    border-radius: 8px;
    padding: 14px 10px;
    width: 90%;
    min-height: 120px;
    text-align: center;
    border-top: 2px solid #E4FF3D;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }
  .flow-label {
    font-size: 17px;
    font-weight: 700;
    color: #FFFFFF;
    line-height: 1.25;
    margin-bottom: 6px;
  }
  .flow-desc {
    font-size: 14px;
    color: #999;
    line-height: 1.35;
  }
  .flow-footer {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    margin-top: 28px;
  }
  .flow-footer-line {
    flex: 1;
    max-width: 200px;
    height: 1px;
    background: linear-gradient(90deg, transparent, #656565);
  }
  .flow-footer-line.right {
    background: linear-gradient(90deg, #656565, transparent);
  }
  .flow-footer-text {
    font-size: 13px;
    font-weight: 700;
    color: #E4FF3D;
    letter-spacing: 2px;
    white-space: nowrap;
  }

  /* ═══════════════════════════════════════════════════════════════════════
     KPI / METRICS
     ═══════════════════════════════════════════════════════════════════════ */
  .kpi-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 20px;
    margin-top: 16px;
  }
  .kpi-grid-4 {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr 1fr;
    gap: 20px;
    margin-top: 16px;
  }
  .kpi-tile {
    background: #292929;
    border-radius: 8px;
    padding: 24px 16px;
    text-align: center;
    border-top: 3px solid #E4FF3D;
  }
  .kpi-number {
    font-size: 48px;
    font-weight: 900;
    color: #E4FF3D;
    line-height: 1;
    margin-bottom: 8px;
  }
  .kpi-label {
    font-size: 16px;
    color: #999;
    font-weight: 400;
  }
  .kpi-sublabel {
    font-size: 13px;
    color: #656565;
    margin-top: 4px;
  }

  /* ═══════════════════════════════════════════════════════════════════════
     QUOTE / TESTIMONIAL
     ═══════════════════════════════════════════════════════════════════════ */
  section.quote-slide {
    justify-content: center;
    padding-top: 60px;
    padding-bottom: 60px;
  }
  .quote-mark {
    font-size: 72px;
    color: #E4FF3D;
    line-height: 1;
    margin-bottom: 0;
    font-weight: 900;
  }
  .quote-text {
    font-size: 28px;
    color: #FFFFFF;
    font-weight: 400;
    font-style: italic;
    line-height: 1.5;
    max-width: 800px;
    margin: 0 auto;
  }
  .quote-author {
    font-size: 18px;
    color: #E4FF3D;
    font-weight: 700;
    margin-top: 24px;
    text-align: center;
  }
  .quote-role {
    font-size: 16px;
    color: #656565;
    text-align: center;
    margin-top: 4px;
  }

  /* ═══════════════════════════════════════════════════════════════════════
     TIMELINE
     ═══════════════════════════════════════════════════════════════════════ */
  .timeline {
    position: relative;
    padding-left: 40px;
    margin-top: 12px;
  }
  .timeline::before {
    content: '';
    position: absolute;
    left: 14px;
    top: 0;
    bottom: 0;
    width: 2px;
    background: #404040;
  }
  .timeline-item {
    position: relative;
    margin-bottom: 20px;
    padding-left: 24px;
  }
  .timeline-item::before {
    content: '';
    position: absolute;
    left: -32px;
    top: 6px;
    width: 14px;
    height: 14px;
    border-radius: 50%;
    background: #E4FF3D;
    border: 3px solid #1C1C1C;
  }
  .timeline-date {
    font-size: 14px;
    font-weight: 700;
    color: #E4FF3D;
    margin-bottom: 2px;
  }
  .timeline-title {
    font-size: 20px;
    font-weight: 700;
    color: #FFFFFF;
    margin-bottom: 2px;
  }
  .timeline-desc {
    font-size: 16px;
    color: #999;
    line-height: 1.4;
  }

  /* ═══════════════════════════════════════════════════════════════════════
     SWOT / QUADRANT
     ═══════════════════════════════════════════════════════════════════════ */
  .quadrant {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: 1fr 1fr;
    gap: 12px;
    margin-top: 12px;
    height: 380px;
  }
  .quadrant-cell {
    background: #292929;
    border-radius: 8px;
    padding: 16px 18px;
    display: flex;
    flex-direction: column;
  }
  .quadrant-cell h4 {
    margin: 0 0 8px 0;
    font-size: 18px;
    font-weight: 900;
  }
  .quadrant-cell.green h4 { color: #4ADE80; }
  .quadrant-cell.yellow h4 { color: #E4FF3D; }
  .quadrant-cell.red h4 { color: #F87171; }
  .quadrant-cell.blue h4 { color: #60A5FA; }
  .quadrant-cell p, .quadrant-cell ul {
    margin: 0;
    font-size: 16px;
    color: #999;
    line-height: 1.4;
  }
  .quadrant-cell ul {
    padding-left: 18px;
  }

  /* ═══════════════════════════════════════════════════════════════════════
     BEFORE / AFTER
     ═══════════════════════════════════════════════════════════════════════ */
  .comparison {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    margin-top: 12px;
  }
  .comparison-before {
    background: #292929;
    border-top: 3px solid #F87171;
    border-radius: 8px;
    padding: 20px;
  }
  .comparison-after {
    background: #292929;
    border-top: 3px solid #4ADE80;
    border-radius: 8px;
    padding: 20px;
  }
  .comparison-before h4, .comparison-after h4 {
    margin: 0 0 12px 0;
    font-size: 20px;
    font-weight: 900;
  }
  .comparison-before h4 { color: #F87171; }
  .comparison-after h4 { color: #4ADE80; }
  .comparison-before p, .comparison-after p,
  .comparison-before ul, .comparison-after ul {
    margin: 0;
    color: #999;
    font-size: 18px;
    line-height: 1.5;
  }
  .comparison-before ul, .comparison-after ul {
    padding-left: 20px;
  }

  /* ═══════════════════════════════════════════════════════════════════════
     TEAM / CONTACT
     ═══════════════════════════════════════════════════════════════════════ */
  .team-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 20px;
    margin-top: 16px;
  }
  .team-member {
    background: #292929;
    border-radius: 8px;
    padding: 24px 16px;
    text-align: center;
  }
  .team-avatar {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    background: #404040;
    margin: 0 auto 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
    color: #E4FF3D;
    font-weight: 900;
  }
  .team-name {
    font-size: 20px;
    font-weight: 700;
    color: #FFFFFF;
    margin-bottom: 4px;
  }
  .team-role {
    font-size: 15px;
    color: #E4FF3D;
    font-weight: 700;
    margin-bottom: 4px;
  }
  .team-info {
    font-size: 14px;
    color: #656565;
  }

  /* ═══════════════════════════════════════════════════════════════════════
     CTA / NEXT STEPS
     ═══════════════════════════════════════════════════════════════════════ */
  .cta-box {
    background: #292929;
    border: 2px solid #E4FF3D;
    border-radius: 12px;
    padding: 32px 40px;
    text-align: center;
    margin-top: 20px;
  }
  .cta-box h2 {
    color: #FFFFFF;
    font-size: 32px;
    margin-bottom: 8px;
  }
  .cta-box p {
    color: #999;
    font-size: 20px;
    margin: 4px 0;
  }
  .cta-action {
    display: inline-block;
    background: #E4FF3D;
    color: #1C1C1C;
    font-weight: 900;
    font-size: 18px;
    padding: 10px 36px;
    border-radius: 6px;
    margin-top: 16px;
    text-decoration: none;
  }

  /* ═══════════════════════════════════════════════════════════════════════
     CLOSING SLIDE
     ═══════════════════════════════════════════════════════════════════════ */
  section.closing-slide {
    justify-content: center;
    padding-top: 0;
    text-align: center;
  }
  section.closing-slide h1 {
    position: static;
    text-align: center;
    width: 100%;
    font-size: 52px;
    margin-bottom: 12px;
  }
  section.closing-slide h3 {
    text-align: center;
    font-weight: 400;
    font-size: 20px;
    margin-top: 8px;
  }
  .closing-contact {
    margin-top: 32px;
    font-size: 18px;
    color: #656565;
  }
  .closing-contact strong {
    color: #E4FF3D;
  }

  /* ═══════════════════════════════════════════════════════════════════════
     SPEAKER / TIME
     ═══════════════════════════════════════════════════════════════════════ */
  .time {
    font-weight: 900;
    color: #E4FF3D;
    font-size: 22px;
  }
  .speaker {
    color: #656565;
    font-size: 22px;
  }

  /* ═══════════════════════════════════════════════════════════════════════
     PRICING HELPERS
     ═══════════════════════════════════════════════════════════════════════ */
  .price {
    font-weight: 900;
    color: #E4FF3D;
    text-align: right;
  }
  .tier {
    color: #CECECE;
    font-weight: 700;
  }
  .users {
    color: #656565;
    font-size: 17px;
  }

  /* ═══════════════════════════════════════════════════════════════════════
     CHECKLIST
     ═══════════════════════════════════════════════════════════════════════ */
  .checklist {
    list-style: none;
    padding-left: 0;
    font-size: 22px;
  }
  .checklist li {
    padding: 6px 0;
    border-bottom: 1px solid #333;
  }
  .checklist li::before {
    content: '✓';
    color: #E4FF3D;
    font-weight: 900;
    margin-right: 12px;
  }

  /* ═══════════════════════════════════════════════════════════════════════
     PROGRESS BARS
     ═══════════════════════════════════════════════════════════════════════ */
  .progress-row {
    display: flex;
    align-items: center;
    margin-bottom: 14px;
    gap: 12px;
  }
  .progress-label {
    min-width: 140px;
    font-size: 18px;
    color: #CECECE;
    font-weight: 700;
    text-align: right;
  }
  .progress-bar {
    flex: 1;
    height: 20px;
    background: #292929;
    border-radius: 10px;
    overflow: hidden;
  }
  .progress-fill {
    height: 100%;
    background: #E4FF3D;
    border-radius: 10px;
  }
  .progress-value {
    min-width: 50px;
    font-size: 18px;
    font-weight: 900;
    color: #E4FF3D;
  }

  /* ═══════════════════════════════════════════════════════════════════════
     ICON LIST
     ═══════════════════════════════════════════════════════════════════════ */
  .icon-list {
    list-style: none;
    padding: 0;
    margin-top: 8px;
  }
  .icon-list li {
    display: flex;
    align-items: flex-start;
    gap: 16px;
    padding: 10px 0;
    border-bottom: 1px solid #333;
    font-size: 22px;
  }
  .icon-list .icon {
    font-size: 28px;
    min-width: 36px;
    text-align: center;
  }
  .icon-list .icon-text strong {
    display: block;
    color: #FFFFFF;
    font-size: 20px;
    margin-bottom: 2px;
  }
  .icon-list .icon-text span {
    color: #999;
    font-size: 17px;
  }

  /* ═══════════════════════════════════════════════════════════════════════
     FUNNEL
     ═══════════════════════════════════════════════════════════════════════ */
  .funnel {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin-top: 20px;
    gap: 6px;
  }
  .funnel-layer {
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: center;
    border-radius: 8px;
    padding: 12px 20px;
    font-weight: 700;
    font-size: 17px;
    color: #FFFFFF;
    background: #292929;
  }
  .funnel-layer:nth-child(1) { width: 95%; border-top: 3px solid #E4FF3D; }
  .funnel-layer:nth-child(2) { width: 80%; border-top: 3px solid #E4FF3D; }
  .funnel-layer:nth-child(3) { width: 65%; border-top: 3px solid #E4FF3D; }
  .funnel-layer:nth-child(4) { width: 50%; border-top: 3px solid #E4FF3D; }
  .funnel-layer:nth-child(5) { width: 35%; border-top: 3px solid #E4FF3D; }
  .funnel-layer span {
    font-weight: 400;
    color: #999;
    font-size: 14px;
    margin-left: 12px;
  }

  /* ═══════════════════════════════════════════════════════════════════════
     LOGO CLOUD
     ═══════════════════════════════════════════════════════════════════════ */
  .logo-cloud {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-top: 16px;
  }
  .logo-item {
    background: #292929;
    border-radius: 8px;
    padding: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 80px;
    font-size: 18px;
    font-weight: 700;
    color: #656565;
  }

  /* ═══════════════════════════════════════════════════════════════════════
     ARCHITECTURE STACK
     ═══════════════════════════════════════════════════════════════════════ */
  .arch-stack {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 12px;
  }
  .arch-layer {
    background: #292929;
    border-radius: 8px;
    padding: 14px 24px;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .arch-layer-name {
    font-size: 18px;
    font-weight: 900;
    color: #FFFFFF;
  }
  .arch-layer-detail {
    font-size: 14px;
    color: #999;
  }
  .arch-layer-badge {
    background: #E4FF3D;
    color: #1C1C1C;
    font-size: 11px;
    font-weight: 900;
    padding: 3px 12px;
    border-radius: 4px;
    text-transform: uppercase;
  }

  /* ═══════════════════════════════════════════════════════════════════════
     GANTT SCHEDULE
     ═══════════════════════════════════════════════════════════════════════ */
  .gantt {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 12px;
  }
  .gantt-row {
    display: grid;
    grid-template-columns: 120px 1fr;
    align-items: center;
    gap: 12px;
  }
  .gantt-label {
    font-size: 14px;
    font-weight: 700;
    color: #CECECE;
    text-align: right;
  }
  .gantt-track {
    height: 24px;
    background: #292929;
    border-radius: 6px;
    position: relative;
    overflow: hidden;
  }
  .gantt-bar {
    position: absolute;
    top: 2px;
    bottom: 2px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 700;
    color: #1C1C1C;
  }
  .gantt-bar.accent { background: #E4FF3D; }
  .gantt-bar.green { background: #4ADE80; }
  .gantt-bar.blue { background: #60A5FA; color: #FFFFFF; }
  .gantt-bar.purple { background: #A78BFA; color: #FFFFFF; }
  .gantt-header {
    display: grid;
    grid-template-columns: 120px 1fr;
    gap: 12px;
    margin-bottom: 4px;
  }
  .gantt-months {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    font-size: 11px;
    font-weight: 700;
    color: #656565;
    text-align: center;
  }

---

<!-- ─── TITLE SLIDE ─── -->

<!-- _class: invert title-slide -->
<!-- _paginate: false -->

## SPLed and spl-core

# Variant documentation without templates

<div class="title-divider"></div>

### useblocks GmbH · Munich, Germany

<div class="title-date">October 2026</div>

<!--
Audience: engineers who know Sphinx and sphinx-needs. Four parts: how upstream does it, why static readers fail, the fix, and what is still open. Everything shown is merged on the useblocks forks: SPLed#4, spl-core#5 and clanguru#1.
-->

---

<!-- _class: invert -->

<span class="badge">Agenda</span>

# Agenda

| # | Part | What it covers |
|:---:|:---|:---|
| **1** | **How upstream builds variant docs** | spl-core, Jinja, one CMake build |
| **2** | **Why ubCode and ubc cannot read it** | static readers, and the one rule they need |
| **3** | **The fix** | a generated selection, declarative gates, spl-core and clanguru changes |
| **4** | **What is still open** | next steps, product ideas, the way upstream |

<div class="note">Everything shown is merged on the forks: <a href="https://github.com/useblocks/SPLed/pull/4">useblocks/SPLed#4</a>, <a href="https://github.com/useblocks/spl-core/pull/5">useblocks/spl-core#5</a> and <a href="https://github.com/useblocks/clanguru/pull/1">useblocks/clanguru#1</a></div>

---

<!-- _class: invert -->

<span class="badge">Summary</span>

# In one slide

- **Today:** every document is a Jinja template, rendered inside a CMake build that alone knows the variant.
- **Problem:** readers that do not run the build, such as ubCode, ubc, an editor or a CI gate, see templates instead of documents.
- **Fix:** selecting a variant generates every file the readers need: the variant data, the rules and the selection. Sphinx and ubc read the same files.
- **Status:** merged on the useblocks forks. Both readers read the same needs, 134 against 132 in Disco's reports, the two untitled imports apart. The [CI documentation gate](https://github.com/useblocks/SPLed/actions/runs/36923824832) is green.

<div class="highlight">

**Key takeaway:** the documentation of a product line should be something a tool can read, not something only a build can produce.

</div>

<!--
If there is time for only one slide, this is it. The rest of the talk backs each line with code and evidence.
-->

---

<!-- _class: invert -->

<span class="badge">Context</span>

# SPLed, a product line in miniature

[SPLed](https://github.com/avengineers/SPLed) has one code base, five [variants](https://github.com/avengineers/SPLed/tree/f5ba89efcabb494ccc66a7619943260444c497de/variants) and two build kits. [spl-core](https://github.com/avengineers/spl-core) turns each variant into firmware, unit tests, coverage and documentation.

| Variant | Features switched on | Components |
|:---|:---|:---:|
| Disco | `BLINKING` | 11 |
| Sleep | `BRIGHTNESS_ADJUSTMENT_MANUAL`, `AUTO_OFF` | 13 |
| Spa | `BRIGHTNESS_ADJUSTMENT_AUTOMATIC` | 12 |
| IDEA/Sloemada | `BRIGHTNESS_ADJUSTMENT_MANUAL`, `AUTO_OFF` | 13 |
| Base/Dev | none, the KConfig defaults | 7 |

<div class="note">Every variant is a value for each of the 21 <a href="https://github.com/avengineers/SPLed/blob/f5ba89efcabb494ccc66a7619943260444c497de/KConfig">KConfig</a> features plus a component list in its <a href="https://github.com/avengineers/SPLed/blob/f5ba89efcabb494ccc66a7619943260444c497de/variants/Disco/parts.cmake">parts.cmake</a>. Component counts are the prod kit; the test kit adds an integration suite to Disco.</div>

---

<!-- _class: invert section-divider -->

<div class="section-number">01</div>

# How upstream builds variant documentation

### [avengineers/SPLed](https://github.com/avengineers/SPLed) and [spl-core 8.9.0](https://github.com/avengineers/spl-core/releases/tag/v8.9.0), as released

---

<!-- _class: invert -->

<span class="badge">Upstream today</span>

# Only a CMake build knows the variant

![w:1160](images/upstream-pipeline.svg)

<div class="note">spl-core's <a href="https://github.com/avengineers/spl-core/blob/95a634771491f7c649566b06e3e1fed3f422d86b/src/spl_core/common.cmake#L650">common.cmake</a> starts sphinx-build with the build context · SPLed's <a href="https://github.com/avengineers/SPLed/blob/f5ba89efcabb494ccc66a7619943260444c497de/conf.py#L64-L81">conf.py</a> renders every page through Jinja</div>

<!--
spl-core's CMake writes a config.json per Sphinx target and the KConfig autoconf.json, then starts sphinx-build with environment variables that point at them. conf.py's source-read hook renders every page through Jinja with that context. A reader that is not this build has no context at all.
-->

---

<!-- _class: invert -->

<span class="badge">Upstream today</span>

# Every document is a template

<div class="columns">
<div>

````django
{% for c in build_config.components_info %}
{% if c.has_docs %}
## {{ c.long_name or c.name }}

```{toctree}
/{{ c.path }}/doc/index
{% if build_config.target == 'reports' %}
/{{ c.reports_output_dir }}/coverage
{% endif %}
```
{% endif %}
{% endfor %}
````

</div>
<div>

````django
```{mermaid}
stateDiagram-v2
    LIGHT_OFF --> LIGHT_ON
    LIGHT_ON --> LIGHT_OFF
{% if config.BLINKING %}
    state LIGHT_ON {
        BlinkON --> BlinkOFF
        BlinkOFF --> BlinkON
    }
{% endif %}
```
````

</div>
</div>

<div class="highlight">

**58 Jinja constructs in 6 of 18 documents.** The components page is a loop over CMake's component list; behaviour differences sit inside diagrams.

</div>

<div class="note">Shortened from <a href="https://github.com/avengineers/SPLed/blob/f5ba89efcabb494ccc66a7619943260444c497de/doc/components/index.md#L3-L20">doc/components/index.md</a> and <a href="https://github.com/avengineers/SPLed/blob/f5ba89efcabb494ccc66a7619943260444c497de/components/light_controller/doc/index.md#L106-L111">components/light_controller/doc/index.md</a></div>

<!--
Names are shortened to fit: component_info is c, and the mermaid transitions lose their labels. index.md adds the variant name and a {{ timestamp }}, which also makes every build unreproducible.
-->

---

<!-- _class: invert -->

<span class="badge">Upstream today</span>

# spl-core ships the Jinja pass

- [The kickstart template's `conf.py`](https://github.com/avengineers/spl-core/blob/95a634771491f7c649566b06e3e1fed3f422d86b/src/spl_core/kickstart/templates/project/conf.py#L71-L84) renders every page through Jinja. spl-core's [architecture notes](https://github.com/avengineers/spl-core/blob/95a634771491f7c649566b06e3e1fed3f422d86b/docs/internals/architecture/report_generation.md#L75-L84) call it "Rendering pages as Jinja templates".
- [`common.cmake`](https://github.com/avengineers/spl-core/blob/95a634771491f7c649566b06e3e1fed3f422d86b/src/spl_core/common.cmake#L650) passes the context as environment variables, and has clanguru wrap generated listings in [`{% raw %}`](https://github.com/avengineers/spl-core/blob/95a634771491f7c649566b06e3e1fed3f422d86b/src/spl_core/common.cmake#L895-L900) so that C braces survive the pass.
- A new project starts with 32 Jinja constructs, for example on its [components page](https://github.com/avengineers/spl-core/blob/95a634771491f7c649566b06e3e1fed3f422d86b/src/spl_core/kickstart/templates/project/doc/components/index.md).

```python
def rstjinja(app, docname, source):
    source[0] = app.builder.templates.render_string(source[0], app.config.html_context)

def setup(app):
    app.connect("source-read", rstjinja)
```

<div class="note">Shortened from the <a href="https://github.com/avengineers/spl-core/blob/95a634771491f7c649566b06e3e1fed3f422d86b/src/spl_core/kickstart/templates/project/conf.py#L71-L84">kickstart template's conf.py</a>; <a href="https://github.com/avengineers/SPLed/blob/f5ba89efcabb494ccc66a7619943260444c497de/conf.py#L64-L81">SPLed's conf.py</a> has the same pass</div>

<!--
This is not a SPLed quirk. It is how every spl-core project is set up, which is why the fix has to start in spl-core.
-->

---

<!-- _class: invert section-divider -->

<div class="section-number">02</div>

# Why ubCode and ubc cannot read it

### Static readers, and the one rule they need

---

<!-- _class: invert -->

<span class="badge">The rule</span>

# ubCode and ubc read, never run

- They parse the documents and `ubproject.toml` directly: no CMake, no `conf.py`, no project Python.
- That makes them fast and safe: an IDE that updates as you type, a CI gate without a compiler, results that can be cached.
- It also makes them honest: what they report is what the sources say, not what one build happened to produce.

<div class="highlight">

**The rule:** whatever decides what a document contains must be data that every reader can see.

</div>

<div class="note"><a href="https://ubcode.useblocks.com/">ubCode</a> · <a href="https://github.com/useblocks/ubc-action">ubc in GitHub Actions</a></div>

<!--
Sphinx is a program that executes conf.py. ubCode and ubc are readers. Both have to arrive at the same document set, and they can only do that from the same data.
-->

---

<!-- _class: invert -->

<span class="badge">Why it fails</span>

# A template is text to a reader

- To a static reader, `{% if config.BLINKING %}` is a paragraph. Both branches are parsed.
- Needs inside an inactive branch enter the index, so traceability shows requirements the variant does not have.
- The rendered page and the file differ, so line numbers in warnings and need positions drift.
- Every brace in prose, code or diagrams is a hazard. Hence the `{% raw %}` armour on generated listings.

<!--
The Jinja pass also defeats Sphinx's own caching: every page is rewritten on every read, so nothing can be skipped.
-->

---

<!-- _class: invert -->

<span class="badge">Why it fails</span>

# The variant lives in the build

- The context arrives through environment variables that spl-core sets when it starts `sphinx-build`.
- A bare `sphinx-build` renders the components page empty, without a warning, and stops at the first stray brace.
- Upstream CI checks documentation only inside full variant builds. No job builds the documents without a compiler.
- An editor cannot show another variant without configuring and building it.

<div class="note">Upstream <a href="https://github.com/avengineers/SPLed/blob/f5ba89efcabb494ccc66a7619943260444c497de/.github/workflows/ci.yml">ci.yml</a>: gate selection, then Windows, Linux and devcontainer jobs that all run the build scripts</div>

---

<!-- _class: invert -->

<span class="badge">Why it fails</span>

# Generated pages have no stable name

```text
build/Disco/test/Debug/components/light_controller/reports/coverage.rst
build/Disco/test/Debug/reports/html/build/Disco/test/Debug/components/…/coverage/index.html
```

- Document names contain the variant, the kit and the build type, so a toctree can only reach the pages through a loop or a `/build/**` glob.
- gcovr writes each coverage report at the page's build-relative path. Move the page and its coverage link breaks.
- A reader that indexes `build/` sees every variant and kit ever built: the same need IDs, many times over.

<div class="note">spl-core writes the <a href="https://github.com/avengineers/spl-core/blob/95a634771491f7c649566b06e3e1fed3f422d86b/src/spl_core/common.cmake#L384">coverage link</a> relative to the page, and the <a href="https://github.com/avengineers/spl-core/blob/95a634771491f7c649566b06e3e1fed3f422d86b/src/spl_core/common.cmake#L624">gcovr tree</a> at the build-relative path</div>

---

<!-- _class: invert -->

<span class="badge">Why it fails</span>

# Two readers, two configurations

- The needs model is split between a [TOML file](https://github.com/avengineers/spl-core/blob/95a634771491f7c649566b06e3e1fed3f422d86b/src/spl_core/report_generation/ubproject.toml) inside the installed spl-core package and [`conf.py`](https://github.com/avengineers/SPLed/blob/f5ba89efcabb494ccc66a7619943260444c497de/conf.py#L56-L61).
- The `results` links come from [`sple_tr_link`](https://github.com/avengineers/spl-core/blob/95a634771491f7c649566b06e3e1fed3f422d86b/src/spl_core/report_generation/spl_sphinx.py#L69-L74), project Python that no static reader can execute.
- Upstream ships no `ubproject.toml`. [The fork's first one](https://github.com/useblocks/SPLed/blob/447b9e11621a44717ce5fca6339bc393f7e1b6ae/ubproject.toml#L3) extended a file inside the virtualenv, specific to one Python version and one OS.
- sphinx-needs does not implement ubCode's `extend`, so the two readers could not even share that file.

---

<!-- _class: invert section-divider -->

<div class="section-number">03</div>

# The fix: generate data, never content

### [SPLed#4](https://github.com/useblocks/SPLed/pull/4), with [spl-core#5](https://github.com/useblocks/spl-core/pull/5) and [clanguru#1](https://github.com/useblocks/clanguru/pull/1), merged on the forks

---

<!-- _class: invert -->

<span class="badge">The fix</span>

# Four rules

1. **One selection step** writes complete, self-describing data for every variant, kit and target, and the rules that gate the documents.
2. **Content stays 150 %** in the tree. Declarative gates decide what a variant contains.
3. **Every reader reads the same files:** the selection, its variant cell, `ubproject.toml` with its generated rules, and the documents.
4. **A variant is selected, not rendered:** CMake configure, or `tools/variant_data.py`, writes the selection; nothing is decided on a command line or in `conf.py`.

<div class="highlight">

Nothing that decides content lives in `conf.py`, CMake or a template, and nothing per component is written by hand.

</div>

---

<!-- _class: invert -->

<span class="badge">The fix</span>

# Both readers take the same inputs

![w:1160](images/declarative-pipeline.svg)

<div class="note"><a href="https://github.com/useblocks/SPLed/blob/e79a759/tools/variant_data.py">tools/variant_data.py</a> writes the cells, the rules and the selection · <a href="https://github.com/useblocks/SPLed/blob/e79a759/ubproject.toml">ubproject.toml</a> holds the model and extends the rules · <a href="https://github.com/useblocks/SPLed/blob/e79a759/conf.py">conf.py</a> hands the selection to Sphinx</div>

<!--
Left: the selection step. Middle: the three inputs, all plain files. Right: the two readers. ubCode reaches the selection through extend; conf.py hands the same keys to Sphinx, whose extensions read one TOML file each. The CI gate checks that both arrive at the same needs.
-->

---

<!-- _class: invert -->

<span class="badge">The fix</span>

# One cell per variant, kit and target

<div class="columns">
<div>

```json
{
  "build_config": {
    "variant": "Sleep",
    "kit": "test",
    "target": "reports",
    "scope": "variant",
    "component": "",
    "components": ["components/rte", "…",
      "components/brightness_controller",
      "components/auto_off"]
  },
  "features": {
    "AUTO_OFF": true,
    "BLINKING": false,
    "BRIGHTNESS_ADJUSTMENT_ENABLED": true,
    "CUSTOMER": "B"
  }
}
```

</div>
<div>

- [`tools/variant_data.py`](https://github.com/useblocks/SPLed/blob/e79a759/tools/variant_data.py) writes all 114 cells in one run, without a compiler: 20 variant cells (5 variants, 2 kits, 2 targets) and 94 for per-component reports.
- Every declared boolean is present, including promptless ones that KConfig leaves out when they are off.
- The component list comes from `parts.cmake`, where the product structure already lives.
- `build/selection.toml` names the cell the IDE and a plain build read.

</div>
</div>

<!--
The features object is shortened: a cell has 21 features. scope and component make a per-component report a cell of its own. The selection is rewritten whenever CMake configures, or by a VS Code task, so the IDE follows the variant a developer is working on.
-->

---

<!-- _class: invert -->

<span class="badge">The fix</span>

# Two gates, one data source

```toml
# ubproject.variants.toml, generated: whole documents, gated on a component
[[source.variant_sources]]
if = "'components/auto_off' in var.build_config.components and (var.build_config.scope == 'variant' or var.build_config.component == 'components/auto_off')"
files = ["components/auto_off/**"]
```

<div class="columns">
<div>

`````text
% any document: blocks, gated on a feature
````{if} var.features.BLINKING
```{mermaid}
stateDiagram-v2
    state LIGHT_ON {
        BlinkON --> BlinkOFF
    }
```
````
`````

</div>
<div>

<div class="highlight">

**Membership, never identity:** gate on the component list, never on the variant name.

</div>

<div class="success">

12 generated rules and 28 `{if}` fences in 11 documents replace 58 Jinja constructs. The components page is a glob over every component.

</div>

</div>
</div>

<div class="note">The generator derives one rule per component from where its documentation lives · <a href="https://github.com/useblocks/SPLed/blob/e79a759/components/light_controller/doc/index.md">the light controller diagram</a> · <a href="https://sphinx-needs.readthedocs.io/en/latest/directives/if.html">the {if} directive</a> · <a href="https://github.com/useblocks/sphinx-mounts">sphinx-mounts</a> applies the rules for Sphinx</div>

<!--
Rules remove whole documents, for Sphinx through sphinx-mounts and for ubCode natively. Excluded toctree entries are reported as info by both tools. Content behind a false {if} is never parsed, so its needs never enter the traceability data. Adding a component means adding it to parts.cmake and writing its documentation: the next selection writes its rule.
-->

---

<!-- _class: invert -->

<span class="badge">The rule</span>

# No variants in toctrees

<div class="comparison">
<div class="comparison-before">

### A condition on a toctree entry

- `a if variant == 'a'` removes the entry, not the document
- the document is still read, and its needs still count
- no condition true: an orphan warning
- two conditions true: two parents, and no warning
- removing the document too needs a second pass or a toctree override

</div>
<div class="comparison-after">

### A rule on the document

- a false rule keeps the file out of discovery
- never read: no needs, no orphan
- the toctree stays static and lists all, 150 %
- an entry to a removed document is INFO, in Sphinx and ubCode
- Sphinx sees only `exclude_patterns` and a log filter

</div>
</div>

<div class="highlight">

**Discovery is the guest list, the toctree is the seating plan.** Sphinx fixes the guest list before it reads the first toctree.

</div>

<div class="note">Sphinx 8.2.3: <a href="https://github.com/sphinx-doc/sphinx/blob/v8.2.3/sphinx/project.py#L49-L62">discovery</a> · <a href="https://github.com/sphinx-doc/sphinx/blob/v8.2.3/sphinx/directives/other.py#L151-L161">entries to excluded documents</a> · <a href="https://github.com/sphinx-doc/sphinx/blob/v8.2.3/sphinx/environment/__init__.py#L799-L817">orphans</a> · <a href="https://github.com/sphinx-doc/sphinx/blob/v8.2.3/sphinx/environment/__init__.py#L879-L898">two parents</a> · sphinx-mounts 0.2.0: <a href="https://github.com/useblocks/sphinx-mounts/blob/0.2.0/src/sphinx_mounts/extension.py#L1001-L1003">rules become exclude_patterns</a>, <a href="https://github.com/useblocks/sphinx-mounts/blob/0.2.0/src/sphinx_mounts/warnings.py#L25-L29">entries become INFO</a></div>

<!--
The question came up as a feature request: conditions on toctree entries. Sphinx's order of work answers it. Discovery collects every file with a source suffix, minus exclude_patterns, before a single document is opened. Every discovered document is read, and sphinx-needs collects its needs while reading. A toctree only records that A lists B and C. So a condition on an entry moves the navigation, never the content: the document is still read, still contributes needs, and without a parent it is an orphan warning. With two true conditions it has two parents, which Sphinx reports only as INFO.
The one real case is a document in every variant whose place changes. Two thin pages at fixed places, one behind a rule and one behind its negation, both include the shared content from a folder outside discovery. The negation guarantees exactly one page per variant; two independent conditions could both be false and drop the content without a warning.
-->

---

<!-- _class: invert -->

<span class="badge">Proof</span>

# No toctree variants left in SPLed

- **Components:** [one glob toctree](https://github.com/useblocks/SPLed/blob/e79a759/doc/components/index.md) lists them all, and the generated rules decide which exist.
- **Reports:** `{if}` blocks on the build shape, `target == "reports"`. Each hides a whole report section in a docs build, not single entries.
- **The entries no longer vary.** Upstream computes them per entry; the fork globs the one build the selection reads:

```text
/{{ component_info.reports_output_dir }}/unit_test_results    upstream: Jinja, per entry
/build/**/components/light_controller/reports/unit_test_results   fork: one page, in every variant
```

<div class="highlight">

**Still required? No.** No document in SPLed changes its place by variant. If one ever does: two thin pages at fixed places, behind a rule and its negation, that include the same content.

</div>

<div class="note">Upstream <a href="https://github.com/avengineers/SPLed/blob/f5ba89efcabb494ccc66a7619943260444c497de/doc/components/index.md#L12-L16">components page</a> · fork <a href="https://github.com/useblocks/SPLed/blob/e79a759/components/light_controller/doc/index.md">report section</a></div>

<!--
The glob resolves to exactly one page because each reader reads one build's pages: the selection names them as the rst parser's include. The pages keep the names spl-core gives them, so the coverage links next to them work unchanged. The variant's own coverage page needs one pattern per depth, because a two-segment variant name such as Base/Dev puts it one level deeper.
-->

---

<!-- _class: invert -->

<span class="badge">The fix</span>

# One file selects the variant

```toml
# build/selection.toml, written by CMake configure or tools/variant_data.py
[needs]
variant_data_file = ".../build/variants/Disco/test/reports.json"

[parse.parsers.rst]   # this build's generated pages, where spl-core writes them
include = ["build/Disco/test/Debug/components/**/*.rst", "…/test/**/*.rst", "…/reports/*.rst"]
```

- ubCode reaches it through `extend`; `conf.py` hands the same keys to Sphinx. Nothing is selected on a command line.
- Every build keeps one such file per documentation run: `sphinx-build -D spl_selection=<file>`, `ubc check -c "$(cat <file>)"`.
- No link, no copy, no mount: two builds' reports run side by side.

<div class="note"><a href="https://github.com/useblocks/SPLed/blob/e79a759/tools/variant_data.py">the generator</a> · <a href="https://github.com/useblocks/SPLed/blob/e79a759/conf.py">conf.py</a> · <a href="https://github.com/useblocks/spl-core/blob/ce62088/docs/reference/variables.md">SPL_SPHINX_OPTIONS</a> names each run's file</div>

<!--
The first design selected the variant with one key on the command line and reached the generated pages through a link called generated. The link was a cross-platform problem, blocked parallel builds, and ubCode never followed it. Reading the pages in place, named by the selection, removed all three.
-->

---

<!-- _class: invert -->

<span class="badge">The fix</span>

# Changes in spl-core and clanguru

| New in spl-core | Default | What a project can do |
|:---|:---|:---|
| `KConfig.declared_boolean_symbols()` | a function | list every declared boolean |
| `SPL_SOURCE_DOCS_JINJA_RAW_TAGS` | `ON` | listings without `{% raw %}` |
| `SPL_VARIANT_DATA_FILE_DOCS`, `_REPORTS` | empty | give each Sphinx build its cell |
| `SPL_SPHINX_SOURCE_DIR` | project root | Sphinx on a folder of its own |
| `SPL_SPHINX_OPTIONS`, `_COMPONENT_OPTIONS` | empty | each run its own selection file |
| `SPL_TEST_RESULTS_AS_NEEDS` | `OFF` | test results as needs.json |

- **clanguru:** a listing shows only its file's own declarations, parsed with every preprocessor option. Before, Spa's report listed a manual-brightness test instead of the automatic ones Spa runs.

<div class="note"><a href="https://github.com/useblocks/spl-core/pull/5">useblocks/spl-core#5</a> · <a href="https://github.com/useblocks/clanguru/pull/1">useblocks/clanguru#1</a>, proposed upstream as <a href="https://github.com/cuinixam/clanguru/pull/9">cuinixam/clanguru#9</a> · <a href="https://github.com/useblocks/spl-core/blob/ce62088/docs/reference/variables.md">variables reference</a></div>

---

<!-- _class: invert -->

<span class="badge">The fix</span>

# What SPLed no longer needs

<div class="comparison">
<div class="comparison-before">

### Upstream

- 58 Jinja constructs in 6 documents
- a `source-read` handler that renders every page
- report entries built from Jinja paths
- test results through a Sphinx-only directive and a Python link function
- no documentation check without a full variant build
- no variant data a static reader can use

</div>
<div class="comparison-after">

### Now

- no Jinja in any document
- no `source-read` handler; [`conf.py`](https://github.com/useblocks/SPLed/blob/e79a759/conf.py) hands the selection on
- report entries as globs over the one selected build
- test results as needs.json, imported by both readers
- every variant and kit checked by both readers on every PR
- 114 variant cells, generated rules and a selection

</div>
</div>

<div class="note"><a href="https://github.com/useblocks/SPLed/pull/4">useblocks/SPLed#4</a>, which carries the earlier SPLed#2 and #3</div>

---

<!-- _class: invert -->

<span class="badge">Proof</span>

# Both readers agree, need for need

- **The gate:** every variant and kit, every per-component report, and the test kit's reports, built by `sphinx-build -W` and by ubc; their needs.json compared on IDs, types, titles, fields and links.
- **Allowed differences** are listed with their reason: `REQ_37` and `REQ_58`, untitled in the ubConnect export, and `remote-url`, which the readers store differently.
- **End to end:** Disco's reports have working coverage links and every relative link resolves: 7,848 of 7,848.

<div class="kpi-grid-4">
<div class="kpi-tile"><div class="kpi-number">134 / 132</div><div class="kpi-label">needs, Sphinx / ubc</div><div class="kpi-sublabel">Disco reports, 0 field differences</div></div>
<div class="kpi-tile"><div class="kpi-number">25 / 25</div><div class="kpi-label">one component's report</div><div class="kpi-sublabel">light_controller</div></div>
<div class="kpi-tile"><div class="kpi-number">95</div><div class="kpi-label"><a href="https://github.com/useblocks/SPLed/actions/runs/36923824832">CI documentation gate</a></div><div class="kpi-sublabel">passed</div></div>
<div class="kpi-tile"><div class="kpi-number">3 / 4</div><div class="kpi-label">CI jobs green</div><div class="kpi-sublabel">Windows fails installing the toolchain, as on upstream develop</div></div>
</div>

---

<!-- _class: invert -->

<span class="badge">Lesson learned</span>

# A trap only a second reader would find

- [Upstream's lock refresh](https://github.com/avengineers/SPLed/commit/f5ba89efcabb494ccc66a7619943260444c497de) moved sphinx-needs from 8.2 to 8.5.
- 8.5 resolves the variant data right after it loads `ubproject.toml`, before the handler in `conf.py` ran.
- Every reports build read the docs cell and silently lost its report sections, or failed on a fresh checkout.
- The documentation gate caught it when [upstream was merged](https://github.com/useblocks/SPLed/commit/f4f98a57913d15fa45fe39c073c9bdbad1c03a2f). Today the selection is a generated file that `conf.py` hands on before sphinx-needs loads its TOML.

<div class="warn">

A selection that lives in one reader's code breaks without a sound. A selection that is data, or a standard override, cannot.

</div>

---

<!-- _class: invert -->

<span class="badge">Lesson learned</span>

# What the second reader found

- **Generated pages missing in ubCode:** ubc read 92 of Sphinx's 134 needs while the pages came in through a mount inside the project. All 42 missing ones were on the verification side. Reading the pages in place closed it.
- **Wrong code in the listings:** clanguru dropped `-isystem`, so every listing showed the `#ifdef` branch of "no feature defined". Spa's report listed `TS_BC-001` instead of `TS_BC-002`/`003`.
- **A link rule only Sphinx knew:** sphinx-codelinks adds it in Python, so ubCode showed the source URL as plain text.

<div class="warn">

Each one looked fine in one reader. The comparison need by need is what made them visible.

</div>

---

<!-- _class: invert section-divider -->

<div class="section-number">04</div>

# What can still be improved

### In the repositories, in ubCode and ubc, and on the way upstream

---

<!-- _class: invert -->

<span class="badge">Still open</span>

# Next in SPLed and spl-core

- **Comparing variants without reconfiguring:** codelinks reads one compile database, the selected build's. One per build, named by each selection, makes a comparison two ubc runs. To discuss: switch off `-save-temps` in spl-core, or let codelinks keep only the preprocessor options.
- **Windows CI:** the toolchain install fails, on the fork and on upstream `develop` alike.
- **A folder for the documents:** move them into `docs/`. The [spl-core setting](https://github.com/useblocks/spl-core/commit/998c97d59a41058ef937ef12c191d19216a72c2c) is ready.
- **The kickstart template:** start new spl-core projects without [the Jinja pass](https://github.com/avengineers/spl-core/blob/95a634771491f7c649566b06e3e1fed3f422d86b/src/spl_core/kickstart/templates/project/conf.py#L71-L84).
- **Upstream data:** titles for `REQ_37` and `REQ_58` in the ubConnect export.

---

<!-- _class: invert -->

<span class="badge">Still open</span>

# What would help in ubCode, ubc and codelinks

- **Consistent overrides:** `-c` replaces the whole rule array but appends to `extend_exclude`.
- **Globs and includes:** an include without a slash matches at any depth while `/index.md` matches nothing; an empty toctree glob warns, which forces one `{if}` per depth.
- **One value for both readers:** sphinx-codelinks stores the path in `remote-url`, ubCode the URL; in a git worktree Sphinx's link has no commit.
- **Compile commands:** keep only the preprocessor options, as clanguru now does, so `-save-temps` stops costing a file its needs.
- **Parity as a feature:** a ubc check that compares its needs with a Sphinx build, like SPLed's gate.

---

<!-- _class: invert -->

<span class="badge">Still open</span>

# Getting it upstream

1. **clanguru:** [cuinixam/clanguru#9](https://github.com/cuinixam/clanguru/pull/9) is open with the two fixes. Release.
2. **spl-core:** propose the changes to [avengineers/spl-core](https://github.com/avengineers/spl-core) from a clean branch. Release.
3. **SPLed:** propose to [avengineers/SPLed](https://github.com/avengineers/SPLed) with both pins moved to PyPI releases, after deciding whether the fork's own 21 commits (customer content, CSV import, codelinks) go along.

<div class="highlight">

Until then, SPLed pins merge commits on the forks' default branches, so every machine and every CI job builds the same code.

</div>

---

<!-- ─── CLOSING SLIDE ─── -->

<!-- _class: invert closing-slide -->
<!-- _paginate: false -->

# One source, two readers, one answer

<div class="title-divider"></div>

### Questions? Let's talk.

<div class="closing-contact">
<strong>SPLed</strong> · <a href="https://github.com/useblocks/SPLed/pull/4">useblocks/SPLed#4</a><br>
<strong>spl-core</strong> · <a href="https://github.com/useblocks/spl-core/pull/5">useblocks/spl-core#5</a> · <strong>clanguru</strong> · <a href="https://github.com/useblocks/clanguru/pull/1">useblocks/clanguru#1</a><br>
<strong>CI</strong> · <a href="https://github.com/useblocks/SPLed/actions/runs/36923824832">the documentation gate, green</a>
</div>

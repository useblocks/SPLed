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

<div class="title-date">September 2026</div>

<!--
Audience: engineers who know Sphinx and sphinx-needs. Four parts: how upstream does it, why static readers fail, the fix, and what is still open. Everything shown is on the useblocks forks: spl-core#4, SPLed#2 and SPLed#3.
-->

---

<!-- _class: invert -->

<span class="badge">Agenda</span>

# Agenda

| # | Part | What it covers |
|:---:|:---|:---|
| **1** | **How upstream builds variant docs** | spl-core, Jinja, one CMake build |
| **2** | **Why ubCode and ubc cannot read it** | static readers, and the one rule they need |
| **3** | **The fix** | variant data, declarative gates, five spl-core changes |
| **4** | **What is still open** | next steps, product ideas, the way upstream |

<div class="note">Everything shown is on <a href="https://github.com/useblocks/spl-core/pull/4">useblocks/spl-core#4</a>, <a href="https://github.com/useblocks/SPLed/pull/2">useblocks/SPLed#2</a> and <a href="https://github.com/useblocks/SPLed/pull/3">useblocks/SPLed#3</a></div>

---

<!-- _class: invert -->

<span class="badge">Summary</span>

# In one slide

- **Today:** every document is a Jinja template, rendered inside a CMake build that alone knows the variant.
- **Problem:** readers that do not run the build, such as ubCode, ubc, an editor or a CI gate without a compiler, see templates instead of documents.
- **Fix:** generate variant data, never content. Sphinx and ubc read the same inputs and select a variant the same way.
- **Status:** five small spl-core changes, SPLed adapted, [CI green](https://github.com/useblocks/SPLed/actions/runs/35985268428) on Windows, Linux and the devcontainer.

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

### [SPLed#2](https://github.com/useblocks/SPLed/pull/2) on the fork, five changes in [spl-core#4](https://github.com/useblocks/spl-core/pull/4), and [SPLed#3](https://github.com/useblocks/SPLed/pull/3) that uses them

---

<!-- _class: invert -->

<span class="badge">The fix</span>

# Four rules

1. **One generation step** writes complete, self-describing data for every variant, kit and target.
2. **Content stays 150 %** in the tree. Declarative gates decide what a variant contains.
3. **Every reader reads the same inputs:** a variant cell, `ubproject.toml` and the documents.
4. **A variant is selected, not rendered:** one key, `variant_data_file`, picks the cell for Sphinx, ubc and the IDE.

<div class="highlight">

Nothing that decides content lives in `conf.py`, CMake or a template.

</div>

---

<!-- _class: invert -->

<span class="badge">The fix</span>

# Both readers take the same inputs

![w:1160](images/declarative-pipeline.svg)

<div class="note"><a href="https://github.com/useblocks/SPLed/blob/362333b7faa50f54e2233efdca7eccf18613057b/tools/variant_data.py">tools/variant_data.py</a> writes the cells · <a href="https://github.com/useblocks/SPLed/blob/362333b7faa50f54e2233efdca7eccf18613057b/ubproject.toml">ubproject.toml</a> holds the model and the rules · <a href="https://github.com/useblocks/SPLed/blob/362333b7faa50f54e2233efdca7eccf18613057b/conf.py">conf.py</a> keeps extensions and theme</div>

<!--
Left: the generator. Middle: the three inputs, all plain files. Right: the two readers, which select a cell with the same key. The CI parity test checks that they arrive at the same document set.
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

- [`tools/variant_data.py`](https://github.com/useblocks/SPLed/blob/362333b7faa50f54e2233efdca7eccf18613057b/tools/variant_data.py) writes all 20 cells in one run, without a compiler: 5 variants, 2 kits, 2 targets.
- Every declared boolean is present, including promptless ones that KConfig leaves out when they are off.
- The component list comes from `parts.cmake`, where the product structure already lives.
- `build/autoconf.json` points at the cell the IDE shows.

</div>
</div>

<!--
The features object is shortened: a cell has 21 features. The pointer is rewritten whenever CMake configures, or by a VS Code task, so the IDE follows the variant a developer is working on.
-->

---

<!-- _class: invert -->

<span class="badge">The fix</span>

# Two gates, one data source

```toml
# ubproject.toml: whole documents, gated on a component
[[source.variant_sources]]
if = "'components/auto_off' in var.build_config.components"
files = ["components/auto_off/doc/**", "generated/components/auto_off/reports/**"]
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

10 rules and 22 `{if}` fences replace 58 Jinja constructs. The components page becomes a static 150 % toctree.

</div>

</div>
</div>

<div class="note">Shortened from the <a href="https://github.com/useblocks/SPLed/blob/362333b7faa50f54e2233efdca7eccf18613057b/ubproject.toml#L310-L316">auto_off rule</a> and the <a href="https://github.com/useblocks/SPLed/blob/362333b7faa50f54e2233efdca7eccf18613057b/components/light_controller/doc/index.md#L92-L103">light controller diagram</a> · <a href="https://sphinx-needs.readthedocs.io/en/latest/directives/if.html">the {if} directive</a> · <a href="https://github.com/useblocks/sphinx-mounts">sphinx-mounts</a> applies the rules for Sphinx</div>

<!--
Rules remove whole documents, for Sphinx through sphinx-mounts and for ubCode natively. Excluded toctree entries are reported as info by both tools. Content behind a false {if} is never parsed, so its needs never enter the traceability data.
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

- **Components:** [one static 150 % toctree](https://github.com/useblocks/SPLed/blob/362333b7faa50f54e2233efdca7eccf18613057b/doc/components/index.md) lists them all, and [10 rules](https://github.com/useblocks/SPLed/blob/362333b7faa50f54e2233efdca7eccf18613057b/ubproject.toml#L253-L340) decide which exist.
- **Reports:** 8 `{if}` blocks on the build shape, `target == "reports"`. Each hides a whole report section in a docs build, not single entries.
- **The entries no longer vary.** Upstream decides them per entry, SPLed#2 globs them, SPLed#3 names them:

```text
/{{ component_info.reports_output_dir }}/unit_test_results        upstream: Jinja, per entry
/build/**/components/light_controller/reports/unit_test_results   SPLed#2: a glob that conf.py narrows
/generated/components/light_controller/reports/unit_test_results  SPLed#3: one name, every variant
```

<div class="highlight">

**Still required? No.** No document in SPLed changes its place by variant. If one ever does: two thin pages at fixed places, behind a rule and its negation, that include the same content.

</div>

<div class="note">Upstream <a href="https://github.com/avengineers/SPLed/blob/f5ba89efcabb494ccc66a7619943260444c497de/doc/components/index.md#L12-L16">components page</a> · SPLed#2 <a href="https://github.com/useblocks/SPLed/blob/bd851d1ba73daac4ea923aabd61512456238cab4/components/light_controller/doc/index.md#L115-L127">glob</a> and <a href="https://github.com/useblocks/SPLed/blob/bd851d1ba73daac4ea923aabd61512456238cab4/conf.py#L166-L189">narrowing in conf.py</a> · SPLed#3 <a href="https://github.com/useblocks/SPLed/blob/362333b7faa50f54e2233efdca7eccf18613057b/components/light_controller/doc/index.md#L114-L126">fixed names</a></div>

<!--
Before spl-core#4, the report entries were the one place where a toctree still changed with the variant: SPLed#2 had to glob /build/** and let conf.py narrow discovery to the configured build, so that each glob matched a single page. SPL_SPHINX_BINARY_DIR gives every generated page a stable name under generated/, so the entries are plain names and conf.py only prunes build/ from the walk.
The remaining {if} blocks gate on the build shape, which is in the variant data, so ubCode and Sphinx evaluate them identically. In the IDE the pointer always holds the docs cell, so they are a clean false there.
-->

---

<!-- _class: invert -->

<span class="badge">The fix</span>

# One key selects the variant

```bash
# Sphinx
sphinx-build -b html -D needs_variant_data_file=build/variants/Sleep/test/docs.json . out

# ubc
ubc check -c "needs.variant_data_file = 'build/variants/Sleep/test/docs.json'"

# IDE: the pointer build/autoconf.json, written by CMake or tools/variant_data.py
```

- spl-core passes `-D needs_variant_data_file=` to every docs and reports build, from [two settings in `CMakeLists.txt`](https://github.com/useblocks/SPLed/blob/362333b7faa50f54e2233efdca7eccf18613057b/CMakeLists.txt#L93-L103).
- `conf.py` selects nothing. It lists extensions and the theme.
- A command-line override survives `ubproject.toml`; a value set in `conf.py` would be replaced by it.

<div class="note"><a href="https://sphinx-needs.readthedocs.io/en/latest/configuration.html">sphinx-needs configuration</a> · <a href="https://github.com/useblocks/spl-core/commit/b3ff837a10d872d95ad4c9ad795641284c702f0d">the spl-core commit that passes the override</a></div>

---

<!-- _class: invert -->

<span class="badge">The fix</span>

# Five small changes in spl-core

| New in spl-core | Default | What a project can do |
|:---|:---|:---|
| [`KConfig.declared_boolean_symbols()`](https://github.com/useblocks/spl-core/commit/762406d87d1052c5d987a7dff0bc31cf7fe4f69b) | a function | list every boolean the model declares |
| [`SPL_SOURCE_DOCS_JINJA_RAW_TAGS`](https://github.com/useblocks/spl-core/commit/1b5ee76ec3f65fb9523850b825638e6cc9ba4af9) | `ON` | build listings without `{% raw %}` |
| [`SPL_VARIANT_DATA_FILE_DOCS`, `_REPORTS`](https://github.com/useblocks/spl-core/commit/b3ff837a10d872d95ad4c9ad795641284c702f0d) | empty | give each Sphinx build its cell |
| [`SPL_SPHINX_SOURCE_DIR`](https://github.com/useblocks/spl-core/commit/998c97d59a41058ef937ef12c191d19216a72c2c) | project root | run Sphinx on a folder of its own |
| [`SPL_SPHINX_BINARY_DIR`](https://github.com/useblocks/spl-core/commit/010727d08b27ca73994772444d25d7bc6e028c31) | build dir | give generated pages stable names |

- 8 files, 543 lines added, 21 removed. A project that sets none of the new settings builds exactly as before.
- A stable name moves everything with it: include patterns, the coverage report next to its page, and `SplBuild`'s artifact lookup.
- A build stops with a clear message if the stable link leads to another build directory.

<div class="note">All five on <a href="https://github.com/useblocks/spl-core/pull/4">useblocks/spl-core#4</a>, documented in the <a href="https://github.com/useblocks/spl-core/blob/010727d08b27ca73994772444d25d7bc6e028c31/docs/reference/variables.md">variables reference</a></div>

<!--
Each commit has its own tests: 256 unit tests pass, and every new CMake test case also fails when its expectation is flipped.
-->

---

<!-- _class: invert -->

<span class="badge">The fix</span>

# What SPLed no longer needs

<div class="comparison">
<div class="comparison-before">

### Upstream

- 58 Jinja constructs in 6 documents
- a `source-read` handler that renders every page
- two functions in `conf.py`
- report entries built from Jinja paths
- no documentation check without a compiler
- no variant data a static reader can use

</div>
<div class="comparison-after">

### Now

- no Jinja in any document
- no handler and no function in [`conf.py`](https://github.com/useblocks/SPLed/blob/362333b7faa50f54e2233efdca7eccf18613057b/conf.py)
- fixed `generated/…` report names
- all five variants checked on every PR
- 20 variant cells and a pointer

</div>
</div>

<div class="note"><a href="https://github.com/useblocks/SPLed/pull/2">SPLed#2</a> removed the Jinja pass and introduced the variant data · <a href="https://github.com/useblocks/SPLed/pull/3">SPLed#3</a> removed the workarounds #2 still needed</div>

<!--
PR #2 still needed a marker strip in conf.py, fixed-name copies of the variant data and globs into build. PR #3 removes those, because spl-core now provides the settings. conf.py keeps 51 lines of code.
-->

---

<!-- _class: invert -->

<span class="badge">Proof</span>

# Both readers agree, on every platform

- **Parity test:** for each variant, [ubc must exclude exactly the documents](https://github.com/useblocks/SPLed/blob/362333b7faa50f54e2233efdca7eccf18613057b/test/test_documentation.py#L295) the component list omits, and [Sphinx must build exactly the rest](https://github.com/useblocks/SPLed/blob/362333b7faa50f54e2233efdca7eccf18613057b/test/test_documentation.py#L117).
- **Compiler-free gate:** all five variants' documents built and checked with ubc on [every pull request](https://github.com/useblocks/SPLed/blob/362333b7faa50f54e2233efdca7eccf18613057b/.github/workflows/ci.yml#L44), in under two minutes.
- **End to end:** Disco's reports have every page under `generated/`, working coverage links, and all 16 report artifacts.

<div class="kpi-grid-4">
<div class="kpi-tile"><div class="kpi-number">256</div><div class="kpi-label">spl-core unit tests</div><div class="kpi-sublabel">passed</div></div>
<div class="kpi-tile"><div class="kpi-number">94</div><div class="kpi-label">SPLed documentation tests</div><div class="kpi-sublabel">passed</div></div>
<div class="kpi-tile"><div class="kpi-number">31</div><div class="kpi-label">CI documentation gate</div><div class="kpi-sublabel">passed, no compiler</div></div>
<div class="kpi-tile"><div class="kpi-number">8/8</div><div class="kpi-label"><a href="https://github.com/useblocks/SPLed/actions/runs/35985268428">CI jobs green</a></div><div class="kpi-sublabel">Windows, Linux, devcontainer, docs</div></div>
</div>

---

<!-- _class: invert -->

<span class="badge">Lesson learned</span>

# A trap only a second reader would find

- [Upstream's lock refresh](https://github.com/avengineers/SPLed/commit/f5ba89efcabb494ccc66a7619943260444c497de) moved sphinx-needs from 8.2 to 8.5.
- 8.5 resolves the variant data right after it loads `ubproject.toml`, before the handler in `conf.py` ran.
- Every reports build read the docs cell and silently lost its report sections, or failed on a fresh checkout.
- The documentation gate caught it when [upstream was merged](https://github.com/useblocks/SPLed/commit/f4f98a57913d15fa45fe39c073c9bdbad1c03a2f). [Moving the selection to the command line](https://github.com/useblocks/spl-core/commit/b3ff837a10d872d95ad4c9ad795641284c702f0d) fixed it for good.

<div class="warn">

A selection that lives in one reader's code breaks without a sound. A selection that is data, or a standard override, cannot.

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

- **A folder for the documents:** move them into `docs/` and mount component docs with [sphinx-mounts](https://github.com/useblocks/sphinx-mounts). The [spl-core setting](https://github.com/useblocks/spl-core/commit/998c97d59a41058ef937ef12c191d19216a72c2c) is ready.
- **Test results as data:** [sphinx-test-reports 2.0](https://github.com/useblocks/sphinx-test-reports/releases/tag/2.0.0) turns JUnit XML into needs that both readers import.
- **Links as data:** replace [`sple_tr_link`](https://github.com/avengineers/spl-core/blob/95a634771491f7c649566b06e3e1fed3f422d86b/src/spl_core/report_generation/spl_sphinx.py#L14) with links written at conversion time.
- **Old warnings:** spl-core's wrapper pages that SPLed does not link, and duplicate implementation needs in the integration suite's listings.
- **The kickstart template:** start new spl-core projects without [the Jinja pass](https://github.com/avengineers/spl-core/blob/95a634771491f7c649566b06e3e1fed3f422d86b/src/spl_core/kickstart/templates/project/conf.py#L71-L84).

<!--
sphinx-codelinks also reads a compilation database that only the VS Code CMake extension copies into place. Pointing it at the configured build would make source tracing variant-aware in CI as well. needs_global_options should move to needs_fields at the same time as the links.
-->

---

<!-- _class: invert -->

<span class="badge">Still open</span>

# What would help in ubCode and ubc

- **Choosing the variant in the IDE:** a setting or picker for the active variant data file, instead of a pointer file on disk.
- **The configured build's output:** indexing generated pages without indexing every build. Today a link to the build directory is not followed.
- **Test results:** first-class support for [sphinx-test-reports](https://github.com/useblocks/sphinx-test-reports) data, so report pages are not placeholders.
- **Traceability from code:** gate [sphinx-codelinks](https://github.com/useblocks/sphinx-codelinks) projects on the variant, not only on where the directive sits.
- **Parity as a feature:** a ubc check that compares its document set with a Sphinx build, like SPLed's [CI gate](https://github.com/useblocks/SPLed/blob/362333b7faa50f54e2233efdca7eccf18613057b/test/test_documentation.py#L295).

---

<!-- _class: invert -->

<span class="badge">Still open</span>

# Getting it upstream

1. Review [useblocks/spl-core#4](https://github.com/useblocks/spl-core/pull/4), then propose the five commits to [avengineers/spl-core](https://github.com/avengineers/spl-core).
2. Release, then switch SPLed from [the fork commit](https://github.com/useblocks/SPLed/blob/362333b7faa50f54e2233efdca7eccf18613057b/pyproject.toml#L9) back to a PyPI version.
3. Land [SPLed#2](https://github.com/useblocks/SPLed/pull/2) and [SPLed#3](https://github.com/useblocks/SPLed/pull/3), and bring the forks' `develop` branches level with [avengineers](https://github.com/avengineers).

<div class="highlight">

Until then, SPLed pins one commit of the fork, so every machine and every CI job builds the same code.

</div>

---

<!-- ─── CLOSING SLIDE ─── -->

<!-- _class: invert closing-slide -->
<!-- _paginate: false -->

# One source, two readers, one answer

<div class="title-divider"></div>

### Questions? Let's talk.

<div class="closing-contact">
<strong>spl-core</strong> · <a href="https://github.com/useblocks/spl-core/pull/4">useblocks/spl-core#4</a><br>
<strong>SPLed</strong> · <a href="https://github.com/useblocks/SPLed/pull/2">useblocks/SPLed#2</a> and <a href="https://github.com/useblocks/SPLed/pull/3">useblocks/SPLed#3</a><br>
<strong>CI</strong> · <a href="https://github.com/useblocks/SPLed/actions/runs/35985268428">green on Windows, Linux, the devcontainer and the docs gate</a>
</div>

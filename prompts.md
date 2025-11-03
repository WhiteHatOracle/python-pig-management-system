Here’s a pass over your HTML/CSS. I found 7 image slots currently using external placeholders. For each, I’ve inferred the intent, suggested size/aspect, and written a tight, generator‑agnostic prompt (plus optional negatives), alt text, and file name.

Brand/style cues pulled from your CSS
- Vibe: clean SaaS, modern, approachable
- Palette: emerald green #00A86B (light mode), #34D399 (dark mode), cool grays, white surfaces
- Typography feel: neo-grotesk sans (Inter-like), soft shadows, rounded corners

Detected image slots and prompts

1) Hero product mockup
- Location: .hero .dashboard-mockup img
- Current: https://i.imgur.com/k2A48Jp.png
- Suggested size/aspect: 1600×1000 (16:10), retina-ready, rounded corners
- Prompt: Clean SaaS dashboard UI for pig farm management. Layout with left sidebar and spacious main area. Top KPI cards: Herd size, Feed remaining, Farrowings due, Health alerts. Central charts: line trend of weight gain, bar chart for feed consumption, small donut for mortality. Table of upcoming tasks/reminders. White cards, subtle soft shadows, minimal icons, crisp grid. Color palette: emerald #00A86B with cool grays. High fidelity, professional, no device frame, no brand logos. Aspect ratio 16:10, high resolution.
- Negative prompt (optional): photoreal animals or people, stock watermarks, heavy gradients, neon colors, skeuomorphic elements, illegible tiny text
- Alt text: Pig farm management dashboard with KPIs, charts and task list
- File name: hero-dashboard-mockup-light-1600x1000.png
- Notes: Also render a dark-mode variant using #34D399 on deep gray panels. You can swap via <picture> and prefers-color-scheme if desired.

2) Feature 1 visual – Intelligent Dashboard
- Location: .features .feature-item:nth-of-type(1) .feature-visual img
- Current: https://i.imgur.com/v8t7E2d.png
- Suggested size/aspect: 1600×900 (16:9)
- Prompt: Analytics-focused SaaS dashboard for pig farming. Grid of KPI tiles (Farrowings this month, Average daily gain, Feed conversion ratio, Health alerts), interactive line and area charts, compact map or barn layout mini-panel, notification sidebar. Light theme with white cards, soft shadows, emerald #00A86B accents, clean sans UI, generous spacing, modern data viz.
- Negative prompt: cluttered widgets, dense text blocks, neon accents, device frames, stock photo backgrounds
- Alt text: Analytics view showing KPIs and charts for a pig farm
- File name: feature-intelligent-dashboard-1600x900.png

3) Feature 2 visual – Automated Feed & Costing
- Location: .features .feature-item.reverse .feature-visual img
- Current: https://i.imgur.com/FwO5K3m.png
- Suggested size/aspect: 1600×900 (16:9)
- Prompt: Feed and cost calculator UI for pig farms. Left panel with inputs (herd size, age groups, growth target sliders), right panel with results: daily feed requirement, projected monthly cost, breakdown by feed types with a donut chart, cost trend sparkline, export/download buttons. Light SaaS styling, white surfaces, emerald #00A86B highlights, clear hierarchy, tidy form controls, legible numbers.
- Negative prompt: photographic farm imagery, noisy backgrounds, brand logos, exaggerated gradients
- Alt text: Feed calculator interface with cost breakdown and charts
- File name: feature-feed-costing-1600x900.png

4) Feature 3 visual – Lifecycle & Health Tracking
- Location: .features .feature-item:nth-of-type(3) .feature-visual img
- Current: https://i.imgur.com/z4b0BqJ.png
- Suggested size/aspect: 1600×900 (16:9)
- Prompt: Breeding and health schedule UI for pig herds. Calendar/timeline view with color-coded events: breeding, farrowing, vaccinations, vet visits. Side panel with animal profile card (ID, age, status), upcoming reminders, completion checkboxes. Clean, airy layout, white cards, emerald #00A86B accents, subtle pastel event colors, accessible contrast, modern SaaS look.
- Negative prompt: dense text, photographic backgrounds, cartoonish icons, harsh neon
- Alt text: Calendar timeline for breeding, farrowing, and vaccination reminders
- File name: feature-lifecycle-health-1600x900.png

5) Testimonial avatar – John M.
- Location: .testimonials .testimonial-card:nth-of-type(1) .author img
- Current: https://randomuser.me/api/portraits/men/32.jpg
- Suggested size/aspect: 800×800 (1:1) for crisp circular crop at 50px
- Prompt: Friendly mid‑40s male farmer headshot, natural smile, light stubble, neutral outdoor background with soft bokeh, simple flannel shirt, no logos. Studio-quality lighting, centered head-and-shoulders, sharp eyes, natural skin tones. Photoreal, 1:1 aspect ratio.
- Negative prompt: text or watermarks, distorted facial features, heavy retouching, hats with logos, sunglasses glare
- Alt text: Portrait of John M., Commercial Farmer in Iowa
- File name: testimonial-john-m-800x800.jpg

6) Testimonial avatar – Sarah L.
- Location: .testimonials .testimonial-card:nth-of-type(2) .author img
- Current: https://randomuser.me/api/portraits/women/44.jpg
- Suggested size/aspect: 800×800 (1:1)
- Prompt: Friendly early‑30s female farmer headshot, warm smile, neutral outdoor farm background with gentle blur, casual solid-color top, hair neatly tied back. Clean natural light, centered composition, photoreal, 1:1 aspect ratio.
- Negative prompt: text/watermarks, exaggerated makeup, logos, harsh shadows, lens distortion
- Alt text: Portrait of Sarah L., Small‑Scale Farmer in the UK
- File name: testimonial-sarah-l-800x800.jpg

7) Testimonial avatar – David C.
- Location: .testimonials .testimonial-card:nth-of-type(3) .author img
- Current: https://randomuser.me/api/portraits/men/56.jpg
- Suggested size/aspect: 800×800 (1:1)
- Prompt: Professional male headshot, late‑30s breeding specialist, neutral indoor background with soft depth-of-field, collared work shirt, approachable expression. Studio-like soft key light, sharp eyes, natural color, photoreal, 1:1 aspect ratio.
- Negative prompt: brand logos, watermark text, extreme contrast, facial distortions
- Alt text: Portrait of David C., Breeding Specialist in Ontario
- File name: testimonial-david-c-800x800.jpg

Optional but recommended (not in your HTML yet)

8) Favicon/App icon
- Use in: /favicon.ico, 180×180 apple-touch-icon, 512×512 for PWA
- Prompt: Minimal pig snout/face icon, flat geometric style, white shape on emerald #00A86B circular or rounded-square background, high contrast, no text. Centered, crisp edges, vector-like, 1:1 aspect ratio.
- File names: favicon-32.png, apple-touch-icon-180.png, app-icon-512.png

9) Social share (Open Graph/Twitter)
- Use in: <meta property="og:image"> 1200×630 (1.91:1)
- Prompt: Clean marketing banner for PigManagePro: abstract white background with soft emerald accents, subtle UI elements (faint dashboard cards and charts) arranged diagonally, space for headline on left, minimal pig icon motif. Premium SaaS look, no heavy text baked in, high contrast focal elements, 1200×630.
- File name: og-pigmanagepro-1200x630.jpg

Tiny implementation note
- For light/dark UI mockups, consider swapping via <picture>:
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="/img/hero-dashboard-mockup-dark-1600x1000.png">
    <img src="/img/hero-dashboard-mockup-light-1600x1000.png" alt="Pig farm management dashboard">
  </picture>

If you tell me which generator you’ll use (Midjourney, SDXL, DALL·E, etc.), I can tune these with exact syntax/parameters and add negative prompts/samplers accordingly.
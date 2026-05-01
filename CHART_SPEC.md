# Crypto Charts Design Spec

This project generates dark, professional crypto data charts for publishing on X.
Every chart must use the shared theme and reusable components so visuals stay consistent across posts.

## Visual Rules

- Canvas: `1200 x 675 px`, `100 DPI`, 16:9 ratio.
- Background: `#0D1117`.
- Surface: `#161B22` for future panels or framed components.
- Primary line color: `#00D4FF`.
- Accent color: `#F7931A` for Bitcoin highlights and key events.
- Up/down colors: `#26C6DA` for up, `#EF5350` for down.
- Grid: `#21262D`.
- Text: `#E6EDF3` primary, `#8B949E` muted, `#484F58` hint.
- Typography: use the sizes and weights defined in `config/theme.py`.
- Never hardcode visual constants in chart or component modules.

## Layout Rules

- Title and subtitle sit in the upper-left area.
- Main price chart uses the primary plot region defined by `theme.LAYOUT["price_axes"]`.
- Volume uses the lower plot region defined by `theme.LAYOUT["volume_axes"]`.
- Source attribution sits in the lower-left corner.
- Watermark uses the configured handle in the lower-right corner.
- Large callouts should use theme callout positions unless the chart needs a specific exception added to `theme.py`.

## Component Rules

- Use `BaseChart` for figure creation, titles, source text, watermark, and saving.
- Use `PriceLine` for price series rendering and high/low annotations.
- Use `VolumeBar` for volume rendering and up/down coloring.
- Use `Annotations` for callouts, event lines, and percentage changes.
- Data fetching must stay in `data/`; rendering code must stay in `components/` and `charts/`.
- Each file in `charts/` should produce exactly one chart type.

## New Chart Workflow

1. Add or reuse a fetcher in `data/fetcher.py`.
2. Create one chart module under `charts/`.
3. Fetch data first and transform it into a clean DataFrame.
4. Initialize `BaseChart`.
5. Add themed axes using layout constants from `config/theme.py`.
6. Draw reusable components from `components/`.
7. Add source attribution and watermark.
8. Save into `output/`.
9. Add a focused test when new theme fields or reusable behavior are introduced.

## Prompt Template

```text
Create a new crypto chart in this project for [asset/protocol/metric].
Use the existing theme from config/theme.py and only draw through reusable components.
Fetch data in data/fetcher.py if a new endpoint is required.
Create one new chart file in charts/ named [chart_name].py.
The chart should include title, subtitle, source, watermark, and save to output/[chart_name].png.
Do not hardcode colors, fonts, canvas size, or layout dimensions outside config/theme.py.
Run the chart script and relevant tests after implementation.
```


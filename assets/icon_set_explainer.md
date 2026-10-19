# Galaxy Stats icon set

Editable sources (this explainer, `icon.svg`, both logos, `og-image.svg`) are tracked in the repo at `assets/`. The exported kit lives in `context/assets/` (gitignored); deployed copies are in `docs/`.

Place the favicon and manifest files in the site root. The logo files and `og-image.svg` are for your own use (header, design edits) and don't need to be deployed.

| File | What it's for |
|---|---|
| `icon.svg` | Main favicon for modern browsers. Scales cleanly and is referenced with `<link rel="icon" type="image/svg+xml">`. |
| `favicon.ico` | Legacy fallback with 16, 32 and 48px versions. Some crawlers and older browsers request `/favicon.ico` directly, so keep it at the site root. The 16px version uses thicker strokes so it stays legible in a tab. |
| `apple-touch-icon.png` | 180×180 icon for iOS "Add to Home Screen". Full-bleed and opaque on purpose, because iOS applies its own rounded corners. |
| `icon-192.png` | Android home-screen icon, listed in the manifest. Also a clean high-res PNG for Google to use as the search-result favicon. |
| `icon-512.png` | Large manifest icon, used for splash screens and high-density displays. |
| `manifest.webmanifest` | Web app manifest. Names the site and points to the 192 and 512 icons. |
| `head-snippet.html` | Ready-to-paste `<head>` tags: favicon links, manifest, theme color, and default OG/Twitter image tags. Intended for the homepage and report pages (captain pages keep their own captain-art og:image). |
| `og-image.png` | 1200×630 social preview card, shown when links are shared on Discord, Slack, X, etc. Includes "OUAG" in the text. |
| `og-image.svg` | Editable source for the OG card. Not needed on the server. |
| `logo-on-dark.svg` | Header logo with light text, transparent background. Use on dark page backgrounds. |
| `logo-on-light.svg` | Header logo with dark text, transparent background. Use on light page backgrounds. |

Both logo files have the wordmark converted to outlines (Lora and Poppins), so they render identically everywhere with no font dependency.

## After deploying

1. Check that `/favicon.ico` and `/icon.svg` load directly in a browser.
2. In Search Console, request indexing of the homepage so Google refreshes the favicon.
3. Make sure robots.txt doesn't block the icon files.
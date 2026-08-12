---
name: html-communication
description: "Communicate through an HTML document; also use when the user mentions HTML without other context."
---

# HTML Communication

Use for plans, specs, write-ups, findings, summaries, reports, comparisons, and UI mocks meant to be read outside the terminal. Do not use for HTML that ships as part of a product.

## Document

Create one self-contained HTML file, capped at 512 KB.

- Write like a spec: dense, scannable, direct. Avoid landing-page heroes, decorative chrome, marketing voice, and em dashes.
- Default to true black, white primary text, and dark gray secondary surfaces or accents.
- Make it mobile-readable with a responsive viewport and no fixed-width layout.
- Use semantic HTML, inline CSS, inline SVG, and data-URL images. Never use remote images; the file must remain fully self-contained and offline-safe.
- Add an inline classic script only when interactivity materially helps. Keep the page useful without JavaScript.
- Never include external or module scripts, inline event handlers, `javascript:` URLs, forms, frames, embeds, objects, applets, meta refresh, linked stylesheets, secrets, private URLs, or local filesystem paths in document content.
- In script-free files, external links may use `target="_blank"` with `rel="noopener noreferrer"`. If any script exists, omit `target="_blank"`.

## UI Mocks

When the user asks for variants:

- Render real styled variants, not prose descriptions.
- Label them A, B, C, and so on.
- Lay them out for direct comparison.

## Delivery

- Store the file in the task's visualization directory outside the product repository unless the user specifies another path.
- Keep one absolute path across iterations so the artifact remains stable.
- Return a clickable local file link.
- Upload only when the user asks or a configured publishing workflow grants standing permission. Report hosting only after upload succeeds.
- Do not open or verify the file in a browser unless the user asks. Static markup validation is allowed.

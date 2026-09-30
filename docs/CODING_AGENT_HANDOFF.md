# Coding-agent handoff — Preview Cleaner 0.1.0

## Objective

Turn the supplied working source prototype into a reliable local macOS/Windows desktop app for authorized removal of separate PDF text overlays. Preserve document content. Do not reinterpret this as an AI image-inpainting project.

## Implemented baseline

`preview_cleaner/core.py` reads PDFs, inspects rendered text spans, parses top-level PDF text objects, applies byte-offset patches, and verifies exported output. `gui.py` provides open/preview/navigation/export and JSON reporting. `__main__.py` is the CLI. `tests/test_core.py` supplies 25 automated cases.

The reference sample is a 12-page PDF whose page wrapper separately invokes the score Form XObject, draws a 150-pt diagonal `Preview` text object, then draws its edition footer. Only the target text-show operand is changed. Do not remove the entire page stream, Form XObject, font resource, gray content, or watermark bounding rectangle.

## First work package

1. Reproduce the existing test result using installed current dependency versions. Record and then lock tested dependencies.
2. Exercise the source app on native macOS and Windows: open file, password prompt, target change, analyze, navigate, preview, export, existing-path refusal, non-ASCII filesystem paths, close and reopen.
3. Add a small fixture corpus with several PDF producers. Separate supported, unsupported, and malformed cases; unsupported must not be reported as clean.
4. Add subprocess-based background work, cancellation, progress, and stricter resource limits. PyMuPDF work should not run concurrently across arbitrary Python threads. Keep source and preview bytes out of telemetry.
5. Review dependency licenses before selecting the distribution model. Build and smoke-test `.app`/`.exe` separately on the respective OS. Do not call source execution a packaged release.

## Next feature priorities (not implemented)

User-selectable pages and per-candidate confirmation; configurable watermark profiles; batch processing with a per-file result; synchronized pan/zoom; comparison highlighting; resumable job report. Preserve the default conservative matching behavior while adding these.

Nested Form-XObject processing must be a separate feature, with shared-object reference accounting and clone-on-write. A Form XObject can contain both a watermark and essential score content or can be reused across pages. Removing the whole object is not acceptable without proving it contains only the selected mark.

Annotation stamps and vector-outline watermarks need separate detectors and tests. Raster watermark cleanup is a different, potentially destructive product mode; keep it off by default and never imply that missing music symbols were recovered reliably.

## Important invariants

- Original source is immutable. Output path cannot replace an existing file or resolve to the source.
- Keep copyright/attribution text, edition footer, metadata, page order, boxes, rotation, vector geometry, and fonts.
- Never remove a target word just because it appears in ordinary text.
- Never use rectangular PDF redaction to remove an overlapping watermark.
- No automatic cloud upload, paid AI service, OCR, or image rasterization of exported pages.
- All exports enable ordinary and high-quality printing (user-requested behavior in 0.2.0). Print-restricted copies remove encryption, opening passwords, and other permission restrictions; already-printable copies preserve security. Report this explicitly. No password guessing. Signed PDFs remain blocked.
- Verify resulting content and distinguish removed / unchanged / unsupported / failed.
- Runtime and tests must use synthetic or authorized fixtures. Do not publish the user's example score as a public test fixture.

## Implementation caveats

The offset parser uses `pypdf.generic.read_object`, not a raw global regex. Unrelated page-stream bytes are retained. Inline-image streams are rejected. A replacement stream is page-local to avoid mutating shared input streams. The entire document is rewritten during export, so file IDs and structural containers can change; do not assert byte-identical PDFs or preserved digital signatures.

Text fingerprint validation protects text content and position, but is not proof of arbitrary graphics equivalence for every PDF. Maintain independent stream checks and add rendered-diff tests with known allowable change masks. The original-sample validation is evidence for that sample, not universal correctness.

The current UI is synchronous and uses Tkinter. A PySide6 UI is a possible later substitution, not required to prove the removal algorithm. There is no existing application repository, migration, or integration requirement assumed by this package.

## Release gates

Core regression suite passes; native Mac/Windows UI acceptance passes; supported fixtures have only expected visual changes; unsupported fixtures remain unchanged; no-overwrite and password/signature tests pass; packaging tested on clean machines; dependency license review completed; usage limitations are visible in the app.

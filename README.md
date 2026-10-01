# Preview Cleaner — working source prototype 0.7.1

A small, local desktop app for removing **supported separate PDF text overlays**, such as the large diagonal `Preview` label in the supplied example. It has a desktop interface and a command-line interface.

**Status:** tested processing core and a packaged macOS app for Apple Silicon on macOS 26 or later. The app was built and smoke-tested on macOS 26.6.2. Windows packaging and testing on other Macs remain to be done. Only use documents you own or are authorized to modify.

## What is included

- Open a PDF; enter the target label (default `Preview`, case-insensitive).
- Analyze and show original/output pages side by side.
- Run analysis in a separate process with page progress, cancellation, and a five-minute timeout. Changing options or loading another document cancels stale work.
- Show source printing permissions and the exact security change expected in the exported copy.
- Navigate all pages and export a new PDF.
- Save a page-by-page JSON verification report.
- Preserve the original file; refuse to overwrite any existing output file.
- Retain PDF vector content rather than exporting page images.
- Enable ordinary and high-quality printing automatically in every export, including when no overlay is found. Print-restricted copies are saved without encryption, opening passwords, or other PDF permission restrictions. Already-printable PDFs retain their existing security. Password-protected inputs still require a valid opening password; passwords are never written to reports.
- Print-only mode preserves page content, including overlays.
- Refuse signed PDFs / detected signature fields.
- Fail closed on unsupported or ambiguous page structures.

All document processing is local. No API key, AI model, OCR engine, subscription, or cloud upload is used. Installing dependencies initially normally needs an Internet connection.

## Run on macOS

Open `dist/PreviewCleaner.app`, or copy it to Applications first. The app includes Python and its runtime dependencies. `dist/PreviewCleaner-macOS-arm64.zip` contains the same app for convenient copying. This local build is ad-hoc signed, not Developer ID signed or notarized.

To rebuild on this Apple Silicon Mac with Python 3.12 and Tkinter:

```bash
bash scripts/build_macos.sh
```

The build recipe uses `requirements-build-macos.txt` and `PreviewCleaner.spec`, runs the tests, verifies the bundle signature, and creates the ZIP. It replaces generated files in `build/` and `dist/`; quit the app before rebuilding. The macOS 26 minimum reflects the bundled Tcl/Tk libraries.

To run directly from source instead:

Use a supported Python 3 installation with Tkinter. Python 3.11 or 3.12 is a reasonable starting point; the test environment was Python 3.13.5. Open Terminal in this extracted project folder:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m preview_cleaner
```

Check Tkinter separately with `python -m tkinter`. An installation without Tkinter needs its matching Tcl/Tk support; alternatively use a Python installer that includes Tkinter. The CLI does not need Tkinter.

## Run on Windows

Open PowerShell in the extracted project folder:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m preview_cleaner
```

These commands avoid needing to activate a PowerShell script.

## Desktop workflow

1. Drag one PDF from Finder onto the **Original PDF** pane, or choose **Open PDF**. Leave the label as `Preview` for the sample. Dropping works before or after loading a document; password prompts and validation are the same as opening a file. Folders and multiple-file drops are rejected.
2. Leave **Remove supported text overlays** checked to clean overlays, or uncheck it for a print-only copy. Printing is always enabled; there is no printing toggle.
3. Choose **Analyze & preview**.
4. Inspect the original/output panes and page-by-page messages. Navigate to check all pages.
5. Choose **Save new PDF** and use a new name, such as `score_printable.pdf`.
6. Optionally choose **Save report**. The report records whether PDF security was removed for printing.

A `no_candidate` result means the detector found no supported-looking text, **not** that the page is guaranteed watermark-free. A label may be an image, vector outlines, or another unsupported representation. Some pages can be cleaned while others remain unchanged; the app reports that distinction.

## Command line

```bash
python -m preview_cleaner "/path/to/input.pdf" --inspect
python -m preview_cleaner "/path/to/input.pdf" -o "/path/to/input_cleaned.pdf" --report "/path/to/report.json"
python -m preview_cleaner "/path/to/input.pdf" --print-only -o "/path/to/input_printable.pdf"
```

Optional label: `--text DRAFT`. Detection remains limited to large diagonal text, even when the target label changes.

All exports enable printing. `--print-only` skips overlay removal; `--inspect` remains read-only and reports the current printing permission. This prepares a PDF for printing in your PDF viewer; it does not send a job to a printer.

Exit codes: `0` successful inspection or export; `1` error; `3` printable output produced but some candidate overlays were unsupported. Version 0.2.0 exports even when no overlay is removed; the former exit code `2` is no longer used.

## Why the sample works

Direct inspection of `30108419.pdf` found a `Preview` text overlay on all 12 pages: Helvetica, about 150 pt, 45 degrees, approximately 35% opacity. Each overlay has an isolated `(Preview)Tj` text-show instruction in the page's top-level content. The score content is referenced separately through Form XObjects.

The prototype empties only that isolated text-show operand. It does not paint a white rectangle, use redaction, threshold gray pixels, reconstruct notes, or flatten pages. The publisher attribution, copyright notice, edition footer, score, and lyrics are left in their original PDF content.

The provided test sample was processed successfully: **12 of 12 overlays removed**. The source sample and cleaned score are not bundled in the source project. `docs/sample_cleaning_report.json` records the result.

## Deliberate limits

This is not a universal watermark remover. It supports a narrow, testable class of native PDF text overlays:

- Exact ASCII target label, 1–40 characters, case-insensitive.
- Visually detected size at least 36 pt and diagonal angle 15–75 degrees from horizontal.
- One standalone `Tj` or `TJ` text-show operation in its own `BT...ET` text object, on the top-level page stream.
- Literal, hex, or simple kerning-array strings that decode to the target.

It leaves scanned/image watermarks, text converted to outlines, nested Form-XObject watermarks, annotation stamps, mixed text objects, unknown encodings, inline-image content streams, and ambiguous target occurrences unchanged. In particular, if a page has both a small standalone `Preview` word and a large one, this version may reject the page rather than risk removing the wrong one.

Limits: 100 MB file, 300 pages, 4 MB combined top-level page content. Desktop cleaning and verification run in a separate process with progress and a Cancel button; jobs time out after five minutes. Opening documents and rendering individual preview pages still run in the UI. Temporary job files live in a private local directory and are removed on completion, cancellation, or normal app exit. Resource limits are not a security sandbox. Do not use the prototype as an Internet-facing upload service for untrusted documents.

## Verification and tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

The current suite passes 93 automated tests on macOS. Tests cover supported encodings, non-target text, phrases, ambiguity, mixed text objects, inline images, comments, clipping mode, nested forms, raster pages, password handling, signatures, no-overwrite behavior, repeat processing, printable copies, dropped-path handling, worker crashes/timeouts/cancellation, and the Tk event loop. The GUI tests require a graphical desktop with Tkinter. Print-only regression fixtures verify unchanged content streams and rendered pixels with AES-128/AES-256 security and both blocked and low-quality-only printing.

`tests/fixtures` contains only synthetic PDFs from ReportLab, fpdf2, and PyMuPDF, plus a malformed file. Supported fixtures are checked for unchanged graphics and exact rendered pixels outside the removed label. Unsupported fixtures must remain byte-identical. To regenerate the corpus, install `requirements-fixtures.txt` and run `python scripts/generate_fixtures.py`; fixture-generator dependencies are not bundled into the app.

Every export checks page count, page geometry, encryption/permission settings, and non-target text/font/size/position signatures. On the uploaded sample, an additional structural check verified unchanged decoded bytes in all 118 non-page-content, non-container streams, and verified each page stream differed only in the expected text-show operand. The original and output were rendered using PDFium; the app also rendered them using MuPDF.

See `docs/validation.json` for the exact execution environment and scope. This does not substitute for native OS testing or broad PDF-corpus testing.

## Dependency / distribution note

PyMuPDF is available under AGPL and commercial licensing. Before distributing a closed-source application, review those terms or choose another PDF backend. pypdf and Tcl/Tk have their own licenses. The generated macOS app bundles runtime dependencies; PyMuPDF and pypdf package metadata and licenses are included. Source installations may use newer dependency versions than the recorded test environment; rerun the tests after installation.

The macOS build recipe is documented above. For a future Windows build, a candidate command after validating on Windows is:

```bash
python -m pip install pyinstaller
python -m PyInstaller --windowed --onedir --name PreviewCleaner run_app.py
```

Build Windows packages on Windows; that build has not been tested. Developer ID signing and notarization are not included in the macOS recipe.

The local app includes a custom icon sourced from `assets/icon.svg`. See [the macOS release procedure](docs/MACOS_RELEASE.md) for the prepared Developer ID signing/notarization script, the built-in `--self-test` diagnostic, and the clean-Mac acceptance checklist. The current local build remains ad-hoc signed until those external steps are completed.

## References

- PyMuPDF low-level stream interfaces: https://pymupdf.readthedocs.io/en/latest/recipes-low-level-interfaces.html
- PyMuPDF document/save APIs: https://pymupdf.readthedocs.io/en/latest/document.html
- PyMuPDF licensing: https://pymupdf.readthedocs.io/en/latest/about.html#license-and-copyright
- pypdf generic objects: https://pypdf.readthedocs.io/en/stable/modules/generic.html
- Tkinter: https://docs.python.org/3/library/tkinter.html
- PyInstaller platform/build model: https://pyinstaller.org/en/stable/operating-mode.html

## Interface

The Google Stitch-inspired comparison workspace keeps export options and printing/security status in a sidebar. PDF details shows source metadata in a read-only window; verification details expand below the previews. Previews refit on resize, and Command-O / Command-S open and save. See [UI design](docs/UI_DESIGN.md).

Double-click either preview or choose **Expand** for a full-screen page viewer. Use Fit page, Fit width, +/− to zoom, drag or scroll to pan, and ←/→ to change pages. Switch Original/Output without losing the current view; Esc returns to the comparison workspace. Display bitmaps are capped at 12 megapixels to bound memory use.

Version 0.7 adds persistent page warnings, direct page-number entry in both views, clearer printable-copy export wording, grouped PDF details with readable timestamps, and an explicit full-screen Original/Output heading.

Worker startup uses a headless subprocess (native `posix_spawn` on macOS), avoiding the forked Cocoa state that caused intermittent startup/cancellation crashes. Passwords travel through the child’s standard-input pipe, never command arguments or configuration files. Progress and results stay in a private temporary directory and are removed after the worker exits.

# Preview Cleaner UI design

Design reference: [Google Stitch project](https://stitch.withgoogle.com/projects/1339150647637069109).

The native Tkinter adaptation uses the generated design's navy headings, teal actions, light surfaces, fixed options sidebar, and equal comparison panels. The implementation retains only supported app functionality. The reference's difference mode, fabricated verification assertions, and RAM-only storage claims are not implemented or shown.

The main flow is Open PDF → adjust options → Analyze & preview → review → Save new PDF. Exports remain disabled until a verified result exists. Changing options or replacing the document invalidates that result. Processing shows progress and cancellation in the footer. Verification details expand on demand; PDF details opens a separate read-only, scrollable window with original-file metadata and security information. No document content is sent to Stitch or any cloud service.

The PDF details window closes when its document is replaced. The overlay field disables in print-only mode. Navigation disables at page boundaries. Previews automatically refit after resizing; Command-O and Command-S open and save. Printing is always enabled, with password/security removal explicitly explained for restricted sources.

Palette: navy #123a56, teal #0d7682, workspace #f5f7fa, preview canvas #e9eef3, border #dce3ea, muted text #536477.

Full-screen inspection is available from each pane’s Expand button or a double-click. Original/output switching preserves page, zoom and pan. Fit page/width, zoom, scrollbars, drag-to-pan, arrow navigation and Escape are supported. Replacing a document or invalidating its result closes the viewer before document resources are released.

## October UX review

[Fresh Stitch review project](https://stitch.withgoogle.com/projects/10824163750815707449). Version 0.7 adopts persistent outcome warnings, direct page entry in both viewers, Save printable copy wording, grouped read-only PDF metadata with readable complete timestamps, and a high-contrast full-screen source selector and heading. Unsupported-page warnings stay visible even when viewing another page; export remains available after verified processing. Invalid page text keeps the current page; numeric entries clamp to document bounds. Unknown or partial PDF dates remain unchanged rather than inventing date components or time zones.

The sidebar reserves its bottom action and authorization note at their natural height. Document/options/security content scrolls independently when long filenames or small windows exceed available height. Mouse-wheel scrolling is scoped to the sidebar; keyboard focus reveals controls as needed.

## macOS viewer crash mitigation (0.7.3)

On macOS, Expand now maximizes a normal viewer window rather than entering a native fullscreen Space. This retains native focus and close controls and avoids asynchronous fullscreen-exit callbacks during destruction. Escape and Close still return to the comparison view; scheduled focus/render callbacks are cancelled before destruction. Other platforms retain native fullscreen.

The supplied 0.7.2 crash shows `CFRelease` in Tk 9.0.4 `resetTkLayerBitmapContext` during an AppKit fullscreen-exit transition. Tk's `TkWmDeadWindow` releases the bitmap context before closing the native window, without clearing the pointer; a late backing-property callback is a plausible double release. This is a targeted workaround, not an upstream Tk repair or proof that all display-change crashes are fixed. The user could not identify the exact triggering control. Main-window green-button fullscreen and multi-monitor transitions need separate acceptance checks.

Upstream source inspected: https://github.com/tcltk/tk/blob/core-9-0-4/macosx/tkMacOSXWm.c and https://github.com/tcltk/tk/blob/core-9-0-4/macosx/tkMacOSXWindowEvent.c.

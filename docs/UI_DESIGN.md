# Preview Cleaner UI design

Design reference: [Google Stitch project](https://stitch.withgoogle.com/projects/1339150647637069109).

The native Tkinter adaptation uses the generated design's navy headings, teal actions, light surfaces, fixed options sidebar, and equal comparison panels. The implementation retains only supported app functionality. The reference's difference mode, fabricated verification assertions, and RAM-only storage claims are not implemented or shown.

The main flow is Open PDF → adjust options → Analyze & preview → review → Save new PDF. Exports remain disabled until a verified result exists. Changing options or replacing the document invalidates that result. Processing shows progress and cancellation in the footer. Verification details expand on demand; PDF details opens a separate read-only, scrollable window with original-file metadata and security information. No document content is sent to Stitch or any cloud service.

The PDF details window closes when its document is replaced. The overlay field disables in print-only mode. Navigation disables at page boundaries. Previews automatically refit after resizing; Command-O and Command-S open and save. Printing is always enabled, with password/security removal explicitly explained for restricted sources.

Palette: navy #123a56, teal #0d7682, workspace #f5f7fa, preview canvas #e9eef3, border #dce3ea, muted text #536477.

Full-screen inspection is available from each pane’s Expand button or a double-click. Original/output switching preserves page, zoom and pan. Fit page/width, zoom, scrollbars, drag-to-pan, arrow navigation and Escape are supported. Replacing a document or invalidating its result closes the viewer before document resources are released.

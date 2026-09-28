"""Small Tk desktop UI. Rendering is for display; exported pages stay vector PDF."""
from __future__ import annotations

import base64
import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

import pymupdf

from .core import CleanerError, PasswordNeeded, clean, open_pdf, read_pdf, save_new


class CleanerWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Preview Cleaner — PDF text-overlay prototype")
        self.root.geometry("1280x960")
        self.root.minsize(960, 780)
        self.path: Path | None = None
        self.data: bytes | None = None
        self.password = ""
        self.original: pymupdf.Document | None = None
        self.output: pymupdf.Document | None = None
        self.result = None
        self.page = 0
        self.images: list[tk.PhotoImage] = []
        self.target = tk.StringVar(value="Preview")
        self.status = tk.StringVar(value="Open a PDF to begin. Your original file will not be overwritten.")
        self.page_label = tk.StringVar(value="No document")

        main = ttk.Frame(root, padding=16)
        main.pack(fill="both", expand=True)
        ttk.Label(main, text="Preview Cleaner", font=("TkDefaultFont", 22, "bold")).pack(anchor="w")
        ttk.Label(main, text="Local-only removal of supported, separate text overlays — no OCR or AI.").pack(anchor="w", pady=(2, 12))
        toolbar = ttk.Frame(main)
        toolbar.pack(fill="x", pady=(0, 10))
        ttk.Button(toolbar, text="Open PDF…", command=self.choose_file).pack(side="left")
        ttk.Label(toolbar, text="Watermark text:").pack(side="left", padx=(18, 5))
        ttk.Entry(toolbar, textvariable=self.target, width=20).pack(side="left")
        self.process_button = ttk.Button(toolbar, text="Analyze & preview", command=self.process, state="disabled")
        self.process_button.pack(side="left", padx=10)
        self.save_button = ttk.Button(toolbar, text="Save new PDF…", command=self.save, state="disabled")
        self.save_button.pack(side="left")
        self.report_button = ttk.Button(toolbar, text="Save report…", command=self.save_report, state="disabled")
        self.report_button.pack(side="left", padx=10)
        self.path_label = ttk.Label(main, text="No PDF selected", wraplength=1200)
        self.path_label.pack(anchor="w", pady=(0, 8))

        viewer = ttk.Frame(main)
        viewer.pack(fill="both", expand=True)
        viewer.columnconfigure(0, weight=1)
        viewer.columnconfigure(1, weight=1)
        viewer.rowconfigure(0, weight=1)
        self.panels = []
        for col, title in enumerate(("Original PDF", "Output preview")):
            frame = ttk.LabelFrame(viewer, text=title, padding=8)
            frame.grid(row=0, column=col, sticky="nsew", padx=(0, 6) if col == 0 else (6, 0))
            label = ttk.Label(frame, text="Open a document" if col == 0 else "Run Analyze & preview", anchor="center")
            label.pack(fill="both", expand=True)
            self.panels.append(label)
        nav = ttk.Frame(main)
        nav.pack(fill="x", pady=8)
        ttk.Button(nav, text="◀ Previous", command=lambda: self.go(-1)).pack(side="left")
        ttk.Label(nav, textvariable=self.page_label).pack(side="left", padx=15)
        ttk.Button(nav, text="Next ▶", command=lambda: self.go(1)).pack(side="left")
        ttk.Button(nav, text="Fit / refresh", command=self.render).pack(side="right")
        ttk.Label(main, textvariable=self.status, wraplength=1200).pack(anchor="w", pady=(0, 8))
        self.log = tk.Text(main, height=5, wrap="word", state="disabled")
        self.log.pack(fill="x")
        ttk.Label(main, text="For documents you own or are authorized to modify. Unsupported pages are left unchanged.").pack(anchor="w", pady=(8, 0))
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.target.trace_add("write", self.invalidate_result)

    def invalidate_result(self, *_):
        self.result = None
        if self.output is not None:
            self.output.close()
            self.output = None
        self.save_button.configure(state="disabled")
        self.report_button.configure(state="disabled")
        if self.original is not None:
            self.status.set("Target changed. Run Analyze & preview again before export.")
            self.render()

    def note(self, text: str):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.insert("1.0", text)
        self.log.configure(state="disabled")

    def choose_file(self):
        path = filedialog.askopenfilename(title="Open PDF", filetypes=[("PDF documents", "*.pdf")])
        if path:
            self.load_path(Path(path))

    def load_path(self, path: Path):
        new_doc = None
        try:
            data = read_pdf(path)
            password = ""
            try:
                new_doc = open_pdf(data)
            except PasswordNeeded:
                answer = simpledialog.askstring("PDF password", "Enter the PDF opening password:", show="*", parent=self.root)
                if answer is None:
                    return
                password = answer
                new_doc = open_pdf(data, password)
            self.close_documents()
            self.path, self.data, self.password = path, data, password
            self.original, self.output, self.result = new_doc, None, None
            self.page = 0
            self.path_label.configure(text=str(path))
            self.process_button.configure(state="normal")
            self.save_button.configure(state="disabled")
            self.report_button.configure(state="disabled")
            self.status.set(f"Loaded {len(self.original)} pages. Analyze before saving.")
            self.note("The first version handles large diagonal text labels in separate top-level PDF text objects. Scanned/image watermarks are not reconstructed.")
            self.render()
        except Exception as exc:
            if new_doc is not None and new_doc is not self.original:
                new_doc.close()
            messagebox.showerror("Cannot open PDF", str(exc))

    def process(self):
        if self.data is None:
            return
        self.invalidate_result()
        self.root.configure(cursor="watch")
        self.status.set("Analyzing and verifying…")
        self.root.update_idletasks()
        try:
            result = clean(self.data, self.target.get(), self.password)
            new_output = open_pdf(result.pdf_bytes, self.password)
            if self.output is not None:
                self.output.close()
            self.result, self.output = result, new_output
            report = result.report
            changed = report["removed_count"]
            self.save_button.configure(state="normal" if changed else "disabled")
            self.report_button.configure(state="normal")
            self.status.set(f"Removed {changed} overlay(s) on {report['pages_changed']} of {report['page_count']} pages. Review both panes before export.")
            self.note("\n".join(f"Page {r['page']}: {r['status']} — {r['reason']}" for r in report["pages"]))
            self.render()
            if report["unsupported_pages"]:
                messagebox.showwarning("Some pages were left unchanged", "Unsupported pages: " + ", ".join(map(str, report["unsupported_pages"])) + ". See the report; do not assume all marks were removed.")
            elif not changed:
                messagebox.showinfo("No supported overlay found", "No supported separate text overlay was removed. The file may use an image, vector outlines, or an unsupported text arrangement. The original is unchanged.")
        except Exception as exc:
            self.status.set("Processing failed. No file has been saved.")
            messagebox.showerror("Could not process PDF", str(exc))
        finally:
            self.root.configure(cursor="")

    def render(self):
        self.images = []
        for label, document in zip(self.panels, (self.original, self.output)):
            if document is None:
                label.configure(image="", text="Run Analyze & preview" if self.original else "Open a document")
                continue
            page = document[self.page]
            width = max(300, label.winfo_width() - 12)
            height = max(380, label.winfo_height() - 12)
            scale = min(width / page.rect.width, height / page.rect.height, 1.75)
            pixmap = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), alpha=False)
            image = tk.PhotoImage(data=base64.b64encode(pixmap.tobytes("png")))
            label.configure(image=image, text="")
            self.images.append(image)
        self.page_label.set(f"Page {self.page + 1} of {len(self.original)}" if self.original is not None else "No document")

    def go(self, step: int):
        if self.original is not None:
            self.page = min(max(self.page + step, 0), len(self.original) - 1)
            self.render()

    def save(self):
        if self.result is None or not self.result.report["removed_count"]:
            return
        path = filedialog.asksaveasfilename(
            title="Save a new PDF (existing files are never replaced)",
            initialdir=str(self.path.parent), initialfile=f"{self.path.stem}_cleaned.pdf",
            defaultextension=".pdf", filetypes=[("PDF document", "*.pdf")],
        )
        if path:
            try:
                save_new(path, self.result.pdf_bytes, self.path)
                self.status.set(f"Saved: {path}. Original unchanged.")
            except CleanerError as exc:
                messagebox.showerror("Could not save PDF", str(exc))

    def save_report(self):
        if self.result is None:
            return
        path = filedialog.asksaveasfilename(
            title="Save verification report", initialfile=f"{self.path.stem}_cleaning_report.json",
            defaultextension=".json", filetypes=[("JSON report", "*.json")],
        )
        if path:
            try:
                save_new(path, json.dumps(self.result.report, indent=2, ensure_ascii=False).encode("utf-8"), self.path)
            except CleanerError as exc:
                messagebox.showerror("Could not save report", str(exc))

    def close_documents(self):
        for document in (self.original, self.output):
            if document is not None:
                document.close()
        self.original = self.output = None

    def close(self):
        self.close_documents()
        self.root.destroy()


def main():
    root = tk.Tk()
    CleanerWindow(root)
    root.mainloop()

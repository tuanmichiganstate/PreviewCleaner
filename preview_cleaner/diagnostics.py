"""Offline packaged-app smoke test using only synthetic data."""
import json
import platform
import time
from pathlib import Path

import pymupdf
from tkinterdnd2 import DND_FILES, TkinterDnD
from tkinter import ttk

from . import __version__
from .core import open_pdf, save_new
from .jobs import CleaningJob


def run(report_path):
    root = TkinterDnD.Tk()
    root.withdraw()
    job = None
    report = {"app_version": __version__, "macos": platform.mac_ver()[0],
              "architecture": platform.machine(), "checks": [], "passed": False}
    try:
        label = ttk.Label(root)
        label.drop_target_register(DND_FILES)
        assert root.tk.call("bind", str(label), "<<DropTargetTypes>>")
        report["checks"].append("native drag-and-drop library and file-drop registration")
        with pymupdf.open() as doc:
            page = doc.new_page(width=612, height=792)
            page.insert_text((40, 50), "Preserve diagnostic text.")
            stream = doc.get_new_xref()
            doc.update_object(stream, "<<>>")
            doc.update_stream(stream, b"q .70710678 .70710678 -.70710678 .70710678 100 200 cm "
                              b"BT /helv 72 Tf (Preview) Tj ET Q")
            doc.xref_set_key(page.xref, "Contents", "[" + " ".join(
                f"{xref} 0 R" for xref in page.get_contents() + [stream]) + "]")
            source = doc.tobytes(encryption=pymupdf.PDF_ENCRYPT_AES_256,
                                user_pw="synthetic-test", owner_pw="synthetic-owner", permissions=0)
        heartbeat = []
        root.after(0, lambda: heartbeat.append(True))
        job = CleaningJob(source, "Preview", "synthetic-test", True)
        deadline = time.monotonic() + 30
        result = None
        while result is None and time.monotonic() < deadline:
            root.update()
            for message in job.poll():
                if message[0] == "error":
                    raise RuntimeError(message[1])
                if message[0] == "done":
                    result = message[1]
            time.sleep(0.01)
        assert result is not None, "Worker did not complete"
        assert heartbeat, "Tk event loop did not run"
        assert result.report["removed_count"] == 1, "Diagnostic overlay was not removed"
        assert result.report["printing_allowed"] and result.report["security_removed_for_printing"]
        with open_pdf(result.pdf_bytes) as output:
            assert "Preserve diagnostic text." in output[0].get_text()
            assert "Preview" not in output[0].get_text()
            assert output[0].get_pixmap().width > 0
        report["checks"].extend(["spawned PDF worker", "responsive Tk event loop", "password authentication",
                                  "overlay removal and text preservation", "printable output", "page rendering"])
        import signal
        exits = {}
        for index in range(50):
            job = CleaningJob(source, "Preview", "synthetic-test", True)
            folder = job.folder
            time.sleep((0, 0.002, 0.02)[index % 3])
            job.close()
            code = job.process.returncode
            expected = (0, 1) if platform.system() == "Windows" else (0, -signal.SIGTERM, -signal.SIGKILL)
            assert code in expected, f"Worker startup/cancellation crashed: {code}"
            assert not folder.exists()
            exits[str(code)] = exits.get(str(code), 0) + 1
        report["worker_cancellation_stress"] = {"iterations": 50, "exit_codes": exits, "unexpected_exits": 0}
        report["checks"].append("50 headless worker starts/cancellations after Tk initialization")
        report["passed"] = True
    except Exception as exc:
        report["error"] = str(exc)
    finally:
        if job is not None:
            job.close()
        root.destroy()
    save_new(Path(report_path), json.dumps(report, indent=2).encode())
    return 0 if report["passed"] else 1

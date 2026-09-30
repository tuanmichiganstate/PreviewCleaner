import time
from types import SimpleNamespace

import pytest
from tkinterdnd2 import TkinterDnD
from preview_cleaner import gui
from preview_cleaner.core import open_pdf
import pymupdf
from test_core import make_pdf


@pytest.fixture
def window(monkeypatch):
    root = TkinterDnD.Tk()
    root.withdraw()
    app = gui.CleanerWindow(root)
    for name in ("showinfo", "showwarning", "showerror"):
        monkeypatch.setattr(gui.messagebox, name, lambda *a, **k: None)
    yield app
    app.close()


def test_gui_worker_keeps_event_loop_running(window, tmp_path):
    source = tmp_path / "test.pdf"
    source.write_bytes(make_pdf())
    window.load_path(source)
    heartbeat = []
    window.root.after(0, lambda: heartbeat.append(True))
    window.process()
    deadline = time.monotonic() + 20
    while window.job and time.monotonic() < deadline:
        window.root.update()
        time.sleep(0.01)
    assert heartbeat
    assert window.result.report["removed_count"] == 1
    assert str(window.cancel_button["state"]) == "disabled"


def test_options_cancel_job_and_invalidate_exports(window, tmp_path):
    source = tmp_path / "test.pdf"
    source.write_bytes(make_pdf())
    window.load_path(source)
    window.process()
    folder = window.job.folder
    window.target.set("Draft")
    assert window.job is None and not folder.exists()
    assert window.result is None
    assert str(window.save_button["state"]) == "disabled"


@pytest.mark.parametrize("answer", [None, "wrong", "open-test"])
def test_dropped_encrypted_pdf_reuses_password_checks(window, tmp_path, monkeypatch, answer):
    original = tmp_path / "original.pdf"
    original.write_bytes(make_pdf())
    window.load_path(original)
    encrypted = tmp_path / "Thử nghiệm {protected}.pdf"
    with open_pdf(make_pdf()) as doc:
        encrypted.write_bytes(doc.tobytes(encryption=pymupdf.PDF_ENCRYPT_AES_256,
                                         owner_pw="owner-test", user_pw="open-test", permissions=0))
    monkeypatch.setattr(gui.simpledialog, "askstring", lambda *a, **k: answer)
    payload = window.root.tk.call("format", "%s", (str(encrypted),))
    window.drop_pdf(SimpleNamespace(data=payload))
    window.root.update()
    assert window.path == (encrypted if answer == "open-test" else original)
    if answer == "open-test":
        assert "printing blocked" in window.security_status.get()
        assert "restrictions removed" in window.security_status.get()


def test_loading_new_document_cancels_previous_job(window, tmp_path):
    first, second = tmp_path / "first.pdf", tmp_path / "second.pdf"
    first.write_bytes(make_pdf())
    second.write_bytes(make_pdf(fontsize=12))
    window.load_path(first)
    window.process()
    folder = window.job.folder
    window.load_path(second)
    assert window.path == second and window.job is None
    assert not folder.exists() and window.result is None


def test_pdf_details_are_read_only_and_close_on_replacement(window, tmp_path):
    source = tmp_path / "metadata.pdf"
    source.write_bytes(make_pdf())
    window.load_path(source)
    window.show_pdf_details()
    dialog = window.pdf_details_window
    assert dialog.winfo_exists()
    def text_widgets(widget):
        for child in widget.winfo_children():
            if isinstance(child, gui.tk.Text):
                yield child
            yield from text_widgets(child)
    details = list(text_widgets(dialog))[0]
    assert str(details["state"]) == "disabled"
    content = details.get("1.0", "end")
    assert "metadata.pdf" in content and "SOURCE PRINTING" in content
    assert "CREATOR" in content and "PRODUCER" in content
    window.load_path(source)
    assert not dialog.winfo_exists()


def test_navigation_and_overlay_controls_follow_document_state(window, tmp_path):
    assert str(window.pdf_details_button["state"]) == "disabled"
    source = tmp_path / "one-page.pdf"
    source.write_bytes(make_pdf())
    window.load_path(source)
    assert str(window.pdf_details_button["state"]) == "normal"
    assert str(window.previous_button["state"]) == "disabled"
    assert str(window.next_button["state"]) == "disabled"
    window.remove_overlays.set(False)
    assert str(window.target_entry["state"]) == "disabled"
    window.remove_overlays.set(True)
    assert str(window.target_entry["state"]) == "normal"

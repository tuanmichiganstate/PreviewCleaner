"""Disposable PDF worker processes; document bytes never go to logs or telemetry."""
from __future__ import annotations

import json
import multiprocessing as mp
from pathlib import Path
from tempfile import TemporaryDirectory
from time import monotonic

from .core import Result, clean, read_pdf


def _run(folder: str, target: str, password: str, remove_overlays: bool, sender):
    try:
        root = Path(folder)
        result = clean(read_pdf(root / "input.pdf"), target, password,
                       remove_overlays=remove_overlays,
                       progress=lambda phase, done, total: sender.send(("progress", phase, done, total)))
        (root / "output.pdf").write_bytes(result.pdf_bytes)
        (root / "report.json").write_text(json.dumps(result.report), encoding="utf-8")
        sender.send(("done",))
    except Exception as exc:
        sender.send(("error", str(exc)))
    finally:
        sender.close()


class CleaningJob:
    """One isolated job with bounded lifetime and parent-owned private storage."""
    def __init__(self, data: bytes, target: str, password: str, remove_overlays: bool,
                 timeout: float = 300):
        self.storage = TemporaryDirectory(prefix="preview-cleaner-")
        self.folder = Path(self.storage.name)
        self.closed = False
        self.started = monotonic()
        self.timeout = timeout
        context = mp.get_context("spawn")
        self.receiver, sender = context.Pipe(duplex=False)
        self.process = context.Process(target=_run, args=(str(self.folder), target, password,
                                                        remove_overlays, sender), daemon=True)
        try:
            (self.folder / "input.pdf").write_bytes(data)
            self.process.start()
        except Exception:
            self.receiver.close()
            self.storage.cleanup()
            raise
        finally:
            sender.close()

    def poll(self):
        """Return small progress messages, a Result, or a terminal error."""
        if self.closed:
            return []
        if monotonic() - self.started > self.timeout:
            self.close()
            return [("error", "Processing exceeded five minutes. Try a smaller PDF.")]
        messages = []
        while self.receiver.poll():
            try:
                message = self.receiver.recv()
            except EOFError:
                self.close()
                return messages + [("error", "The PDF worker exited unexpectedly. No file was saved.")]
            if message[0] == "done":
                try:
                    result = Result((self.folder / "output.pdf").read_bytes(),
                                    json.loads((self.folder / "report.json").read_text(encoding="utf-8")))
                    return messages + [("done", result)]
                finally:
                    self.close()
            if message[0] == "error":
                self.close()
                return messages + [message]
            messages.append(message)
        if not self.process.is_alive():
            # Check again next poll: the final message may have arrived after poll().
            if not self.receiver.poll():
                self.close()
                return messages + [("error", "The PDF worker exited unexpectedly. No file was saved.")]
        return messages

    def close(self):
        if self.closed:
            return
        self.closed = True
        if self.process.is_alive():
            self.process.terminate()
        self.process.join(timeout=0.2)
        if self.process.is_alive():
            self.process.kill()
            self.process.join(timeout=0.2)
        self.receiver.close()
        self.process.close()
        self.storage.cleanup()

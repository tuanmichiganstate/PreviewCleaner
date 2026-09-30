import hashlib
import json
from pathlib import Path

import pymupdf
import pytest
from preview_cleaner.core import CleanerError, clean, open_pdf

FIXTURES = Path(__file__).parent / "fixtures"
CASES = json.loads((FIXTURES / "manifest.json").read_text())


@pytest.mark.parametrize("case", CASES, ids=lambda c: c["file"])
def test_producer_corpus(case):
    data = (FIXTURES / case["file"]).read_bytes()
    assert hashlib.sha256(data).hexdigest() == case["sha256"]
    if case["expected"] == "error":
        with pytest.raises(CleanerError):
            clean(data)
        return
    result = clean(data)
    assert result.report["pages"][0]["status"] == case["expected"]
    if case["expected"] != "removed":
        assert result.pdf_bytes == data
        return
    with open_pdf(data) as source, open_pdf(result.pdf_bytes) as output:
        assert source.metadata == output.metadata
        assert source[0].get_drawings() == output[0].get_drawings()
        # Outside the detected watermark bbox, rendered RGB pixels must be exact.
        before, after = source[0].get_pixmap(), output[0].get_pixmap()
        assert (before.width, before.height, before.n) == (after.width, after.height, after.n)
        box = pymupdf.Rect(result.report["pages"][0]["candidates"][0]["bbox"])
        box = box + (-3, -3, 3, 3)
        a, b = before.samples, after.samples
        assert a != b
        for y in range(before.height):
            for x in range(before.width):
                if box.contains(pymupdf.Point(x, y)):
                    continue
                offset = (y * before.width + x) * before.n
                assert a[offset:offset + before.n] == b[offset:offset + before.n]


@pytest.mark.parametrize("case", [c for c in CASES if c["expected"] != "error"], ids=lambda c: c["file"])
def test_corpus_print_only_is_byte_identical_when_already_printable(case):
    data = (FIXTURES / case["file"]).read_bytes()
    assert clean(data, remove_overlays=False).pdf_bytes == data

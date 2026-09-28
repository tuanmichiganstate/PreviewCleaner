from __future__ import annotations
import pytest
import pymupdf
from preview_cleaner.core import (
    CleanerError, PasswordNeeded, UnsupportedContent, analyze, clean,
    find_patches, open_pdf, parse_instructions, save_new,
)


def make_pdf(show=b"(Preview) Tj", *, fontsize=72, rotation=True, extra=b"", mode=0):
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((50, 60), "Test document: keep this text.", fontsize=12, fontname="helv")
    page.draw_line((45, 470), (540, 470), width=0.6)
    transform = b".70710678 .70710678 -.70710678 .70710678 100 200 cm" if rotation else b"1 0 0 1 100 200 cm"
    content = b"q " + transform + b" BT /helv " + str(fontsize).encode() + b" Tf " + str(mode).encode() + b" Tr 0 0 Td " + show + b" ET Q\n" + extra
    xref = doc.get_new_xref()
    doc.update_object(xref, "<<>>")
    doc.update_stream(xref, content)
    refs = page.get_contents() + [xref]
    doc.xref_set_key(page.xref, "Contents", "[" + " ".join(f"{r} 0 R" for r in refs) + "]")
    data = doc.tobytes()
    doc.close()
    return data


def test_basic_removes_only_mark():
    source = make_pdf()
    result = clean(source)
    assert result.report["removed_count"] == 1
    with open_pdf(result.pdf_bytes) as doc:
        assert "Preview" not in doc[0].get_text()
        assert "keep this text" in doc[0].get_text()
        assert len(doc[0].get_drawings()) == 1


@pytest.mark.parametrize("show", [b"(PREVIEW) Tj", b"(preview) Tj", b"<50726576696577> Tj", b"(\\120review) Tj", b"[(Pre) 0 (view)] TJ", b"[(Pre) 0.5 (view)] TJ"])
def test_supported_string_encodings(show):
    result = clean(make_pdf(show))
    assert result.report["removed_count"] == 1


def test_small_body_word_is_unchanged():
    source = make_pdf(fontsize=12)
    result = clean(source)
    assert result.pdf_bytes == source


def test_horizontal_word_is_unchanged():
    source = make_pdf(rotation=False)
    assert clean(source).pdf_bytes == source


def test_larger_phrase_is_unchanged():
    source = make_pdf(b"(Preview this document) Tj")
    assert clean(source).pdf_bytes == source


def test_mixed_object_is_unchanged():
    source = make_pdf(b"(Preview) Tj 0 -100 Td (Important text) Tj")
    result = clean(source)
    assert result.report["removed_count"] == 0
    assert result.report["unsupported_pages"] == [1]
    assert result.pdf_bytes == source


def test_ambiguous_small_and_large_word_fails_closed():
    source = make_pdf(extra=b"BT /helv 12 Tf 50 100 Td (Preview) Tj ET")
    result = clean(source)
    assert result.pdf_bytes == source
    assert result.report["unsupported_pages"] == [1]


def test_inline_image_is_not_tokenized_as_text():
    with pytest.raises(UnsupportedContent):
        parse_instructions(b"q BI /W 1 /H 1 /BPC 8 /CS /G ID (Preview) Tj EI Q")


def test_comments_are_not_replaced():
    raw = b"% BT (Preview) Tj ET\nBT /F 90 Tf (Preview) Tj ET\n% keep"
    patches = find_patches(raw, "Preview")
    assert len(patches) == 1
    start, end, replacement = patches[0]
    revised = raw[:start] + replacement + raw[end:]
    assert revised.startswith(b"% BT (Preview) Tj ET")
    assert revised.endswith(b"% keep")


def test_clipping_text_not_edited():
    raw = b"q BT /F 90 Tf 7 Tr (Preview) Tj ET Q"
    assert not find_patches(raw, "Preview")


def test_unbalanced_state_rejected():
    with pytest.raises(UnsupportedContent):
        find_patches(b"q BT (Preview) Tj ET", "Preview")


def test_nested_form_left_unchanged():
    source = pymupdf.open(stream=make_pdf(), filetype="pdf")
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    page.show_pdf_page(page.rect, source, 0)
    data = doc.tobytes()
    doc.close()
    source.close()
    result = clean(data)
    assert result.report["unsupported_pages"] == [1]
    assert result.pdf_bytes == data


def test_raster_page_left_unchanged():
    source = pymupdf.open(stream=make_pdf(), filetype="pdf")
    pix = source[0].get_pixmap()
    doc = pymupdf.open()
    page = doc.new_page(width=612, height=792)
    page.insert_image(page.rect, pixmap=pix)
    data = doc.tobytes()
    doc.close()
    source.close()
    assert clean(data).pdf_bytes == data


def test_no_overwrite(tmp_path):
    dest = tmp_path / "file.pdf"
    save_new(dest, b"original")
    with pytest.raises(CleanerError):
        save_new(dest, b"replacement")
    assert dest.read_bytes() == b"original"


def test_input_path_cannot_be_output(tmp_path):
    path = tmp_path / "file.pdf"
    with pytest.raises(CleanerError):
        save_new(path, b"x", source=path)
    assert not path.exists()


def test_idempotent():
    result = clean(make_pdf())
    again = clean(result.pdf_bytes)
    assert again.report["removed_count"] == 0
    assert again.pdf_bytes == result.pdf_bytes


def test_password_and_encryption_preserved():
    with open_pdf(make_pdf()) as doc:
        data = doc.tobytes(encryption=pymupdf.PDF_ENCRYPT_AES_256,
                           user_pw="open-test", owner_pw="owner-test")
    with pytest.raises(PasswordNeeded):
        clean(data)
    result = clean(data, password="open-test")
    assert result.report["removed_count"] == 1
    with pytest.raises(PasswordNeeded):
        open_pdf(result.pdf_bytes)
    with open_pdf(result.pdf_bytes, "open-test") as doc:
        assert len(doc) == 1


def test_signature_fields_block_editing():
    with open_pdf(make_pdf()) as doc:
        root = doc.pdf_catalog()
        doc.xref_set_key(root, "AcroForm", "<< /Fields [] /SigFlags 3 >>")
        data = doc.tobytes()
    with pytest.raises(CleanerError, match="Signed"):
        clean(data)


@pytest.mark.parametrize("sigflags", ["null", "0"])
@pytest.mark.parametrize("inherited", [False, True])
@pytest.mark.parametrize("field_type", ["Sig", "Tx"])
def test_field_type_checked_without_signature_flags(sigflags, inherited, field_type):
    with open_pdf(make_pdf()) as doc:
        page = doc[0]
        widget = doc.get_new_xref()
        doc.update_object(widget, (
            f"<< /Type /Annot /Subtype /Widget /Rect [20 650 200 700] "
            f"/P {page.xref} 0 R >>"
        ))
        field = widget
        if inherited:
            field = doc.get_new_xref()
            doc.update_object(field, f"<< /Kids [{widget} 0 R] >>")
            doc.xref_set_key(widget, "Parent", f"{field} 0 R")
        doc.xref_set_key(field, "FT", f"/{field_type}")
        doc.xref_set_key(field, "T", "(Approval)")
        doc.xref_set_key(page.xref, "Annots", f"[{widget} 0 R]")
        doc.xref_set_key(doc.pdf_catalog(), "AcroForm", (
            f"<< /Fields [{field} 0 R] /SigFlags {sigflags} >>"
        ))
        data = doc.tobytes()

    with open_pdf(data) as doc:
        assert doc.get_sigflags() <= 0
        actual_widget = next(doc[0].widgets())
        expected_type = (pymupdf.PDF_WIDGET_TYPE_SIGNATURE if field_type == "Sig"
                         else pymupdf.PDF_WIDGET_TYPE_TEXT)
        assert actual_widget.field_type == expected_type
    assert analyze(data)["signed_or_signature_fields"] == (field_type == "Sig")
    if field_type == "Sig":
        with pytest.raises(CleanerError, match="signature fields"):
            clean(data)
    else:
        assert clean(data).report["removed_count"] == 1


def test_invalid_pdf_and_target():
    with pytest.raises(CleanerError):
        clean(b"not a PDF")
    with pytest.raises(CleanerError):
        clean(make_pdf(), target="")


def test_analyze_is_read_only():
    data = make_pdf()
    assert analyze(data)["visible_candidate_count"] == 1
    assert clean(data).report["input_sha256"] == analyze(data)["input_sha256"]

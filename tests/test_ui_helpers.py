import pytest
from preview_cleaner.ui_helpers import format_pdf_date, page_number, result_notice

@pytest.mark.parametrize('value,expected', [('4',3),('999',9),('-2',0),('abc',2),('',2)])
def test_page_entry_clamps_or_preserves(value, expected):
    assert page_number(value, 10, 2) == expected

@pytest.mark.parametrize('value,expected', [
    ('D:20261001120000Z','01 Oct 2026, 12:00:00 UTC+0000'),
    ("D:20261001120000+07'00'",'01 Oct 2026, 12:00:00 UTC+0700'),
    ('D:20261001120000','01 Oct 2026, 12:00:00 (time zone unspecified)'),
    ('D:20261301120000Z','D:20261301120000Z'),
    ('D:2026','D:2026'),('', 'Not specified')])
def test_pdf_dates_do_not_invent_timezone_or_missing_fields(value, expected):
    assert format_pdf_date(value) == expected

def test_warning_remains_visible_when_navigating_away_from_unsupported_page():
    report = {'unsupported_pages':[2], 'removed_count':1, 'target':'Preview'}
    assert 'Page 2:' in result_notice(report, 1)[0]
    assert 'pages 2' in result_notice(report, 0)[0]
    assert result_notice(report, 0)[1]
    assert result_notice(None, 0) == ('', False)

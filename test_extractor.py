"""Self-check for the extractor + output encoding. Run: python test_extractor.py"""
import json
import tempfile
from pathlib import Path

from scrapling.parser import Selector

from main import save_output
from scrapers.example import _faq_answers, _schema_types, extract


def test_extract():
    html = """<html><head><meta charset="utf-8"><title>T</title></head><body>
    <main><p>We\u2019ve got smart quotes \u2013 and an em dash.</p></main>
    <table><tr><td>cell\u00a0one</td></tr></table>
    <ul><li>a</li><li>b</li></ul>
    <ol><li>one</li></ol>
    <dl><dt>term</dt><dd>def</dd></dl>
    <time datetime="2026-08-26">today</time>
    </body></html>"""
    sel = Selector(content=html)

    main_txt = extract(sel, "main")
    assert main_txt == ["We\u2019ve got smart quotes \u2013 and an em dash."], main_txt

    table_txt = extract(sel, "table")
    assert table_txt and "cell\u00a0one" in table_txt[0], table_txt

    assert extract(sel, "ul li::text") == ["a", "b"]
    assert extract(sel, "ol li::text") == ["one"]
    assert extract(sel, "dt::text,dd::text") == ["term", "def"]
    assert extract(sel, "time::attr(datetime)") == ["2026-08-26"]
    print("extract() ok")


def test_jsonld():
    blocks = [json.dumps({
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebSite", "name": "x"},
            {"@type": "FAQPage", "mainEntity": [
                {"@type": "Question", "name": "Q1?",
                 "acceptedAnswer": {"@type": "Answer", "text": "A1\u2019s"}},
                {"@type": "Question", "name": "Q2?",
                 "acceptedAnswer": {"@type": "Answer", "text": "A2"}},
            ]},
        ],
    }, ensure_ascii=False)]
    assert _schema_types(blocks) == ["Answer", "FAQPage", "Question", "WebSite"], _schema_types(blocks)
    assert _faq_answers(blocks) == ["A1\u2019s", "A2"], _faq_answers(blocks)

    list_type = [json.dumps({
        "@type": ["WebPage", "FAQPage"],
        "mainEntity": [
            {"@type": "Question", "name": "Q?",
             "acceptedAnswer": {"@type": "Answer", "text": "<p>Answer with <a href=\"/x\">a link</a>.</p>"}},
        ],
    }, ensure_ascii=False)]
    assert _faq_answers(list_type) == ["Answer with a link."], _faq_answers(list_type)

    assert _faq_answers(["not json"]) == []
    assert _schema_types(["not json"]) == []
    print("jsonld parsing ok")


def test_save_output():
    result = {"data": {"first_p": ["We\u2019ve helped \u2013 clean"]}}
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "t.json"
        save_output(out, result)
        raw = out.read_bytes()
        assert b"\xe2\x80\x99" in raw, "file is not UTF-8"
        back = json.loads(out.read_text(encoding="utf-8"))
        assert back["data"]["first_p"] == ["We\u2019ve helped \u2013 clean"]
    print("save_output utf-8 ok")


if __name__ == "__main__":
    test_extract()
    test_jsonld()
    test_save_output()
    print("ALL PASS")

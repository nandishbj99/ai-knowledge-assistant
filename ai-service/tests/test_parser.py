import tempfile
import os
from app.services.parser import DocumentParser

def test_markdown_table_formatting():
    table = [
        ["Product", "Q1 Sales", "Growth"],
        ["AI Assistant", "$1.2M", "+24%"],
        ["Cloud Storage", "$3.4M", "+12%"]
    ]
    md = DocumentParser._format_markdown_table(table)
    assert md is not None
    assert "| Product | Q1 Sales | Growth |" in md
    assert "| --- | --- | --- |" in md
    assert "| AI Assistant | $1.2M | +24% |" in md

def test_parse_text_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("Line 1: Knowledge Assistant Architecture.\nLine 2: Spec-driven development.")
        temp_path = f.name

    try:
        pages = DocumentParser.parse(temp_path)
        assert len(pages) == 1
        assert pages[0]["page_number"] == 1
        assert "Knowledge Assistant Architecture" in pages[0]["text"]
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

if __name__ == "__main__":
    test_markdown_table_formatting()
    test_parse_text_file()
    print("=== ALL PARSER TESTS PASSED SUCCESSFULLY! ===")

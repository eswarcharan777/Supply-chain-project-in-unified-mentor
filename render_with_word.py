"""Fallback DOCX-to-PDF renderer when the bundled LibreOffice runtime is unavailable."""

from __future__ import annotations

import sys
from pathlib import Path

import win32com.client


WD_EXPORT_FORMAT_PDF = 17


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: render_with_word.py INPUT.docx OUTPUT.pdf")
    source = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    word = win32com.client.DispatchEx("Word.Application")
    word.Visible = False
    word.DisplayAlerts = 0
    document = None
    try:
        document = word.Documents.Open(str(source), ReadOnly=True)
        document.ExportAsFixedFormat(str(output), WD_EXPORT_FORMAT_PDF)
    finally:
        if document is not None:
            document.Close(False)
        word.Quit()


if __name__ == "__main__":
    main()

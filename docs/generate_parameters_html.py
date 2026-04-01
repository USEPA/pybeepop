from __future__ import annotations

import csv
import html
from pathlib import Path

import pandas as pd

DOCS_DIR = Path(__file__).resolve().parent
CSV_PATH = DOCS_DIR / "BeePop_exposed_parameters.csv"
HTML_PATH = DOCS_DIR / "parameters.html"
HERO_FRAGMENT_PATH = DOCS_DIR / "_hero_fragment.html"


def read_note(csv_path: Path) -> str:
    with csv_path.open(newline="", encoding="utf-8-sig") as csv_file:
        reader = csv.reader(csv_file)
        first_row = next(reader)
    return first_row[0].strip()


def build_html_table(csv_path: Path) -> str:
    dataframe = pd.read_csv(csv_path, skiprows=1, keep_default_na=False)
    dataframe.columns = [column.strip() for column in dataframe.columns]
    return dataframe.to_html(
        index=False,
        classes="parameter-table",
        border=0,
        escape=True,
        justify="left",
    )


def build_hero(active_page: str) -> str:
    fragment = HERO_FRAGMENT_PATH.read_text(encoding="utf-8")
    return (
        fragment.replace("__ACTIVE_HOME__", " active" if active_page == "home" else "")
        .replace("__ACTIVE_INTRO__", " active" if active_page == "intro" else "")
        .replace("__ACTIVE_PARAMS__", " active" if active_page == "params" else "")
    )


def build_document(note_text: str, table_html: str) -> str:
    escaped_note = html.escape(note_text)
    hero_html = build_hero("params")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>BeePop+ Exposed Parameters</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="styles.css">
</head>
<body>
    {hero_html}
    <div class="container wide">
        <div class="note">{escaped_note}</div>
        <div class="table-wrap">
            {table_html}
        </div>
        <p class="footer-link">For the full list and latest details, see <a href="https://github.com/USEPA/pybeepop/blob/main/docs/BeePop_exposed_parameters.csv">BeePop_exposed_parameters.csv on GitHub</a>.</p>
    </div>
</body>
</html>
"""


def main() -> None:
    note_text = read_note(CSV_PATH)
    table_html = build_html_table(CSV_PATH)
    HTML_PATH.write_text(build_document(note_text, table_html), encoding="utf-8")


if __name__ == "__main__":
    main()

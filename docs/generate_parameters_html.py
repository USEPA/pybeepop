from __future__ import annotations

import csv
import html
from pathlib import Path

import pandas as pd


DOCS_DIR = Path(__file__).resolve().parent
CSV_PATH = DOCS_DIR / "BeePop_exposed_parameters.csv"
HTML_PATH = DOCS_DIR / "parameters.html"


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


def build_document(note_text: str, table_html: str) -> str:
    escaped_note = html.escape(note_text)
    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"utf-8\">
    <title>BeePop+ Exposed Parameters</title>
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">
    <style>
        body {{
            font-family: 'Segoe UI', 'Roboto', Arial, sans-serif;
            margin: 0;
            padding: 0;
            background: #f8fafc;
            color: #1f2937;
        }}
        .container {{
            max-width: 1320px;
            margin: 40px auto;
            background: #fff;
            border-radius: 12px;
            box-shadow: 0 4px 24px rgba(60, 72, 88, 0.10);
            padding: 32px 24px 24px 24px;
        }}
        h1 {{
            color: #1a202c;
            font-size: 2.2rem;
            margin-bottom: 24px;
        }}
        .note {{
            background: #fffbe6;
            border-left: 4px solid #fec44f;
            padding: 12px 18px;
            margin-bottom: 24px;
            color: #444;
        }}
        .table-wrap {{
            overflow-x: auto;
        }}
        table.parameter-table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 24px;
            font-size: 0.96rem;
        }}
        table.parameter-table th,
        table.parameter-table td {{
            border: 1px solid #e2e8f0;
            padding: 8px 10px;
            text-align: left;
            vertical-align: top;
        }}
        table.parameter-table th {{
            background: #fec44f;
            color: #222;
            font-weight: 600;
            position: sticky;
            top: 0;
        }}
        table.parameter-table tbody tr:nth-child(even) {{
            background: #f9fafb;
        }}
        .footer-link {{
            color: #888;
            font-size: 0.98rem;
        }}
        .back-link {{
            color: #2563eb;
        }}
        @media (max-width: 700px) {{
            .container {{
                padding: 10px 2vw;
            }}
            table.parameter-table,
            table.parameter-table th,
            table.parameter-table td {{
                font-size: 0.92rem;
            }}
        }}
    </style>
</head>
<body>
    <div class=\"container\">
        <h1>BeePop+ Exposed Parameters</h1>
        <div class=\"note\">{escaped_note}</div>
        <div class=\"table-wrap\">
            {table_html}
        </div>
        <p class=\"footer-link\">For the full list and latest details, see <a href=\"https://github.com/USEPA/pybeepop/blob/main/docs/BeePop_exposed_parameters.csv\">BeePop_exposed_parameters.csv on GitHub</a>.</p>
        <a class=\"back-link\" href=\"index.html\">&larr; Back to Documentation Home</a>
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
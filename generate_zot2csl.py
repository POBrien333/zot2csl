#!/usr/bin/env python3
"""
Generate docs/index.html with a table of Zotero → CSL mappings.

Creators are inserted right after the "title" field where possible.
"""

import sys
import requests
from datetime import datetime
from pathlib import Path

SCHEMA_URL = "https://raw.githubusercontent.com/zotero/zotero-schema/master/schema.json"
LOCALE = "en-US"
OUTPUT_FILE = Path("docs/index.html")

def fetch_schema(url=SCHEMA_URL):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Error fetching schema:", e, file=sys.stderr)
        return {}

def normalize_field_entry(field_entry):
    if isinstance(field_entry, str):
        return field_entry
    if isinstance(field_entry, dict):
        return field_entry.get("field") or field_entry.get("baseField") or str(field_entry)
    return str(field_entry)

def normalize_creator_entry(creator_entry):
    if isinstance(creator_entry, str):
        return creator_entry, False
    if isinstance(creator_entry, dict):
        return (
            creator_entry.get("creatorType") or creator_entry.get("type") or str(creator_entry),
            bool(creator_entry.get("primary", False)),
        )
    return str(creator_entry), False

def merge_fields_and_creators(item_type_schema, fields_map, creators_map):
    fields_list = item_type_schema.get("fields", [])
    creators_list = item_type_schema.get("creatorTypes", [])
    merged = []
    title_seen = False

    for field_entry in fields_list:
        field_key = normalize_field_entry(field_entry)
        field_label = fields_map.get(field_key, field_key)
        merged.append(("field", field_key, field_label))

        if field_key == "title":
            title_seen = True
            for creator_entry in creators_list:
                c_key, primary = normalize_creator_entry(creator_entry)
                c_label = creators_map.get(c_key, c_key)
                display_key = f"{c_key} (author)" if primary else c_key
                merged.append(("creator", display_key, c_label))

    if not title_seen and creators_list:
        for creator_entry in creators_list:
            c_key, primary = normalize_creator_entry(creator_entry)
            c_label = creators_map.get(c_key, c_key)
            display_key = f"{c_key} (author)" if primary else c_key
            merged.append(("creator", display_key, c_label))

    return merged

def generate_html(schema, schema_url, schema_version):
    current_date = datetime.now().strftime("%Y-%m-%d")

    locales = schema.get("locales", {})
    loc = locales.get(LOCALE, {})
    fields_map = loc.get("fields", {})
    creators_map = loc.get("creatorTypes", {})
    item_types_map = loc.get("itemTypes", {})

    item_types = schema.get("itemTypes", [])

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Zotero to CSL Mappings</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <h1>Zotero to CSL Mappings</h1>
  <p>Extracted on <strong>{current_date}</strong> from <strong>version {schema_version}</strong> of the Zotero schema at
  <a href="{schema_url}">{schema_url}</a></p>
  <div class="toc">
    <h2>Table of Contents</h2>
    <ul>
"""

    # TOC
    for item_schema in item_types:
        item_key = item_schema.get("itemType")
        if not item_key:
            continue
        item_label = item_types_map.get(item_key, item_key)
        html += f'      <li><a href="#{item_key}">{item_label} ({item_key})</a></li>\n'

    html += """    </ul>
  </div>
"""

    # Sections
    for item_schema in item_types:
        item_key = item_schema.get("itemType")
        if not item_key:
            continue
        item_label = item_types_map.get(item_key, item_key)
        merged = merge_fields_and_creators(item_schema, fields_map, creators_map)

        html += f"""  <div class="item-type" id="{item_key}">
    <h2>{item_label} ({item_key})</h2>
    <table>
      <tr>
        <th>Kind</th>
        <th>Zotero Key</th>
        <th>UI Label</th>
      </tr>
"""
        for kind, key, label in merged:
            html += f"""      <tr>
        <td>{kind}</td>
        <td>{key}</td>
        <td>{label}</td>
      </tr>
"""
        html += "    </table>\n  </div>\n"

    html += """</body>
</html>
"""
    return html

def main():
    schema = fetch_schema()
    if not schema:
        sys.exit(1)

    schema_version = schema.get("version", "unknown")

    html = generate_html(schema, SCHEMA_URL, schema_version)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ HTML file generated at {OUTPUT_FILE}")

if __name__ == "__main__":
    main()

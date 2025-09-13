import json
import requests
from datetime import datetime
import os

SCHEMA_URL = "https://raw.githubusercontent.com/zotero/zotero-schema/master/schema.json"
LOCALE = "en-US"

# Function to load the schema
def load_schema():
    try:
        r = requests.get(SCHEMA_URL, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Error fetching schema:", e)
        return {}

# Normalize field entry
def normalize_field_entry(field_entry):
    if isinstance(field_entry, str):
        return field_entry
    if isinstance(field_entry, dict):
        return field_entry.get("field") or field_entry.get("baseField") or str(field_entry)
    return str(field_entry)

# Normalize creator entry
def normalize_creator_entry(creator_entry):
    if isinstance(creator_entry, str):
        return creator_entry, False
    if isinstance(creator_entry, dict):
        return creator_entry.get("creatorType") or creator_entry.get("type") or str(creator_entry), bool(creator_entry.get("primary", False))
    return str(creator_entry), False

# Merge fields and creators
def merge_fields_and_creators(item_type_schema, fields_map, creators_map, csl_fields):
    merged = []
    title_seen = False
    fields_list = item_type_schema.get("fields", [])
    creators_list = item_type_schema.get("creatorTypes", [])

    for field_entry in fields_list:
        field_key = normalize_field_entry(field_entry)
        field_label = fields_map.get(field_key, field_key)

        # CSL variable lookup
        csl_variable = ""
        for category, fields in csl_fields.items():
            if isinstance(fields, dict):
                for sub_field, csl_vars in fields.items():
                    if field_key in csl_vars:
                        csl_variable = sub_field
                        break
                if csl_variable:
                    break
            elif field_key in fields:
                csl_variable = category
                break

        merged.append(("field", field_key, field_label, csl_variable))

        if field_key == "title":
            title_seen = True
            for creator_entry in creators_list:
                c_key, primary = normalize_creator_entry(creator_entry)
                c_label = creators_map.get(c_key, c_key)
                display_key = f"{c_key} (author)" if primary else c_key

                # CSL variable for creator
                csl_var = ""
                if c_key in csl_fields.get("names", {}):
                    csl_var = csl_fields["names"][c_key]
                elif primary:
                    csl_var = "author"

                merged.append(("creator", display_key, c_label, csl_var))

    if not title_seen and creators_list:
        for creator_entry in creators_list:
            c_key, primary = normalize_creator_entry(creator_entry)
            c_label = creators_map.get(c_key, c_key)
            display_key = f"{c_key} (author)" if primary else c_key
            csl_var = ""
            if c_key in csl_fields.get("names", {}):
                csl_var = csl_fields["names"][c_key]
            elif primary:
                csl_var = "author"
            merged.append(("creator", display_key, c_label, csl_var))

    return merged

# Generate HTML
def generate_html(schema):
    current_date = datetime.now().strftime("%Y-%m-%d")
    locales = schema.get("locales", {}).get(LOCALE, {})
    fields_map = locales.get("fields", {})
    creators_map = locales.get("creatorTypes", {})
    item_types_map = locales.get("itemTypes", {})
    item_types = schema.get("itemTypes", [])
    csl_fields = schema.get("csl", {})

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Zotero to CSL Mappings</title>
<link rel="stylesheet" type="text/css" href="style.css">
</head>
<body>
<h1>Zotero to CSL Mappings</h1>
<p>Extracted on <strong>{current_date}</strong> from <strong>version {schema.get("version","unknown")}</strong> of the Zotero schema found at <a href="{SCHEMA_URL}">{SCHEMA_URL}</a></p>
<div class="toc">
<h2>Table of Contents</h2>
<ul>
'''

    # Table of Contents
    for item in item_types:
        item_key = item.get("itemType")
        if not item_key:
            continue
        item_label = item_types_map.get(item_key, item_key)

        # CSL type mapping
        csl_type = []
        for ctype, zotero_types in csl_fields.get("types", {}).items():
            if item_key in zotero_types:
                csl_type.append(ctype)
        if not csl_type:
            csl_type = ["No CSL mapping found"]
        csl_type_str = ", ".join(csl_type)
        html += f'  <li><a href="#{item_key}">{item_label} → {csl_type_str}</a></li>\n'

    html += '</ul>\n</div>\n'

    # Item tables
    for item in item_types:
        item_key = item.get("itemType")
        if not item_key:
            continue
        item_label = item_types_map.get(item_key, item_key)
        csl_type = []
        for ctype, zotero_types in csl_fields.get("types", {}).items():
            if item_key in zotero_types:
                csl_type.append(ctype)
        if not csl_type:
            csl_type = ["No CSL mapping found"]
        csl_type_str = ", ".join(csl_type)

        html += f'<div class="item-type" id="{item_key}">\n<h2>{item_label} → {csl_type_str}</h2>\n<table>\n<tr><th>UI Label</th><th>Zotero Field</th><th>CSL Variable</th></tr>\n'

        merged = merge_fields_and_creators(item, fields_map, creators_map, csl_fields)
        for kind, key, label, csl_var in merged:
            html += f'<tr><td>{label}</td><td>{key}</td><td>{csl_var}</td></tr>\n'

        html += '</table>\n</div>\n'

    html += '</body>\n</html>'
    return html

# Main execution
if __name__ == "__main__":
    os.makedirs("docs", exist_ok=True)
    schema = load_schema()
    html_output = generate_html(schema)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html_output)
    print("HTML file has been generated: docs/index.html")

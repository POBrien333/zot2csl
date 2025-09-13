import json
import requests
from datetime import datetime
import os  # <- added to ensure docs/ exists

SCHEMA_URL = "https://raw.githubusercontent.com/zotero/zotero-schema/master/schema.json"
LOCALE = "en-US"

# --- Helper functions from your working console script ---

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
        return creator_entry.get("creatorType") or creator_entry.get("type") or str(creator_entry), bool(creator_entry.get("primary", False))
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
            # Insert creators immediately after the title
            for creator_entry in creators_list:
                c_key, primary = normalize_creator_entry(creator_entry)
                c_label = creators_map.get(c_key, c_key)
                display_key = f"{c_key} (author)" if primary else c_key
                merged.append(("creator", display_key, c_label))

    # Fallback: append creators at the end if title missing
    if not title_seen and creators_list:
        for creator_entry in creators_list:
            c_key, primary = normalize_creator_entry(creator_entry)
            c_label = creators_map.get(c_key, c_key)
            display_key = f"{c_key} (author)" if primary else c_key
            merged.append(("creator", display_key, c_label))

    return merged

# --- Existing HTML generator functions (only change: creator handling) ---

def load_schema_from_url(url):
    print(f"Fetching schema from {url}")
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        schema = response.json()
        print("Schema top-level keys:", list(schema.keys()))
        return schema
    except requests.RequestException as e:
        print(f"Error fetching schema: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return {}

def get_item_type_label(schema, item_type):
    locales = schema.get('locales', {})
    en_us = locales.get(LOCALE, {})
    item_types = en_us.get('itemTypes', {})
    return item_types.get(item_type, item_type)

def get_csl_mapping_for_zotero_item_type(schema, item_type):
    csl_types = schema.get('csl', {}).get('types', {})
    for csl_type, zotero_types in csl_types.items():
        if item_type in zotero_types:
            return [csl_type]
    return ["No CSL mapping found"]

# --- Main HTML generator ---

def generate_html(schema, schema_url, schema_version):
    current_date = datetime.now().strftime("%Y-%m-%d")
    item_types = schema.get('itemTypes', [])
    csl_fields = schema.get('csl', {}).get('fields', {})

    # Get locale maps
    loc = schema.get('locales', {}).get(LOCALE, {})
    fields_map = loc.get("fields", {})
    creators_map = loc.get("creatorTypes", {})

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
    <p>Extracted on <strong>{current_date}</strong> from <strong>version {schema_version}</strong> of the Zotero schema found at <a href="{schema_url}">{schema_url}</a></p>
    <div class="toc">
        <h2>Table of Contents</h2>
        <ul>
'''
    for item in item_types:
        item_type = item['itemType']
        item_type_label = get_item_type_label(schema, item_type)
        csl_type = get_csl_mapping_for_zotero_item_type(schema, item_type)
        csl_type_str = ', '.join(csl_type)
        html += f'            <li><a href="#{item_type}">{item_type_label} → {csl_type_str}</a></li>\n'

    html += '''        </ul>
    </div>
'''

    for item in item_types:
        item_type = item['itemType']
        item_type_label = get_item_type_label(schema, item_type)
        csl_type = get_csl_mapping_for_zotero_item_type(schema, item_type)
        csl_type_str = ', '.join(csl_type)
        html += f'''    <div class="item-type" id="{item_type}">
        <h2>{item_type_label} → {csl_type_str}</h2>
        <table>
            <tr>
                <th>UI Label</th>
                <th>Zotero Field</th>
                <th>CSL Variable</th>
            </tr>
'''
        # Merge fields and creators
        merged_rows = merge_fields_and_creators(item, fields_map, creators_map)
        for kind, key, label in merged_rows:
            # Attempt to get CSL variable for fields; empty for creators
            csl_var = ''
            if kind == "field" and key in csl_fields:
                csl_var = key
            row_class = 'creator-row' if kind == 'creator' else ''
            html += f'''            <tr class="{row_class}">
                <td>{label}</td>
                <td>{key}</td>
                <td>{csl_var}</td>
            </tr>
'''

        html += '''        </table>
    </div>
'''
    html += '''</body>
</html>
'''
    return html

# --- Main script ---

schema = load_schema_from_url(SCHEMA_URL)
if not schema:
    exit(1)

schema_version = schema.get("version", "unknown version")
html_output = generate_html(schema, SCHEMA_URL, schema_version)

# --- Ensure docs directory exists (GitHub Pages) ---
os.makedirs("docs", exist_ok=True)

# Save the HTML output
with open("docs/index.html", "w", encoding="utf-8") as f:
    f.write(html_output)

print("HTML file has been generated: docs/index.html")

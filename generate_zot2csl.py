import json
import requests
from datetime import datetime

# Function to load the schema from a URL
def load_schema_from_url(url):
    print(f"Fetching schema from {url}")
    try:
        response = requests.get(url, timeout=10)
        print(f"HTTP Status Code: {response.status_code}")
        response.raise_for_status()  # Raise for bad HTTP responses
        schema = response.json()
        print("Schema top-level keys:", list(schema.keys()))
        if 'locales' in schema:
            print("Locales section found. en-US itemTypes:", list(schema.get('locales', {}).get('en-US', {}).get('itemTypes', {}).keys())[:5], "...")
        else:
            print("Error: 'locales' key not found in schema")
        return schema
    except requests.RequestException as e:
        print(f"Error fetching schema: {e}")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        return {}

# Function to get the en-US label for a Zotero item type
def get_item_type_label(schema, item_type):
    locales = schema.get('locales', {})
    en_us = locales.get('en-US', {})
    item_types = en_us.get('itemTypes', {})
    label = item_types.get(item_type, item_type)
    print(f"Looking up label for {item_type}: {label}")
    return label

# Function to get CSL mapping for a given Zotero item type
def get_csl_mapping_for_zotero_item_type(schema, item_type):
    csl_types = schema.get('csl', {}).get('types', {})
    for csl_type, zotero_types in csl_types.items():
        if item_type in zotero_types:
            return [csl_type]
    return ["No CSL mapping found"]

# UI labels for Zotero fields
field_ui_labels = {
    "title": "Title",
    "abstractNote": "Abstract Note",
    "bookTitle": "Book Title",
    "publicationTitle": "Publication Title",
    "series": "Series",
}

# Special field overrides
special_field_overrides = {
    "bookTitle": "publicationTitle"
}

# Function to generate the HTML based on the schema
def generate_html(schema, schema_url, schema_version):
    current_date = datetime.now().strftime("%Y-%m-%d")
    item_types = schema.get('itemTypes', [])
    csl_fields = schema.get('csl', {}).get('fields', {})
    
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
        for field in item['fields']:
            zotero_field = field['field']
            zotero_baseField = field.get('baseField', zotero_field)
            lookup_field = special_field_overrides.get(zotero_field, zotero_baseField)
            ui_label = field_ui_labels.get(zotero_field, zotero_field)
            csl_variable = ''
            for category, fields in csl_fields.items():
                if isinstance(fields, dict):
                    for sub_field, csl_var in fields.items():
                        if lookup_field in csl_var:
                            csl_variable = sub_field
                            break
                    if csl_variable:
                        break
                elif lookup_field in fields:
                    csl_variable = category
                    break
            html += f'''            <tr>
                <td>{ui_label}</td>
                <td>{zotero_field}</td>
                <td>{csl_variable}</td>
            </tr>
'''
        html += '''        </table>
    </div>
'''
    html += '''</body>
</html>
'''
    return html

# URL of the Zotero schema
schema_url = "https://raw.githubusercontent.com/zotero/zotero-schema/master/schema.json"

# Fetch the schema
schema = load_schema_from_url(schema_url)

# Get the schema version
schema_version = schema.get("version", "unknown version")

# Generate the HTML output
html_output = generate_html(schema, schema_url, schema_version)

# Write to an HTML file
with open("index.html", "w", encoding="utf-8") as file:
    file.write(html_output)

print("HTML file has been generated: index.html")

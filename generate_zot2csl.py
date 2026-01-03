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

# Function to get the en-US label for a Zotero creator type
def get_creator_type_label(schema, creator_type):
    locales = schema.get('locales', {})
    en_us = locales.get('en-US', {})
    creator_types = en_us.get('creatorTypes', {})
    label = creator_types.get(creator_type, creator_type)
    return label

# Function to get the en-US label for a Zotero field
def get_field_label(schema, field_name):
    locales = schema.get('locales', {})
    en_us = locales.get('en-US', {})
    fields = en_us.get('fields', {})
    label = fields.get(field_name, field_name)
    return label

# Function to get CSL mapping for a given Zotero item type
def get_csl_mapping_for_zotero_item_type(schema, item_type):
    csl_types = schema.get('csl', {}).get('types', {})
    for csl_type, zotero_types in csl_types.items():
        if item_type in zotero_types:
            return [csl_type]
    return ["-"]  # ✅ replaced text with dash

# Function to get CSL mapping for a given Zotero creator type
def get_csl_mapping_for_zotero_creator_type(schema, creator_type):
    csl_names = schema.get('csl', {}).get('names', {})
    return csl_names.get(creator_type, "-")  # ✅ replaced text with dash

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

        # ✅ creators at the top, primary mapped to CSL "author"
        if 'creatorTypes' in item and item['creatorTypes']:
            for ct in item['creatorTypes']:
                creator_type = ct['creatorType']
                creator_label = get_creator_type_label(schema, creator_type)
                if ct.get('primary'):
                    csl_var = get_csl_mapping_for_zotero_creator_type(schema, 'author')
                else:
                    csl_var = get_csl_mapping_for_zotero_creator_type(schema, creator_type)
                html += f'''            <tr class="creator-row">
                <td>{creator_label}</td>
                <td>{creator_type}</td>
                <td>{csl_var}</td>
            </tr>
'''

        # then list the fields
        for field in item['fields']:
            zotero_field = field['field']
            zotero_baseField = field.get('baseField', zotero_field)
            lookup_field = zotero_baseField
            ui_label = get_field_label(schema, zotero_field)
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
            if not csl_variable:
                csl_variable = "-"  # ✅ replaced fallback with dash
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

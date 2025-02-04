import json
import requests
from datetime import datetime

# Function to load the schema from a URL
def load_schema_from_url(url):
    response = requests.get(url)
    response.raise_for_status()  # Will raise an exception for bad HTTP responses
    return response.json()

# Function to get CSL mapping for a given Zotero item type
def get_csl_mapping_for_zotero_item_type(schema, item_type):
    # Extract CSL types from the schema
    csl_types = schema.get('csl', {}).get('types', {})
    
    # Reverse mapping: Check if the item_type is a value for any CSL type
    for csl_type, zotero_types in csl_types.items():
        if item_type in zotero_types:
            return [csl_type]  # Return the matching CSL type
    
    # If no CSL mapping is found, return a default message
    return ["No CSL mapping found"]

# In this example, we assume some UI labels exist for Zotero fields.
# You can extend or modify this dictionary as needed.
field_ui_labels = {
    "title": "Title",
    "abstractNote": "Abstract Note",
    "bookTitle": "Book Title",
    "publicationTitle": "Publication Title",
    "series": "Series",
    # ... add additional mappings as desired
}

# A special overrides dictionary to ensure that, for example,
# if a field like "bookTitle" should really be looked up as "publicationTitle"
special_field_overrides = {
    "bookTitle": "publicationTitle"
    # Add any additional special cases here.
}

# Function to generate the HTML based on the schema
def generate_html(schema, schema_url, schema_version):
    # Get the current date for the output
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Extract relevant parts of the schema
    item_types = schema.get('itemTypes', [])
    csl_fields = schema.get('csl', {}).get('fields', {})  # CSL fields to variables

    # Initialize the HTML structure
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Zotero to CSL Mappings</title>
    <!-- Link to the external CSS file -->
    <link rel="stylesheet" type="text/css" href="style.css">
</head>
<body>
    <h1>Zotero to CSL Mappings</h1>
    <p>Extracted on <strong>{current_date}</strong> from <strong>version {schema_version}</strong> of the Zotero schema found at <a href="{schema_url}">{schema_url}</a></p>
    <div class="toc">
        <h2>Table of Contents</h2>
        <ul>
'''

    # Generate the Table of Contents with CSL mapping
    for item in item_types:
        item_type = item['itemType']
        # Lookup CSL types for the item type
        csl_type = get_csl_mapping_for_zotero_item_type(schema, item_type)
        # Join multiple CSL types with a comma if needed
        csl_type_str = ', '.join(csl_type)
        html += f'            <li><a href="#{item_type}">{item_type} → {csl_type_str}</a></li>\n'
    
    html += '''        </ul>
    </div>
'''

    # Generate details for each item type with the correct CSL mapping in the headings
    for item in item_types:
        item_type = item['itemType']
        csl_type = get_csl_mapping_for_zotero_item_type(schema, item_type)
        csl_type_str = ', '.join(csl_type)
        html += f'''    <div class="item-type" id="{item_type}">
        <h2>{item_type} → {csl_type_str}</h2>
        <table>
            <tr>
                <th>UI Label</th>
                <th>Zotero Field</th>
                <th>CSL Variable</th>
            </tr>
'''
        # Process each field for the current item type
        for field in item['fields']:
            zotero_field = field['field']
            # Use baseField if available, otherwise fall back to the original field
            zotero_baseField = field.get('baseField', zotero_field)
            # Use special override if defined
            lookup_field = special_field_overrides.get(zotero_field, zotero_baseField)
            ui_label = field_ui_labels.get(zotero_field, zotero_field)
            csl_variable = ''

            # Lookup the CSL variable from the CSL fields mapping
            for category, fields in csl_fields.items():
                if isinstance(fields, dict):
                    for sub_field, csl_var in fields.items():
                        # Check if the lookup_field is found in the CSL mapping string
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

# Fetch the schema from the URL
schema = load_schema_from_url(schema_url)

# Get the schema version (or a default message if not present)
schema_version = schema.get("version", "unknown version")

# Generate the HTML output
html_output = generate_html(schema, schema_url, schema_version)

# Write to an HTML file
with open("zotero_schema_output.html", "w", encoding="utf-8") as file:
    file.write(html_output)

print("HTML file has been generated: zotero_schema_output.html")

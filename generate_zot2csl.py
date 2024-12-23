import os
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
    csl_types = schema.get('csl', {}).get('types', {})
    for csl_type, zotero_types in csl_types.items():
        if item_type in zotero_types:
            return [csl_type]
    return ["No CSL mapping found"]

# Function to generate the HTML based on the schema
def generate_html(schema, schema_url, schema_version):
    current_date = datetime.now().strftime("%Y-%m-%d")
    current_time = datetime.now().strftime("%H:%M")  # Exact time in hours:minutes

    # Extract relevant parts of the schema
    item_types = schema.get('itemTypes', [])
    csl_types = schema.get('csl', {}).get('types', {})
    csl_fields = schema.get('csl', {}).get('fields', {})
    csl_names = schema.get('csl', {}).get('names', {})  # Map of creatorTypes to CSL variables
    locales = schema.get('locales', {}).get('en-GB', {})
    creator_ui_labels = locales.get('creatorTypes', {})  # UI labels for creatorTypes
    field_ui_labels = locales.get('fields', {})  # UI labels for fields

    # Initialize the HTML structure
    html = f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Zotero to CSL Mappings</title>
        <link rel="stylesheet" type="text/css" href="style.css">
    </head>
    <body>
        <h1>Zotero to CSL Mappings</h1>
        <p>Extracted on {current_date} at {current_time} from version {schema_version} found at <a href="{schema_url}">{schema_url}</a></p>
        <div class="toc">
            <h2>Table of Contents</h2>
            <ul>
    '''

    # Generate the Table of Contents with CSL mapping
    for item in item_types:
        item_type = item['itemType']
        csl_type = get_csl_mapping_for_zotero_item_type(schema, item_type)
        csl_type_str = ', '.join(csl_type)
        html += f'<li><a href="#{item_type}">{item_type} → {csl_type_str}</a></li>\n'

    html += '''
            </ul>
        </div>
    '''

    # Generate details for each item type with the correct CSL mapping in the headings
    for item in item_types:
        item_type = item['itemType']
        csl_type = get_csl_mapping_for_zotero_item_type(schema, item_type)
        csl_type_str = ', '.join(csl_type)

        html += f'''
        <div class="item-type" id="{item_type}">
            <h2>{item_type} → {csl_type_str}</h2>
            <table border="1" cellpadding="5" cellspacing="0">
                <thead>
                    <tr>
                        <th>UI Label</th>
                        <th>Zotero field</th>
                        <th>CSL variable</th>
                    </tr>
                </thead>
                <tbody>
        '''

        # Process creators
        html += '''
                <tr>
                    <th colspan="3">Creators</th>
                </tr>
        '''
        creator_types = item.get('creatorTypes', [])
        if creator_types:
            for creator in creator_types:
                zotero_creator = creator['creatorType']
                primary = " (Primary)" if creator.get("primary", False) else ""
                
                # If Primary, map to CSL variable "author"
                csl_creator = "author" if creator.get("primary", False) else csl_names.get(zotero_creator, "No CSL mapping found")
                
                ui_label = creator_ui_labels.get(zotero_creator, zotero_creator)
                html += f'''
                    <tr>
                        <td>{ui_label}</td>
                        <td>{zotero_creator}</td>
                        <td>{csl_creator}</td>
                    </tr>
                '''
        else:
            html += '''
                <tr>
                    <td colspan="3">No creators available for this item type.</td>
                </tr>
            '''

        # Process other metadata
        html += '''
                <tr>
                    <th colspan="3">Other Metadata</th>
                </tr>
        '''
        for field in item['fields']:
            zotero_field = field['field']
            ui_label = field_ui_labels.get(zotero_field, zotero_field)
            csl_variable = ''
            for category, fields in csl_fields.items():
                if isinstance(fields, dict):
                    for sub_field, csl_var in fields.items():
                        if zotero_field in csl_var:
                            csl_variable = sub_field
                            break
                elif zotero_field in fields:
                    csl_variable = category

            html += f'''
                <tr>
                    <td>{ui_label}</td>
                    <td>{zotero_field}</td>
                    <td>{csl_variable}</td>
                </tr>
            '''

        html += '''
            </tbody>
            </table>
        </div>
        '''

    # Close HTML structure
    html += '''
    </body>
    </html>
    '''

    return html


# URL of the Zotero schema
schema_url = "https://raw.githubusercontent.com/zotero/zotero-schema/master/schema.json"

# Fetch the schema from the URL
schema = load_schema_from_url(schema_url)

# Get the schema version
schema_version = schema.get("version", "unknown version")

# Generate HTML output
html_output = generate_html(schema, schema_url, schema_version)

# Write to an HTML file
with open("index.html", "w", encoding="utf-8") as file:
    file.write(html_output)

print("HTML file has been generated: index.html")

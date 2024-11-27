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
    
    # Handle reverse mapping: Check if the item_type is a value for any CSL type
    for csl_type, zotero_types in csl_types.items():
        if item_type in zotero_types:
            return [csl_type]  # Return the matching CSL type
    
    # If no CSL types are found, log a message and set a default message
    return ["No CSL mapping found"]

# Function to generate the HTML based on the schema
def generate_html(schema, schema_url, schema_version):
    # Get the current date
    current_date = datetime.now().strftime("%Y-%m-%d")

    # Extract relevant parts of the schema
    item_types = schema.get('itemTypes', [])
    csl_types = schema.get('csl', {}).get('types', {})  # CSL type mapping
    csl_fields = schema.get('csl', {}).get('fields', {})  # CSL fields to variables
    locales = schema.get('locales', {}).get('en-GB', {}).get('fields', {})

    # Initialize the HTML structure
    html = f'''
    <!DOCTYPE html>
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
        
        # Correctly lookup CSL types from csl["types"]
        csl_type = get_csl_mapping_for_zotero_item_type(schema, item_type)
        
        # Join multiple CSL types with a comma if necessary
        csl_type_str = ', '.join(csl_type)

        html += f'<li><a href="#{item_type}">{item_type} → {csl_type_str}</a></li>\n'
    
    html += '''
            </ul>
        </div>
    '''

    # Generate details for each item type with the correct CSL mapping in the headings
    for item in item_types:
        item_type = item['itemType']
        
        # Correctly lookup CSL types from csl["types"]
        csl_type = get_csl_mapping_for_zotero_item_type(schema, item_type)
        
        # Join multiple CSL types with a comma if necessary
        csl_type_str = ', '.join(csl_type)

        html += f'''
        <div class="item-type" id="{item_type}">
            <h2>{item_type} → {csl_type_str}</h2>
            <table>
                <tr>
                    <th>UI Label</th>
                    <th>Zotero field</th>
                    <th>CSL variable</th>
                </tr>
        '''

        # Process fields for each item type
        for field in item['fields']:
            zotero_field = field['field']
            ui_label = locales.get(zotero_field, zotero_field)
            
            # Match CSL variable (check against csl_fields)
            csl_variable = ''
            for category, fields in csl_fields.items():
                if isinstance(fields, dict):  # Handle fields that map to a dictionary (date, names)
                    for sub_field, csl_var in fields.items():
                        if zotero_field in csl_var:
                            csl_variable = sub_field
                            break
                elif zotero_field in fields:  # If it's a list of possible Zotero fields
                    csl_variable = category  # Use the category as the CSL variable

            # Add row to the table
            html += f'''
                <tr>
                    <td>{ui_label}</td>
                    <td>{zotero_field}</td>
                    <td>{csl_variable}</td>
                </tr>
            '''
        
        html += '''
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

# Generate the HTML output
html_output = generate_html(schema, schema_url, schema_version)

# Write to an HTML file
with open("zotero_schema_output.html", "w", encoding="utf-8") as file:
    file.write(html_output)

print("HTML file has been generated: zotero_schema_output.html")

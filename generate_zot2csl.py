#!/usr/bin/env python3
"""
Generate a console listing of Zotero item types with fields and creators,
inserting creator types immediately after the "title" field.

Fixes the "unhashable type: 'dict'" error by normalising field/creator entries
that can be either strings or dicts in the Zotero schema.
"""
import sys
import requests

SCHEMA_URL = "https://raw.githubusercontent.com/zotero/zotero-schema/master/schema.json"
LOCALE = "en-US"

def fetch_schema(url=SCHEMA_URL):
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Error fetching schema:", e, file=sys.stderr)
        return {}

def normalize_field_entry(field_entry):
    """
    Accept either:
      - "title" (str)
      - {"field": "title", "baseField": "title", ...}
    Return the canonical field key string (e.g. "title").
    """
    if isinstance(field_entry, str):
        return field_entry
    if isinstance(field_entry, dict):
        # Prefer explicit 'field', fallback to 'baseField'
        return field_entry.get("field") or field_entry.get("baseField") or str(field_entry)
    return str(field_entry)

def normalize_creator_entry(creator_entry):
    """
    Accept either:
      - "author" (str)
      - {"creatorType": "author", "primary": True}
    Return tuple (creator_key, primary_bool).
    """
    if isinstance(creator_entry, str):
        return creator_entry, False
    if isinstance(creator_entry, dict):
        return creator_entry.get("creatorType") or creator_entry.get("type") or str(creator_entry), bool(creator_entry.get("primary", False))
    return str(creator_entry), False

def merge_fields_and_creators(item_type_schema, fields_map, creators_map):
    """
    Merge fields and creatorTypes into a single ordered list,
    placing creators right after the title field.
    Returns list of tuples: (kind, key, label)
      kind: 'field' or 'creator'
      key: canonical key (for creator, add " (author)" to the key if primary)
      label: human UI label from locales
    """
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
            # Insert creators immediately after the title field
            for creator_entry in creators_list:
                c_key, primary = normalize_creator_entry(creator_entry)
                c_label = creators_map.get(c_key, c_key)
                display_key = f"{c_key} (author)" if primary else c_key
                merged.append(("creator", display_key, c_label))

    # If there was no title, append creators at the end as a fallback
    if not title_seen and creators_list:
        for creator_entry in creators_list:
            c_key, primary = normalize_creator_entry(creator_entry)
            c_label = creators_map.get(c_key, c_key)
            display_key = f"{c_key} (author)" if primary else c_key
            merged.append(("creator", display_key, c_label))

    return merged

def main():
    schema = fetch_schema()
    if not schema:
        sys.exit(1)

    locales = schema.get("locales", {})
    loc = locales.get(LOCALE, {})
    if not loc:
        print(f"Locale '{LOCALE}' not found in schema.", file=sys.stderr)
        sys.exit(1)

    fields_map = loc.get("fields", {})
    creators_map = loc.get("creatorTypes", {})
    item_types_map = loc.get("itemTypes", {})

    # itemTypes in the schema is a list of item-type objects (not a dict)
    item_types = schema.get("itemTypes", [])

    for item_schema in item_types:
        item_key = item_schema.get("itemType")
        if not item_key:
            continue
        item_label = item_types_map.get(item_key, item_key)
        print("\n" + "=" * 60)
        print(f"{item_label} ({item_key})")
        print("-" * 60)

        merged = merge_fields_and_creators(item_schema, fields_map, creators_map)
        for kind, key, label in merged:
            print(f"{kind:8} {key:30} → {label}")

if __name__ == "__main__":
    main()

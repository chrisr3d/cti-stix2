# This script exists to validate the structure and numbering of sections in a Markdown document.
# It will return 1 if any errors appear in 0 if it succeeds
# Usage: python validate_markdown.py <markdown_file.md>

import argparse
import re

def validate_section_numbers(content: str):
    """Check heading numbering, indentation depth, and ordering in the document."""
    pattern = re.compile(r'\n(#+) (\d+(\.\d+)*)\.? +([^<\n]+)')
    results = pattern.findall(content, re.MULTILINE)
    errors = []
    running_counts = []
    last_name = ''

    for result in results:
        depth = len(result[0])
        number = result[1]
        name = result[3]

        if depth > len(running_counts):
            running_counts.append(0)
            last_name = ""
        elif depth < len(running_counts):
            running_counts = running_counts[:depth]
            last_name = ""
        else:
            name = name.strip()
            # section 1 and 12 don't follow alphabetical order currently.  Section 1 and 3 for narrative reasons.  Sections 9 and 12 are for legacy ones.
            # 7.2.3 is for granular markings which are after object markings so this also might make sense from a narrative perspective
            if last_name > name and running_counts[0] not in (1, 3, 9, 12) and number != "7.2.3":
                errors.append(f"Section {number} contains {name} which should appear before {last_name}")
            last_name = name

        running_counts[-1] += 1
        expected_num = ".".join(str(count) for count in running_counts)
        if expected_num != number:
            errors.append(f"Section number mismatch for section: {number} expected {expected_num}")

        if depth != len(number.split('.')):
            errors.append(f"Indentation mismatch for section number: {number}")

    return errors

def validate_references(content: str):
    """Validate that markdown and HTML links point to existing anchors."""
    valid_anchors = set()
    anchors = re.findall(r'<a id=[\'"]([^"\']*)["\']', content, re.MULTILINE)
    markdown_references = re.findall(r'\(#([^)]+)\)', content, re.MULTILINE)
    html_references = re.findall(r'href=[\'"]#([^"\']+)["\']', content, re.MULTILINE)

    for anchor in anchors:
        valid_anchors.add(anchor)

    errors = set()
    for reference in markdown_references:
        if reference not in valid_anchors:
            errors.add(f"Invalid reference: {reference}")
    for reference in html_references:
        if reference not in valid_anchors:
            errors.add(f"Invalid reference: {reference}")

    return list(errors)

def validate_table_of_contents(content: str):
    """Verify that the table of contents matches the document headings."""
    errors = []
    table_start = content.find('# Table of Contents')
    table_end = content.find('---', table_start + 1)
    full_table = content[table_start: table_end]
    table_entries = re.findall(r'- ([\dA-Z]+(\.\d+)*|Appendix [A-Z])[:\.]? +\[([^\]]+)\]\(#([^)]+)\)', full_table)
    all_sections = re.findall(r'\n#+ ([\dA-Z]+(\.\d+)*|Appendix [A-Z])[:\.]? +([^<\n]+)<a id=[\'"]([^"\']*)["\']>', content[table_end:], re.MULTILINE)

    table_dict = {}
    actual_entries = set()
    
    for entry in table_entries:
        if entry[0]:
            table_dict[entry[0]] = {
                "title": entry[2].strip(),
                "anchor": entry[3].strip()
            }

    for entry in all_sections:
        actual_entries.add(entry[0])
        if entry[0] not in table_dict:
            errors.append(f"Section {entry[0]} is in the document but not in the table of contents.")
        elif table_dict[entry[0]]["title"] != entry[2].strip():
            errors.append(f"Title mismatch for section {entry[0]}: expected '{table_dict[entry[0]]['title']}', got '{entry[2].strip()}'")
        elif table_dict[entry[0]]["anchor"] != entry[3].strip():
            errors.append(f"Anchor mismatch for section {entry[0]}: expected '{table_dict[entry[0]]['anchor']}', got '{entry[3].strip()}'")

    for entry in table_dict.keys():
        if entry not in actual_entries:
            errors.append(f"Section {entry} is in the table of contents but not in the document.")

    return errors

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Validates Markdown Document')
    parser.add_argument("file", help="Path to the Markdown file to validate")
    args = parser.parse_args()
    errors = []

    with open(args.file, 'r', encoding='utf-8') as input_file:
        content = input_file.read()

    errors.extend(validate_section_numbers(content))
    errors.extend(validate_references(content))
    errors.extend(validate_table_of_contents(content))
    if len(errors) > 0:
        for error in errors:
            print(error)
        exit(1)

    exit(0)
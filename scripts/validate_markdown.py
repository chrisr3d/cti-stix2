# This script exists to validate the structure and numbering of sections in a Markdown document.
# It will return 1 if any errors appear in 0 if it succeeds

import argparse
import html
import re

def _split_number(number: str) -> (str, int):
    parts = number.split('.')
    if len(parts) == 1:
        return '', int(parts[0])
    else:
        return '.'.join(parts[:-1]), int(parts[-1])

def validate_section_numbers(content: str):
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

        prefix, suffix = _split_number(number)
        running_counts[-1] += 1
        if running_counts[-1] != suffix:
            expected_num = ".".join(str(count) for count in running_counts)
            errors.append(f"Section number mismatch for section: {number} expected {expected_num}")

        if depth != len(number.split('.')):
            errors.append(f"Indentation mismatch for section number: {number}")

    return errors

def validate_references(content: str):
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Validates Markdown Document')
    parser.add_argument("file", help="Path to the Markdown file to validate")
    args = parser.parse_args()
    errors = []

    with open(args.file, 'r', encoding='utf-8') as input_file:
        content = input_file.read()

    errors.extend(validate_section_numbers(content))
    errors.extend(validate_references(content))

    if len(errors) > 0:
        for error in errors:
            print(error)
        exit(1)

    exit(0)
import argparse
import re

def handle_properties(markdown_text):
    sections = [
        ("\n# 4. ", "\n# 5. "), 
        # ("\n# 6. ", "\n# 7. "), 
    ]

    for start_text, end_text in sections:
        section_start = markdown_text.find(start_text)
        section_end = markdown_text.find(end_text, section_start)
        section = markdown_text[section_start:section_end]

        # object property tables
        start = section.find("| **Required Common Properties** |")
        while start > -1 and start < section_end:
            end = section.find("\n###", start + 1)

            if end == -1:
                end = section_end

            if start != -1:
                html_table = _object_property_table(section[start:end])
                section = section[:start] + html_table + section[end:]
                start = section.find("| **Required Common Properties** |", start + len(html_table))
            else:
                start = section.find("| **Required Common Properties** |", end)

        # extension property tables
        start = section.find("| **Property Name** |")
        while start > -1 and start < section_end:
            end = section.find("\n###", start + 1)

            if end == -1:
                end = section_end

            if start != -1:
                html_table = _extension_property_table(section[start:end])
                section = section[:start] + html_table + section[end:]
                start = section.find("| **Property Name** |", start + len(html_table))
            else:
                start = section.find("| **Property Name** |", end)

        markdown_text = markdown_text[:section_start] + section + markdown_text[section_end:]

    return markdown_text

def _object_property_table(markdown_text):
    property_pattern =re.compile(r"\*\*([^\*]+)\*\* \(+([^\)]+)\)")
    type_pattern = re.compile(r"\[([^\]]+)\]\((#([^\)]+))\)")
    bold_pattern = re.compile(r"\*\*([^\*]+)\*\*")

    required_properties = {}
    optional_properties = {}
    property_list_items = {
        "Required Common Properties": [],
        "Optional Common Properties": [],
        "Not Applicable Common Properties": [],
        "Object Specific Properties": []
    }
    row_content = ""

    template = '<table border="1" cellspacing="0" cellpadding="6" width="100%">\n' \
        '  <tr>\n' \
        '    <th><span class="stixtr">Required Common Properties</span></th>\n' \
        '  </tr>\n' \
        '  <tr><td>{{required_common_properties}}</td></tr>\n' \
        '  <tr>\n' \
        '    <th><span class="stixtr">Optional Common Properties</span></th>\n' \
        '  </tr>\n' \
        '  <tr><td>{{optional_common_properties}}</td></tr>\n' \
        '  <tr>\n' \
            '<th><span class="stixtr">Not Applicable Common Properties</span></th>\n' \
        '</tr>\n' \
        '  <tr><td>{{not_applicable}}</td></tr>\n' \
        '  <tr>\n' \
            '<th><span class="stixtr">Object Specific Properties</span></th>\n' \
        '</tr>\n' \
        '  <tr><td>{{specific_properties}}</td></tr>\n' \
        '</table>\n' \
        '<table border="1" cellspacing="0" cellpadding="6">\n' \
        '  <tr>\n' \
        '    <th><span class="stixtr">Property Name</span></th>\n' \
        '    <th><span class="stixtr">Type</span></th>\n' \
        '    <th><span class="stixtr">Description</span></th>\n' \
        '  </tr>\n{{rows}}' \
        '\n</table>\n'

    # this handles the header
    current_section = None
    for line in markdown_text.split('\n'):
        parts = line.split("|")
        if len(parts) == 1 or parts[1].strip().startswith("-"):
            continue
        elif len(parts) < 2:
            break
        if parts[1].strip() in ["**Required Common Properties**", "**Optional Common Properties**", "**Not Applicable Common Properties**"]:
            current_section = parts[1].strip().strip("**")
            continue
        elif parts[1].strip().endswith("Object Specific Properties**"):
            current_section = "Object Specific Properties"
            continue
        elif current_section is not None and current_section != "Object Specific Properties":
            for item in parts[1].strip().split(","):
                property_list_items[current_section].append(item.strip().strip("**"))

    # this handles the table body
    start = markdown_text.find("| **Property Name** | **Type** | **Description** |")
    for line in markdown_text[start:].split('\n'):
        parts = line.split("|")
        if len(parts) == 1 or parts[1].strip().startswith("-"):
            continue
        elif parts[1].strip() == "**Property Name**":
            continue
        elif len(parts) < 2:
            break

        property_match = property_pattern.match(parts[1].strip())
        property_name = f"<strong>{property_match[1]}</strong> ({property_match[2]})"
        type_name = type_pattern.sub('<a href="\\2" class="stixtype">\\1</a>', parts[2].strip())
        description = type_pattern.sub('<a href="\\2" class="stixtype">\\1</a>', parts[3].strip())
        description = bold_pattern.sub("<strong>\\1</strong>", description)

        if property_match[2] == "required":
            required_properties[property_name] = {
                "type": type_name,
                "description": description
            }
        else:
            optional_properties[property_name] = {
                "type": type_name,
                "description": description
            }

    for entry in sorted(required_properties.keys()):
        print(f"Adding required property: {entry}")
        row_content += f"\n  <tr>\n    <td>{entry}</td>\n    <td>{required_properties[entry]['type']}</td>\n    <td>{required_properties[entry]['description']}</td>\n</tr>\n"
    for entry in sorted(optional_properties.keys()):
        row_content += f"\n  <tr>\n    <td>{entry}</td>\n    <td>{optional_properties[entry]['type']}</td>\n    <td>{optional_properties[entry]['description']}</td>\n</tr>\n"

    template = template.replace("{{required_common_properties}}", ", ".join(property_list_items["Required Common Properties"]))
    template = template.replace("{{optional_common_properties}}", ", ".join(property_list_items["Optional Common Properties"]))
    template = template.replace("{{not_applicable}}", ", ".join(property_list_items["Not Applicable Common Properties"]))
    template = template.replace("{{specific_properties}}", ", ".join(property_list_items["Object Specific Properties"]))
    template = template.replace("{{rows}}", row_content)

    return template

def _extension_property_table(markdown_text):
    property_pattern =re.compile(r"\*\*([^\*]+)\*\* \(+([^\)]+)\)")
    type_pattern = re.compile(r"\[([^\]]+)\]\((#([^\)]+))\)")
    bold_pattern = re.compile(r"\*\*([^\*]+)\*\*")

    required_properties = {}
    optional_properties = {}
    row_content = ""

    template = '<table border="1" cellspacing="0" cellpadding="6">\n' \
        '  <tr>\n' \
        '    <th><span class="stixtr">Property Name</span></th>\n' \
        '    <th><span class="stixtr">Type</span></th>\n' \
        '    <th><span class="stixtr">Description</span></th>\n' \
        '  </tr>\n{{rows}}' \
        '\n</table>\n'

    # extensions have no header

    # this handles the table body
    start = markdown_text.find("| **Property Name** | **Type** | **Description** |")
    for line in markdown_text[start:].split('\n'):
        parts = line.split("|")
        if len(parts) == 1 or parts[1].strip().startswith("-"):
            continue
        elif parts[1].strip() == "**Property Name**":
            continue
        elif len(parts) < 2:
            break

        property_match = property_pattern.match(parts[1].strip())
        property_name = f"<strong>{property_match[1]}</strong> ({property_match[2]})"
        type_name = type_pattern.sub('<a href="\\2" class="stixtype">\\1</a>', parts[2].strip())
        description = type_pattern.sub('<a href="\\2" class="stixtype">\\1</a>', parts[3].strip())
        description = bold_pattern.sub("<strong>\\1</strong>", description)

        if property_match[1] == "(Required)":
            required_properties[property_name] = {
                "type": type_name,
                "description": description
            }
        else:
            optional_properties[property_name] = {
                "type": type_name,
                "description": description
            }

    for entry in sorted(required_properties.keys()):
        row_content += f"\n  <tr>\n    <td>{entry}</td>\n    <td>{required_properties[entry]['type']}</td>\n    <td>{required_properties[entry]['description']}</td>\n</tr>\n"
    for entry in sorted(optional_properties.keys()):
        row_content += f"\n  <tr>\n    <td>{entry}</td>\n    <td>{optional_properties[entry]['type']}</td>\n    <td>{optional_properties[entry]['description']}</td>\n</tr>\n"

    template = template.replace("{{rows}}", row_content)

    return template

def handle_relationships(markdown_text):
    # TODO: Implement method
    return markdown_text

def handle_vocabs(markdown_text):
    # read through the markdown file and find all vocabulary tables in section 10
    start = section_start = markdown_text.find("\n## 10.")
    section_end = markdown_text.find("\n## 11.", section_start)
    while start > -1 and start < section_end:
        end = markdown_text.find("\n## 10.", start + 1)

        if end == -1:
            end = section_end

        start_table = markdown_text[start:end].find("| **Vocabulary Value** | **Description** |")
        if start_table != -1:
            start = start + start_table
            html_table = _vocab_table(markdown_text[start:end])
            markdown_text = markdown_text[:start] + html_table + markdown_text[end:]
            start = start + len(html_table)
        else:
            start = end

    return markdown_text

def _vocab_table(markdown_text):
    vocab_items = {}

    template = '<table border="1" cellspacing="0" cellpadding="6" width="100%">' \
    '<tr>' \
    '    <th><span class="stixtr">Vocabulary Summary</span></th>' \
    "</tr>" \
    "<tr>\n    <td>{{summary}}</td>\n</tr>" \
    "</table>\n" \
    '<table border="1" cellspacing="0" cellpadding="6" width="100%">' \
    '<tr>' \
    '    <th><span class="stixtr">Vocabulary Value</span></th>' \
    '    <th><span class="stixtr">Description</span></th>' \
    "</tr>\n{{rows}}\n</table>\n\n"
    
    for line in markdown_text.split('\n'):
        parts = line.split("|")
        if len(parts) == 1 or (parts[1].strip().startswith("*") or parts[1].strip().startswith("-")):
            continue
        elif len(parts) < 2:
            break

        vocab_items[parts[1].strip()] = parts[2].strip()

    row_content = ""
    summary_content = []
    for entry in sorted(vocab_items.keys()):
        summary_content.append('<span class="stixliteral">' + entry + '</span>')
        row_content += f"<tr>\n    <td><span class=\"stixliteral\">{entry}</span></td>\n    <td>{vocab_items[entry]}</td>\n</tr>\n"

    template = template.replace("{{summary}}", ", ".join(summary_content))
    template = template.replace("{{rows}}", row_content)

    return template

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Replaces md table content with HTML tables')
    parser.add_argument('input_file', help='Input Markdown file')
    parser.add_argument('output_file', help='Output HTML file')
    args = parser.parse_args()

    with open(args.input_file, 'r', encoding='utf-8') as f:
        markdown_text = f.read()

    markdown_text = handle_vocabs(markdown_text)
    markdown_text = handle_properties(markdown_text)
    markdown_text = handle_relationships(markdown_text)

    with open(args.output_file, 'w', encoding='utf-8') as f:
        f.write(markdown_text)
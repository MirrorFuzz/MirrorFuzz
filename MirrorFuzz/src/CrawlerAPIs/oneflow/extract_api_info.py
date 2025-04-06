import json
import re
from time import sleep

import requests
import pandas as pd
from bs4 import BeautifulSoup


def remove_extra_newlines(text):
    # Use line breaks to separate text
    lines = text.split('\n')
    # Remove the leading and trailing spaces from each line and filter out all blank lines
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    # Reconnect the cleaned lines with a line break character
    cleaned_text = '\n'.join(cleaned_lines)
    return cleaned_text


def remove_extra_newlines(text):
    # Use line breaks to separate text
    text = remove_torch(text)
    lines = text.split('\n')
    # Remove the leading and trailing spaces from each line and filter out all blank lines
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    # Reconnect the cleaned lines with a line break character
    cleaned_text = '\n'.join(cleaned_lines)
    return cleaned_text


def remove_torch(text):
    cleaned_text = "\n".join([line for line in text.split("\n") if "pytorch" not in line.lower()])
    return cleaned_text


def split_and_clean_documentation(doc_str):
    sections = ["Parameters", "Returns", "Return type", "Note", "Shape", "For example", "Examples:"]
    split_docs = {section: "" for section in sections}
    split_docs["Description"] = ""

    current_section = "Description"
    for line in doc_str.split('\n'):
        line_strip = line.strip()
        if any(line_strip.startswith(sec) for sec in sections):
            current_section = next(sec for sec in sections if line_strip.startswith(sec))
            # Skip the line that contains the section keyword
            continue

        split_docs[current_section] += line + '\n'

    return split_docs


def extract_api_full_signature(text):
    pattern = r'\b[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*\s*\([^\)]*\)'
    match = re.search(pattern, text)
    if match:
        full_signature = match.group(0)
        return full_signature
    else:
        return None


def extract_api_signature(text):
    # Use \ b to ensure complete word matching, and use \ s * to match possible spaces
    pattern = r'\b[a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*(?=\()'
    match = re.search(pattern, text)
    if match:
        # Combine the matched API signature parts
        api_signature = match.group(0)
        return api_signature
    else:
        return None


def save_to_file(data, filename='oneflow_api_list_jsons.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json_str = json.dumps(data, ensure_ascii=False, indent=4)
        f.write(json_str)


if __name__ == '__main__':
    # Read CSV file
    input_csv = 'oneflow_api_list_html.csv'

    df = pd.read_csv(input_csv, header=None, names=['api_name', 'api_url'])

    # Initialization result list
    results = []
    results_jsons = []

    # Traverse every line
    for index, row in df.iterrows():
        api_name = row['api_name']
        api_url = row['api_url']
        print('now processing: ', api_url, api_name)
        # Request API documentation page
        while True:
            try:
                response = requests.get(api_url)
                break
            except Exception as e:
                print(e)
                sleep(1)
        soup = BeautifulSoup(response.content, 'html.parser')
        api_signature = soup.find(id=api_name)
        api_html_block = api_signature.findParent()

        split_docs = split_and_clean_documentation(api_html_block.text)
        jittor_api_info = {"api_name": api_name, "api_url": api_url,
                           'api_signature': extract_api_full_signature(api_signature.text),
                           'api_description': "",
                           "return_value": "", "parameters": "", "input_shape": "", "notes": "", "code_example": ""}
        # Print each section
        for section, content in split_docs.items():
            # print(f"{section}:\n{remove_extra_newlines(content)}\n")
            if section == "Parameters":
                jittor_api_info["parameters"] = content
            elif section == "Returns" or section == "Return value":
                jittor_api_info["return_value"] += content
            elif section == "Note":
                jittor_api_info["notes"] = remove_extra_newlines(content)
            elif section == "Shape":

                jittor_api_info["input_shape"] = content
            elif section == "For example":

                jittor_api_info["code_example"] = content
            elif section == "Example":

                jittor_api_info["code_example"] = content
            elif section == "Description":
                content = content.replace(api_signature.text, "")
                jittor_api_info["api_description"] = remove_extra_newlines(content)
            else:
                pass

        results_jsons.append(jittor_api_info)
        save_to_file(results_jsons)
        sleep(1)

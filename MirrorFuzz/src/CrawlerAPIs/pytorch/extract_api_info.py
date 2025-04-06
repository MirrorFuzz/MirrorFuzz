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


def save_to_file(data, filename='pytorch_api_list_jsons.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        # print(data)
        json_str = json.dumps(data, ensure_ascii=False, indent=4)
        f.write(json_str)


if __name__ == '__main__':
    input_csv = 'pytorch_api_list_html.csv'

    df = pd.read_csv(input_csv, header=None, names=['api_name', 'api_url'])

    results = []
    results_jsons = []

    for index, row in df.iterrows():
        api_name = row['api_name']
        api_url = row['api_url']
        print('now processing: ', api_url,
              api_name)

        while True:
            try:
                response = requests.get(api_url)
                break
            except Exception as e:
                print(e)
                sleep(1)
        soup = BeautifulSoup(response.content, 'html5lib')

        api_signature = soup.find(id=api_name)
        if api_signature is None:
            torch_api_info = {"api_name": api_name, "api_url": api_url,
                              'api_signature': '',
                              'api_description': '',
                              "return_value": '', "parameters": '',
                              "input_shape": '',
                              "notes": '', "code_example": ''}

            results_jsons.append(torch_api_info)
            # print(results_jsons)
            save_to_file(results_jsons)
            continue
        api_html_block = api_signature.findParent()

        # print(api_html_block.text)
        dts = api_html_block.find_all('dt')
        api_parameters = ''
        code_block_text = ''
        api_description = ''
        api_returns = ''
        api_note_text = ''
        input_shape = ''
        for dt in dts:
            if "Parameters" in dt.text:
                if dt.find_next_sibling() is not None:
                    api_parameters += dt.find_next_sibling().text

            if "Keyword Arguments" in dt.text:
                # print(dt.text)
                if dt.find_next_sibling() is not None:
                    api_parameters += dt.find_next_sibling().text

            if "Returns" in dt.text:
                if dt.find_next_sibling() is not None:
                    api_returns += dt.find_next_sibling().text
            if "Note" in dt.text:
                if dt.find_next_sibling() is not None:
                    api_note_text += dt.find_next_sibling().text
            if "Shape:" in dt.text:
                if dt.find_next_sibling() is not None:
                    input_shape += dt.find_next_sibling().text
            if "Example:" in dt.text:
                if dt.find_next_sibling() is not None:
                    code_block_text += dt.find_next_sibling().text
            if "Examples:" in dt.text:
                if dt.find_next_sibling() is not None:
                    code_block_text += dt.find_next_sibling().text
        if api_signature.find_next_sibling() is not None:
            dd = api_signature.find_next_sibling()
            if dd.find('p') is not None:
                api_description = dd.find('p').text

        torch_api_info = {"api_name": api_name, "api_url": api_url,
                          'api_signature': extract_api_full_signature(api_signature.text),
                          'api_description': api_description,
                          "return_value": api_returns, "parameters": remove_extra_newlines(api_parameters),
                          "input_shape": input_shape,
                          "notes": api_note_text, "code_example": code_block_text}

        results_jsons.append(torch_api_info)
        # print(results_jsons)
        save_to_file(results_jsons)
        sleep(1)

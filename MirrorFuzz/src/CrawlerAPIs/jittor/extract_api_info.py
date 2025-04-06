import json
import re
from time import sleep

import requests
import pandas as pd
from bs4 import BeautifulSoup


def remove_extra_newlines(text):
    lines = text.split('\n')
    # Remove the leading and trailing spaces from each line and filter out all blank lines
    cleaned_lines = [line.strip() for line in lines if line.strip()]
    # Reconnect the cleaned lines with a line break character
    cleaned_text = '\n'.join(cleaned_lines)
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


def save_to_file(data, filename='jittor_api_list_jsons.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json_str = json.dumps(data, ensure_ascii=False, indent=4)
        f.write(json_str)


if __name__ == '__main__':

    # Read CSV file
    input_csv = 'jittor_api_list_html.csv'
    output_csv = 'jittor_api_list_jsons.json'
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
        response = requests.get(api_url)
        soup = BeautifulSoup(response.content, 'html.parser')
        api_signature = soup.find(id=api_name)
        try:
            api_info = api_signature.findNextSiblings('dd')[0]
        except Exception as e:
            print(e)
            continue

        # intro_content = api_info.find('dd').find_all(recursive=False)
        api_description = ''.join([tag.get_text() for tag in api_info if tag.name != 'dl'])
        print(api_signature.text)
        print(api_name)
        jittor_api_info = {"api_name": api_name, "api_url": api_url,
                           'api_signature': extract_api_full_signature(api_signature.text),
                           'api_description': remove_extra_newlines(api_description),
                           "return_value": "", "parameters": "", "input_shape": "", "notes": "", "code_example": ""}

        if extract_api_full_signature(api_signature.text) is not None:
            if api_name not in extract_api_full_signature(api_signature.text) and extract_api_full_signature(
                    api_signature.text) not in api_name:
                # print(api_name)
                api_name = extract_api_signature(api_signature.text)
                print('new api_name: ', api_name)
        else:
            if "别名" in api_info.text:
                jittor_api_info = {"api_name": api_name, "api_url": api_url, 'alias': ''.join(
                    [char for char in api_info.text if char.isalpha() and char.isascii()])}

        # Extract<dl>tag content
        dl_tag = api_info.find('dl')
        if dl_tag:
            dt_tags = dl_tag.find_all('dt')
            for dt_tag in dt_tags:
                if '返回值' in dt_tag.get_text():
                    jittor_api_info['return_value'] = dt_tag.find_next_sibling('dd').get_text().strip()
                elif '参数' in dt_tag.get_text():
                    jittor_api_info['parameters'] = dt_tag.find_next_sibling('dd').get_text().strip()
                elif '形状' in dt_tag.get_text():
                    jittor_api_info['input_shape'] = dt_tag.find_next_sibling('dd').get_text().strip()
                elif '注意事项' in dt_tag.get_text():
                    jittor_api_info['notes'] = dt_tag.find_next_sibling('dd').get_text().strip()
                elif '代码示例' in dt_tag.get_text():
                    jittor_api_info['code_example'] = dt_tag.find_next_sibling('dd').get_text().strip()
        results_jsons.append(jittor_api_info)
        save_to_file(results_jsons, output_csv)
        sleep(1)

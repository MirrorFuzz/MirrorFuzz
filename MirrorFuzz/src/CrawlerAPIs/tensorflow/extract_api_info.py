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


def save_to_file(data, filename='tensorflow_api_list_jsons.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        # print(data)
        json_str = json.dumps(data, ensure_ascii=False, indent=4)
        f.write(json_str)


if __name__ == '__main__':

    input_csv = 'tensorflow_api_list_html.csv'

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
        # print(soup)
        api_html = soup.find(class_='devsite-article')

        methods_div = api_html.find(id="methods")

        if methods_div is not None:
            # Find all peer elements and delete the elements after methods
            siblings = methods_div.find_next_siblings()

            # Delete all elements of the same level
            for sibling in siblings:
                sibling.decompose()
            methods_div.decompose()

        # Find all table tags
        tables = api_html.find_all(name='table')

        api_signature = ''
        input_shape = ''
        api_description = ''
        if api_html.find(class_="tfo-signature-link") is not None:
            api_signature = api_html.find(class_="tfo-signature-link").text

        api_article_body = api_html.find(class_="devsite-article-body")

        api_note = api_html.find(class_="warning")
        # print(api_html.find(id="input_shapessdfdsfd"))
        if api_html.find(id="input_shape") is not None:
            if api_html.find(id="input_shape").find_next_sibling() is not None:
                input_shape = api_html.find(id="input_shape").find_next_sibling().text

        if api_article_body.find_all('p') is not None:
            try:
                api_description = api_article_body.find_all('p')[1].text  # Description is always in the second p tag
            except Exception as e:
                print(e)
                api_description = ''

        api_returns = ''
        api_parameters = ''
        for table in tables:
            if table.find(id="args") is not None:
                api_parameters += remove_extra_newlines(table.text.replace('\n', '').replace('Args', ''))

            if table.find(id="attributes") is not None:
                api_parameters += remove_extra_newlines(table.text.replace('Attributes', ''))

            if table.find(id="returns") is not None:
                api_returns = remove_extra_newlines(table.text.replace('Returns', ''))

        # get code
        code1 = api_html.find(id="for_example", attrs={"data-text": "For example:"})
        code2 = api_html.find(id="example", attrs={"data-text": "Example:"})
        code3 = api_html.find(id="Sample Usages", attrs={"data-text": "Sample Usages:"})
        code_block = None
        if code1 is not None:
            selected_code = code1
        elif code2 is not None:
            selected_code = code2
        else:
            selected_code = code3

        if selected_code is not None:
            code_block = selected_code.find_next_sibling()

        code_block_text = ''
        api_note_text = ''
        if code_block is not None:
            code_block_text = code_block.text
        if api_note is not None:
            api_note_text = api_note.text

        tf_api_info = {"api_name": api_name, "api_url": api_url,
                       'api_signature': api_signature,
                       'api_description': api_description,
                       "return_value": api_returns, "parameters": api_parameters, "input_shape": input_shape,
                       "notes": api_note_text, "code_example": code_block_text}

        results_jsons.append(tf_api_info)
        save_to_file(results_jsons)
        sleep(1)

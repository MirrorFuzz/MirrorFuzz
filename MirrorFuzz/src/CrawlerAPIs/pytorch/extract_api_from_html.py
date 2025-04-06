from bs4 import BeautifulSoup


def extract_hrefs(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    base_url = "https://pytorch.org/docs/stable/"
    result = []

    # Find all<li>tags
    for li in soup.find_all('li'):
        a_tag = li.find('a')
        if a_tag and 'href' in a_tag.attrs:
            href = a_tag['href']
            hash_part = href.split('#')[-1]
            full_url = base_url + href
            result.append((hash_part, full_url))

    return result


def save_to_file(data, output_file):
    with open(output_file, 'w', encoding='utf-8') as file:
        for hash_part, full_url in data:
            file.write(f"{hash_part},{full_url}\n")


def load_csv(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        return list(reader)


def save_csv(data, file_path):
    with open(file_path, 'w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)


def process_apis(data):
    api_set = set(row[0] for row in data)
    processed_data = []

    for row in data:
        api = row[0]
        if api.startswith('module-'):
            stripped_api = api[len('module-'):]
            if stripped_api in api_set:
                # Remove both `module-` prefixed API and the stripped version
                api_set.remove(stripped_api)
            else:
                # Keep the stripped version
                row[0] = stripped_api
                processed_data.append(row)
        else:
            processed_data.append(row)

    return processed_data


import csv


def load_txt(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return set(line.strip() for line in file)


def load_csv(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        return list(reader)


def save_csv(data, file_path):
    with open(file_path, 'w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(data)


def find_common_apis(txt_apis, csv_data):
    csv_apis = set(row[0] for row in csv_data)
    common_apis = txt_apis.intersection(csv_apis)
    return [row for row in csv_data if row[0] in common_apis]


def remove_duplicates(data):
    seen = set()
    unique_data = []
    for row in data:
        row_tuple = tuple(row)
        if row_tuple not in seen:
            seen.add(row_tuple)
            unique_data.append(row)
    return unique_data


if __name__ == '__main__':
    html_file = './pytorch_api.html'
    output_file = 'pytorch_api_list_html.csv'

    # Read HTML file content
    with open(html_file, 'r', encoding='utf-8') as file:
        html_content = file.read()
    # Extract href information
    href_data = extract_hrefs(html_content)
    # Save to output file
    save_to_file(href_data, output_file)

    input_file = './pytorch_api_list_html.csv'
    output_file = 'pytorch_api_list_html.csv'

    # Load CSV file content
    data = load_csv(input_file)

    processed_data = process_apis(data)

    save_csv(processed_data, output_file)

    txt_file = './pytorch_api_list_code.txt'
    csv_file = './pytorch_api_list_html.csv'
    output_file = 'pytorch_api_list_html.csv'

    # Load the contents of txt and csv files
    txt_apis = load_txt(txt_file)
    csv_data = load_csv(csv_file)

    # Find common APIs that exist together
    common_data = find_common_apis(txt_apis, csv_data)
    # unique_csv_data = remove_duplicates(common_data)
    save_csv(common_data, output_file)
    csv_file = 'pytorch_api_list_html.csv'
    output_file = 'pytorch_api_list_html.csv'

    csv_data = load_csv(csv_file)
    unique_csv_data = remove_duplicates(csv_data)

    save_csv(unique_csv_data, output_file)

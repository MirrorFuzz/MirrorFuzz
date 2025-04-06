from bs4 import BeautifulSoup

if __name__ == '__main__':

    html_file_path = './tensorflow_api.html'
    csv_file_path = 'tensorflow_api_list_html.csv'

    # Read HTML file content
    with open(html_file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    # Find all<li>elements
    li_elements = soup.find_all('li')
    # Initialization result list
    results = []

    # Traverse the<li>element and extract the<a>element's href and content
    for li in li_elements:
        a = li.find('a')
        if a:
            href = a['href']
            code_content = a.find('code').text if a.find('code') else ''
            results.append((code_content, href))


    def save_to_file(data, output_file):
        with open(output_file, 'w', encoding='utf-8') as file:
            for hash_part, full_url in data:
                file.write(f"{hash_part},{full_url}\n")


    save_to_file(results, csv_file_path)

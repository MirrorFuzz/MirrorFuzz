from bs4 import BeautifulSoup
import csv

if __name__ == '__main__':

    csv_file_path = 'oneflow_api_list_html.csv'
    html_file_path = './oneflow_api.html'

    with open(html_file_path, 'r') as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    data = []


    # Function to process list items
    def process_li(li):
        if 'has-children' in li.get('class', []):
            return

        a_tag = li.find('a', class_='reference internal')
        if a_tag:
            text = a_tag.get_text()
            href = 'https://oneflow.readthedocs.io/en/master/' + a_tag['href']
            data.append([text, href])


    # Iterate over all `li` elements
    for li in soup.find_all('li'):
        process_li(li)

    # Write the data to a CSV file
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        # writer.writerow(['Content', 'Href'])
        writer.writerows(data)

    print("Successfully extract APIs from HTML file and saved to CSV file.")

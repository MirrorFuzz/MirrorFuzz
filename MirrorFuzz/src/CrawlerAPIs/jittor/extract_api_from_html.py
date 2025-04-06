from bs4 import BeautifulSoup
import csv

if __name__ == '__main__':
    html_file_path = './jittor_api.html'
    csv_file_path = 'jittor_api_list_html.csv'

    # Read HTML file content
    with open(html_file_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, 'html.parser')
    links = soup.find_all('a')

    results = []
    for link in links:
        href = link.get('href')
        if href and '#' in href:
            fragment = href.split('#')[-1]
            href = 'https://cg.cs.tsinghua.edu.cn/jittor/assets/docs/' + href
            results.append((fragment, href))

    # Write results to a CSV file
    with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        csvwriter = csv.writer(csvfile)

        # csvwriter.writerow(['api_name', 'api_url'])  # Writing header
        csvwriter.writerows(results)
    print("Successfully extract APIs from HTML file and saved to CSV file.")

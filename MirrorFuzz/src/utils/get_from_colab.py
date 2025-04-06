import re
import gdown
import nbformat
import os

import requests


def download_notebook(url, output):
    gdown.download(url, output, quiet=False)


def extract_code_blocks(notebook_path):
    with open(notebook_path, 'r', encoding='utf-8') as f:
        notebook = nbformat.read(f, as_version=4)

    code_cells = [cell['source'] for cell in notebook.cells if cell.cell_type == 'code']
    code_blocks = ""
    result = []
    # print(code_cells)
    for code in code_cells:

        pattern = r'^!.*\n?'

        if re.search(pattern, code, flags=re.MULTILINE) is None:
            # code_blocks += f"#Code Block {code_cells.index(code) + 1}:\n{code}\n\n"
            result.append(f"#Code Block {code_cells.index(code) + 1}:\n{code}\n\n")

    # result.append(code_blocks)
    return result
    # with open('../ExtractIssues/extracted_code_blocks.txt', 'w', encoding='utf-8') as f:
    #     for i, code in enumerate(code_cells):
    #         f.write(f"Code Block {i + 1}:\n{code}\n\n")



def extract_file_id(url):

    match = re.search(r'/drive/([^/?]+)', url)
    if match:
        return match.group(1)
    else:
        raise ValueError('Invalid Google Colab URL')


# 主函数
def get_from_colab(colab_url):
    output = "notebook_temp.ipynb"
    file_id = extract_file_id(colab_url)
    download_url = f"https://drive.google.com/uc?id={file_id}&export=download"
    while True:
        try:
            response = requests.get(download_url, timeout=60)
            if response.status_code == 200:
                # Save the content to a .ipynb file
                with open(output, 'wb') as file:
                    file.write(response.content)
                code_blocks = extract_code_blocks(output)
                return code_blocks
            else:
                print(f"Failed to download the file. Status code: {response.status_code}")
                return []

        except Exception as e:
            if "Notebook does not appear to be JSON" in str(e):
                break
            print(e)







    os.remove(output)

    # output = "notebook_temp.ipynb"
    # count = 0
    # while count < 10:
    #     try:
    #         download_notebook(download_url, output)
    #         code_blocks = extract_code_blocks(output)
    #
    #         os.remove(output)
    #         return code_blocks
    #
    #     except Exception as e:
    #         print(e)
    #         if "Connection to drive.google.com timed out" in str(e):
    #             count += 1
    #             print("fail " + str(count), e)

    return []






import json
import itertools
import os

from src.utils.utils import list_subdirectories, folder_exists, create_directory, file_exists
from FlagEmbedding import BGEM3FlagModel


def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        return json.load(file)


def save_similarity_results(results, filepath):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        json.dump(results, outfile, ensure_ascii=False, indent=4)


def load_similarity_results(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return json.load(infile)


def calculate_and_save_similarity_results(api_a_json,api_b_json,dlf_a_name,dlf_b_name, model):
    chunk_size = 1000
    total = len(api_a_json)
    for index, api in enumerate(api_a_json):
        save_folder = f'./results/{dlf_a_name}_{dlf_b_name}/'
        if not folder_exists(save_folder):
            create_directory(save_folder)
        # if os.path.isfile(save_folder + api['api_name'] + '.json'):
        #     print('json file already exists: ', api['api_name'])
        #     continue
        with open(save_folder + api['api_name'] + '.json', 'w', encoding='utf-8') as outfile:
            outfile.write('[' + '\n')

            print('Now processing: ', index, '/', total, api['api_name'])
            api_a_content = []
            api_b_content = []
            temp = ''
            for lable, value in api.items():

                if value:
                    temp += value
            api_a_content.append(temp)
            for api_b in api_b_json:
                temp2 = ''
                for lable, value in api_b.items():
                    if value:
                        temp2 += value
                api_b_content.append(temp2)
            api_name_product = list(itertools.product([api['api_name']],[x['api_name'] for x in api_b_json]))
            cartesian_product =  [[i,j] for i in api_a_content for j in api_b_content]
            # print(len(api_name_product))
            # print(api_name_product[:2])
            # print(len(cartesian_product))
            # print(cartesian_product[:2])

            num_chunks = (len(cartesian_product) + chunk_size - 1) // chunk_size

            for i in range(num_chunks):

                start = i * chunk_size
                end = min(start + chunk_size, len(cartesian_product))
                chunk = cartesian_product[start:end]
                api_name_chunk = api_name_product[start:end]

                output_data = model.compute_score(chunk,
                                          # max_passage_length,  # a smaller max length leads to a lower latency
                                          weights_for_different_modes=[0.4, 0.2, 0.4])
                print('------------chunk is ', i, '------------')

                for idx, value in enumerate(chunk):
                    # Create a dictionary for each pair
                    result_dict = {
                        dlf_a_name: api_name_chunk[idx][0],
                        dlf_b_name: api_name_chunk[idx][1],
                        'similarity': {
                            'colbert': output_data['colbert'][idx],
                            'sparse': output_data['sparse'][idx],
                            'dense': output_data['dense'][idx],
                            'sparse+dense': output_data['sparse+dense'][idx],
                            'colbert+sparse+dense': output_data['colbert+sparse+dense'][idx]
                        }
                    }
                    print(result_dict)
                    outfile.write(json.dumps(result_dict) + ',\n')
            print('-----------------------------------------')

            outfile.write('{}]' + '\n')
        outfile.close()

def load_api_json(dir1, dir2):
    # 文件路径
    dir1_json = open_file('../CrawlerAPIs/' + dir1 + '/' + dir1 + '_api_list_jsons.json')
    dir2_json = open_file('../CrawlerAPIs/' + dir2 + '/' + dir2 + '_api_list_jsons.json')
    return dir1_json, dir2_json



if __name__ == '__main__':
    model = BGEM3FlagModel('../LLMs/BAAI/bge-m3', use_fp16=True)
    apis_directory = list_subdirectories('../CrawlerAPIs/')
    apis_combination = list(itertools.combinations(apis_directory, 2))
    print()
    for api_pair in apis_combination:
        api_json_a, api_json_b = load_api_json(api_pair[0], api_pair[1])
        print('Now processing: ', api_pair[0], api_pair[1])
        calculate_and_save_similarity_results(api_json_a, api_json_b, api_pair[0], api_pair[1], model)

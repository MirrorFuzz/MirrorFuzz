import json
import csv
import os
import re
import time
from configparser import ConfigParser

from src.utils.utils import list_files, query_llm, list_subdirectories, ensure_directory_exists, \
    calculate_tfidf_similarity, calculate_weighted_similarity, calculate_levenshtein_similarity, get_top_k_similar_apis
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import Levenshtein



import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from Levenshtein import distance as levenshtein_distance


def find_most_similar_string(target, string_list):

    min_distance = float('inf')
    most_similar = None


    for string in string_list:
        distance = Levenshtein.distance(target, string)
        if distance < min_distance:
            min_distance = distance
            most_similar = string

    return most_similar



def find_most_similar_strings_k(target, string_list, k=1):

    distances = []
    most_similar = []

    for string in string_list:
        distance = Levenshtein.distance(target, string)
        distances.append((string, distance))

    distances.sort(key=lambda x: x[1])

    for i in range(min(k, len(distances))):
        most_similar.append(distances[i][0])
    return most_similar


def query_api_info(target_api, api_info_json):
    for api_info in api_info_json:
        if api_info['api_name'] == target_api:
            return api_info

    return None


if __name__ == '__main__':
    issues_directory = list_subdirectories('./result/')

    config = ConfigParser()

    config.read('../config.ini', encoding='utf-8')
    identify_model = config.get('run', 'identify_model')
    similarity_algorithm = config.get('run', 'similarity_algorithm')
    # print(identify_model)
    # print(issues_directory)
    for dlf in issues_directory:
        # dlf_api_info_json = []

        # with open(f'../CrawlerAPIs/{dlf}/{dlf}_api_list_jsons.json', mode='r', encoding='utf-8') as file:
        #     dlf_api_info_json = json.load(file)
        json_files = list_files(f"./result/{dlf}/{identify_model}")
        api_string_list = []
        savedir = f'./result/{dlf}/{identify_model}-{similarity_algorithm}-relocate/'
        ensure_directory_exists(savedir)

        with open(f'../CrawlerAPIs/{dlf}/{dlf}_api_list_html.csv', mode='r', encoding='utf-8') as file:
            reader = csv.reader(file)

            api_string_list = [row[0] for row in reader]

        start_time = time.time()
        for jsons in json_files:
            print(jsons)
            with open(jsons, 'r') as f:
                data = json.load(f)
                for issue in data:
                    # print(issue)
                    print(issue['url'])
                    if issue.get('annotation', []) != []:
                        # print(issue['annotation'])
                        for annotation in issue['annotation']:
                            print(annotation['api'])
                            # most_similar = find_most_similar_strings_k(annotation['api'], api_string_list, 1)
                            if similarity_algorithm == 'tf-idf':
                                tfidf_similarities = calculate_tfidf_similarity(annotation['api'], api_string_list)
                                top_k_tfidf_apis, top_k_tfidf_similarities = get_top_k_similar_apis(annotation['api'], api_string_list,
                                                                                                    tfidf_similarities)
                                for i, api in enumerate(top_k_tfidf_apis):
                                    print(f"{i + 1}. {api} (相似度: {top_k_tfidf_similarities[i]:.4f})")
                                    if top_k_tfidf_similarities[i] == 0:

                                        annotation['api'] = None
                            elif similarity_algorithm == 'levenshtein':

                                levenshtein_similarities = calculate_levenshtein_similarity(annotation['api'], api_string_list)
                                top_k_levenshtein_apis, top_k_levenshtein_similarities = get_top_k_similar_apis(annotation['api'],
                                                                                                                api_string_list,
                                                                                                                levenshtein_similarities)
                                for i, api in enumerate(top_k_levenshtein_apis):
                                    print(f"{i + 1}. {api} (相似度: {top_k_levenshtein_similarities[i]:.4f})")
                                    annotation['api'] = api
                            elif similarity_algorithm == 'leven-tf':

                                weighted_similarities = calculate_weighted_similarity(annotation['api'], api_string_list,
                                                                                      levenshtein_weight=0.4,
                                                                                      tfidf_weight=0.6)
                                top_k_weighted_apis, top_k_weighted_similarities = get_top_k_similar_apis(annotation['api'],
                                                                                                          api_string_list,
                                                                                                          weighted_similarities)
                                for i, api in enumerate(top_k_weighted_apis):
                                    print(f"{i + 1}. {api} (相似度: {top_k_weighted_similarities[i]:.4f})")
                                    annotation['api'] = api

                            time.sleep(1)
                    print('----' * 10)

            with open(savedir + os.path.basename(jsons), 'w') as f:
                json.dump(data, f)

        end_time = time.time()
        print(f"Total time: {end_time - start_time:.2f} seconds")


import ast
import csv
import glob
import json
import os
from configparser import ConfigParser
import time

import Levenshtein

from APIsMatcher.Mather import calc_text_and_sem_sim
from synthesis import synthesis
from utils.log import setup_logging
from utils.utils import file_exists, folder_exists, get_now_time, create_directory, list_files, \
    calculate_levenshtein_similarity, get_top_k_similar_apis, calculate_tfidf_similarity, calculate_weighted_similarity, \
    clear_folder


def logger_config(log_path):
    if not folder_exists(log_path):
        create_directory(log_path)
    return setup_logging(f'{log_path}/run.log')


def read_config():
    config = ConfigParser()

    config.read('./config.ini', encoding='utf-8')

    generation_number = int(config.get('run', 'generation_number'))

    timeout = int(config.get('run', 'timeout'))
    save_folder = config.get('run', 'save_folder')
    test_deep_learning_framework = config.get('run', 'test_deep_learning_framework').split(',')
    similarity_algorithm = config.get('run', 'similarity_algorithm')
    super_parameter_sim_K = int(config.get('run', 'super_parameter_sim_K'))
    llm_model = config.get('run', 'llm_model')
    llm_model_ip = config.get('run', 'llm_model_ip')
    llm_model_port = config.get('run', 'llm_model_port')
    super_parameter_crash_K = int(config.get('run', 'super_parameter_crash_K'))



    new_test_directory = save_folder
    logger_path = new_test_directory + '/log'
    logger = logger_config(logger_path)

    init_result_directory(new_test_directory, test_deep_learning_framework)
    logger.info("----------------------------MirrorFuzz Config----------------------------")
    logger.info(f'1. generation_number: {generation_number}')
    logger.info(f'2. timeout: {timeout}')
    logger.info(f'3. save_folder: {save_folder}')
    logger.info(f'4. test_deep_learning_framework: {test_deep_learning_framework}')
    logger.info(f'5. llm_model: {llm_model}')
    logger.info("-------------------------------------------------------------------------")

    return generation_number, timeout, new_test_directory, test_deep_learning_framework, similarity_algorithm, llm_model, llm_model_ip, llm_model_port, super_parameter_sim_K, super_parameter_crash_K, logger


def init_result_directory(path, dlf):
    crash_path = path + '/crash'
    hang_path = path + '/hang'
    crash_pool_path = path + '/crash_pool'
    test_case_pool_path = path + '/seed_pool'
    runtime_path = path + '/runtime'
    api_list_path = path + '/api_list_tested'
    if not folder_exists(crash_path):

        for framework in dlf:
            create_directory(crash_path + '/' + framework)

    if not folder_exists(hang_path):

        for framework in dlf:
            create_directory(hang_path + '/' + framework)

    if not folder_exists(crash_pool_path):

        for framework in dlf:
            create_directory(crash_pool_path + '/' + framework)

    if not folder_exists(test_case_pool_path):
        for framework in dlf:
            create_directory(test_case_pool_path + '/' + framework)

    if not folder_exists(runtime_path):
        create_directory(runtime_path)

    if not folder_exists(api_list_path):
        for framework in dlf:
            create_directory(api_list_path + '/' + framework)


def read_api_list(dlf):
    dlf_result = {}
    for dl_dir in dlf:
        dlf_dir_path = f'./CrawlerAPIs/{dl_dir}/'
        dlf_result[dl_dir] = []

        if folder_exists(dlf_dir_path):

            csv_file_path = dlf_dir_path + dl_dir + '_api_list_html.csv'
            if os.path.exists(csv_file_path):
                # logger.info(csv_files[0])
                with open(csv_file_path, mode='r', encoding='utf-8') as file:
                    reader = csv.reader(file)

                    api_list = [row[0] for row in reader]
                    dlf_result[dl_dir].extend(api_list)

            else:
                logger.info('No CSV files found in ' + dl_dir + ' folder')
                return None
        else:
            logger.info('Folder ' + dl_dir + ' not found')
            return None
    if dlf_result:
        return dlf_result
    logger.info('Deep Learning Framework' + dlf + ' not found, please check config.ini')
    return None


def query_similar_api_levenshtein(target_api, api_dict, k):

    most_similar_dict = {key: [] for key in api_dict}

    for framework, apis in api_dict.items():
        distances = []

        for api in apis:
            distance = Levenshtein.distance(target_api, api)
            distances.append((api, distance))

        distances.sort(key=lambda x: x[1])

        for i in range(min(k, len(distances))):
            most_similar_dict[framework].append(distances[i][0])

    return most_similar_dict


def filter_keywords(target):
    if target == 'oneflow' or target == 'pytorch' or target == 'tensorflow' or target == 'jittor' \
            or target == 'tf' or target == 'torch' or target == 'flow':
        return False
    return True


def query_dlf_crash(target_api_list, dlf, model, similarity_algorithm, super_parameter_crash_K):
    result = []
    for target_api in target_api_list:
        issue_files = list_files(f'./IdentifyAPIs/result/{dlf}/Qwen2-7B-Instruct-AWQ-leven-tf-relocate/')
        for issue_file in issue_files:
            with open(issue_file, mode='r', encoding='utf-8') as file:
                issues = json.load(file)
                for crash_api in issues:
                    for annotation in crash_api['annotation']:
                        if target_api == annotation['api'] and filter_keywords(annotation['api']):
                            result.append(crash_api)
                            if len(result) >= super_parameter_crash_K:
                                return result
    return result


def skip_api(test_api, test_dlf, save_folder):
    try:
        with open(f'{save_folder}/api_list_tested/{test_dlf}/api_list.txt', 'r') as f:
            api_list = f.read()
        for api in api_list.split('\n'):
            if test_api == api:
                print('Skip ' + test_api)
                return True
        return False
    except:

        return False


if __name__ == '__main__':
    (generation_number, timeout, save_folder, test_deep_learning_framework,
     similarity_algorithm, llm_model, llm_model_ip, llm_model_port, super_parameter_sim_K, super_parameter_crash_K,
     logger) = read_config()
    test_all_start_time = time.time()

    for test_dlf in test_deep_learning_framework:

        test_dlf_start_time = time.time()
        test_api_list = read_api_list([test_dlf])
        test_current_api_list = test_api_list[test_dlf]
        length_test_api_list = len(test_current_api_list)
        for index, test_api in enumerate(test_current_api_list):


            if skip_api(test_api, test_dlf, save_folder):
                continue
            logger.info(f'Test {test_dlf} api [{index}/{length_test_api_list}]: {test_api}')
            dlf_api_list = read_api_list(test_deep_learning_framework)

            test_op_api_similar_list = {key: [] for key in dlf_api_list}
            test_ps_api_similar_list = {key: [] for key in dlf_api_list}

            for framework, api_list in dlf_api_list.items():
                if similarity_algorithm == 'levenshtein':

                    levenshtein_similarities = calculate_levenshtein_similarity(test_api, api_list)
                    top_k_levenshtein_apis, top_k_levenshtein_similarities = get_top_k_similar_apis(test_api,
                                                                                                    api_list,
                                                                                                    levenshtein_similarities,
                                                                                                    K=super_parameter_sim_K)
                    test_op_api_similar_list[framework], test_ps_api_similar_list[framework] = {module: score for module, score in
                                                        zip(top_k_levenshtein_apis, top_k_levenshtein_similarities) if
                                                        score != 0}
                elif similarity_algorithm == 'tf-idf':
                    tfidf_similarities = calculate_tfidf_similarity(test_api, api_list)
                    top_k_tfidf_apis, top_k_tfidf_similarities = get_top_k_similar_apis(test_api, api_list,
                                                                                        tfidf_similarities,
                                                                                        K=super_parameter_sim_K)
                    test_op_api_similar_list[framework], test_ps_api_similar_list[framework] = {module: score for module, score in
                                                        zip(top_k_tfidf_apis, top_k_tfidf_similarities) if score != 0}
                elif similarity_algorithm == 'leven-tf':
                    weighted_similarities = calculate_weighted_similarity(test_api, api_list,
                                                                          levenshtein_weight=0.4,
                                                                          tfidf_weight=0.6)
                    top_k_weighted_apis, top_k_weighted_similarities = get_top_k_similar_apis(test_api,
                                                                                              api_list,
                                                                                              weighted_similarities,
                                                                                              K=super_parameter_sim_K)
                    test_op_api_similar_list[framework], test_ps_api_similar_list[framework] = {module: score for module, score in
                                                        zip(top_k_weighted_apis, top_k_weighted_similarities) if
                                                        score >= 0.25}
                elif similarity_algorithm == 'both':
                    query_sim_start_time = time.time()
                    test_op_api_similar_list[framework], test_ps_api_similar_list[framework] = calc_text_and_sem_sim(test_api, test_dlf, framework, "both")
                    query_sim_end_time = time.time()
                    print('query_sim_time:', query_sim_end_time - query_sim_start_time)

            crash_op_api_list = {key: [] for key in test_op_api_similar_list}
            crash_ps_api_list = {key: [] for key in test_ps_api_similar_list}

            for framework, similar_api in test_op_api_similar_list.items():

                query_content = query_dlf_crash(similar_api, framework, llm_model, similarity_algorithm,
                                                super_parameter_crash_K)

                crash_op_api_list[framework].extend(query_content)
                print(len(query_content), 'operation sim crash in', framework)


            for framework, similar_api in test_ps_api_similar_list.items():

                query_content = query_dlf_crash(similar_api, framework, llm_model, similarity_algorithm,
                                                super_parameter_crash_K)

                crash_ps_api_list[framework].extend(query_content)
                print(len(query_content), 'parameter sim crash in', framework)

            synthesis(test_dlf, test_api, crash_op_api_list, "operation", generation_number, timeout, save_folder, llm_model,
                      llm_model_ip, llm_model_port)

            synthesis(test_dlf, test_api, crash_ps_api_list, "parameter", generation_number, timeout, save_folder, llm_model,
                      llm_model_ip, llm_model_port)

            with open(f'{save_folder}/api_list_tested/{test_dlf}/api_list.txt', 'a') as f:
                f.write(f'{test_api}\n')

        test_dlf_end_time = time.time()
        logger.info(f'Test time cost in {test_dlf} framework: {test_dlf_end_time - test_dlf_start_time:.2f}s')
    test_all_end_time = time.time()
    logger.info(f'Total test time cost: {test_all_end_time - test_all_start_time:.2f}s')

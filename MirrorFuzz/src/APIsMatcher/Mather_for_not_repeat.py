import json
import time
from collections import Counter

import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
import json



def get_semantic_similarity(source_name, target_names, source_dl_framework, target_dl_framework, type):

    score = []
    current_dir = os.path.dirname(os.path.abspath(__file__))

    handle_path = os.path.join(current_dir, '.', 'results', source_dl_framework + "_" + type + "/" + target_dl_framework)




    for filename in os.listdir(handle_path):
        if filename.endswith('.json') and os.path.splitext(filename)[0] == source_name[0]:
            with open(handle_path + "/" + filename, 'r') as f:
                data = json.load(f)
                # print(data[:10])
                for api in target_names:
                    # print(api)
                    for sim_data in data:
                        if api == sim_data['API']:
                            score.append(sim_data['similarity'])
    return score


def calculate_similarity(source_api, all_target_apis, target_apis, source_dl_framework, target_dl_framework,
                         sim_type, topk, alpha, h, calc_type="operation_sim"):
    # 准备文档
    name_documents = [source_api.get('name', '').split('.')[-1]]
    params_documents = [source_api.get('params', '')]
    desc_documents = [source_api.get('desc', '')]

    for t in target_apis:
        name_documents.append(t.get('name', '').split('.')[-1])
        params_documents.append(t.get('params', ''))
        desc_documents.append(t.get('desc', ''))


    name_vectorizer = TfidfVectorizer()
    params_vectorizer = TfidfVectorizer()
    desc_vectorizer = TfidfVectorizer()

    name_tfidf_matrix = name_vectorizer.fit_transform(name_documents)
    params_tfidf_matrix = params_vectorizer.fit_transform(params_documents)
    desc_tfidf_matrix = desc_vectorizer.fit_transform(desc_documents)


    name_cosine_similarities = cosine_similarity(name_tfidf_matrix[0:1], name_tfidf_matrix[1:]).flatten()
    params_cosine_similarities = cosine_similarity(params_tfidf_matrix[0:1], params_tfidf_matrix[1:]).flatten()
    desc_cosine_similarities = cosine_similarity(desc_tfidf_matrix[0:1], desc_tfidf_matrix[1:]).flatten()

    source_name = [source_api['name']] if 'name' in source_api else [""]
    source_params = [source_api['params']] if 'params' in source_api else [""]
    source_desc = [source_api['desc']] if 'desc' in source_api else [""]

    target_names = []
    target_params = []
    target_desc = []
    for t in target_apis:
        target_names.append(t['name'] if 'name' in t else [""])
        target_params.append(t['params'] if 'params' in t else [""])
        target_desc.append(t['desc'] if 'desc' in t else [""])




    start_time = time.time()
    semantics_name_similarities = get_semantic_similarity(source_name, target_names, source_dl_framework,
                                                          target_dl_framework, "name")
    semantics_params_similarities = get_semantic_similarity(source_name, target_names, source_dl_framework,
                                                            target_dl_framework, "para")
    semantics_desc_similarities = get_semantic_similarity(source_name, target_names, source_dl_framework,
                                                          target_dl_framework, "desc")
    end_time = time.time()



    similarities = {}

    for i in range(len(target_apis)):
        api_name = target_apis[i]['name']



        text_similarity = max(
            (name_cosine_similarities[i] + params_cosine_similarities[i]) / 2,
            (desc_cosine_similarities[i] + params_cosine_similarities[i]) / 2
        )
        semantics_similarity = max(
            (semantics_name_similarities[i] + semantics_params_similarities[i]) / 2,
            (semantics_desc_similarities[i] + semantics_params_similarities[i]) / 2
        )

        param_text_similarity = params_cosine_similarities[i]
        param_semantics_similarity = semantics_params_similarities[i]

        # only text
        if sim_type == "text":
            similarities[api_name] = {
                'text_similarity': text_similarity,
                'semantics_similarity': semantics_similarity,
                'final_similarity': text_similarity
            }
        # # only sim
        if sim_type == "sem":
            similarities[api_name] = {
                'text_similarity': text_similarity,
                'semantics_similarity': semantics_similarity,
                'final_similarity': semantics_similarity
            }
        # both
        if sim_type == "both":
            similarities[api_name] = {
                'text_similarity': text_similarity,
                'semantics_similarity': semantics_similarity,
                "param_text_similarity": param_text_similarity,
                "param_semantics_similarity": param_semantics_similarity,
                'final_similarity': alpha * text_similarity + (1 - alpha) * semantics_similarity,
                "param_final_similarity": alpha * param_text_similarity + (1 - alpha) * param_semantics_similarity
            }


    sorted_op_similarities = sorted(similarities.items(), key=lambda item: item[1]['final_similarity'], reverse=True)
    sorted_ps_similarities = sorted(similarities.items(), key=lambda item: item[1]['param_final_similarity'], reverse=True)



    top_k_op_similarities = sorted_op_similarities[:topk]

    for api_name, similarity in sorted_op_similarities:
        # if calc_type == "operation_sim":
        #     print(api_name, similarity)
        if similarity['final_similarity'] > h:
            top_k_op_similarities.append((api_name, similarity))


    temp_api_list = {item[0] for item in top_k_op_similarities}

    sorted_api_names = set(api_name for api_name, _ in top_k_op_similarities)

    filtered_similarities2 = [(api_name, similarity) for api_name, similarity in sorted_ps_similarities
                              if api_name not in sorted_api_names]


    resorted_ps_similarities = sorted(filtered_similarities2, key=lambda item: item[1]['param_final_similarity'],
                                           reverse=True)

    top_k_ps_similarities = resorted_ps_similarities[:topk]
    for api_name, similarity in resorted_ps_similarities:

        if similarity['final_similarity'] > h:
            top_k_ps_similarities.append((api_name, similarity))



    return top_k_op_similarities, top_k_ps_similarities


def find_most_common_param(api_data, k=1):
    result = {}

    for framework, apis in api_data.items():
        param_counter = Counter()
        for api in apis:
            params = api.get("params", "")

            param_counter[params] += 1

        most_common_params = param_counter.most_common(k)
        result[framework] = [
            {"param": param, "count": count} for param, count in most_common_params
        ]

    return result


# def get_random_buggy_api(target_dl_framework, param, topk):
#     with open(f"../IdentifyAPIs/{target_dl_framework}/result.json", mode='r', encoding='utf-8') as file:
#


def calc_text_and_sem_sim(source_api,source_dl_framework,target_dl_framework,sim_type):
    # print(os.path.relpath('./results/target_filtered.json'))

    current_dir = os.path.dirname(os.path.abspath(__file__))

    file_path = os.path.join(current_dir, '.', 'results', 'target_filtered.json')
    with open(file_path, mode='r', encoding='utf-8') as file:
        all_target_apis = json.load(file)

    most_common_params = find_most_common_param(all_target_apis, 20)

    alpha = 0.35
    topk = 6
    os_sim_h = 0.50
    ps_sim_h = 0.50
    if source_dl_framework == target_dl_framework:
        os_sim_h = 0.55
        ps_sim_h = 0.55

    source_api_info = {}
    for target_api in all_target_apis[source_dl_framework]:
        if target_api['name'] == source_api:
            source_api_info = target_api

    if source_api_info == {}:
        print(f"{source_api} not found in {source_dl_framework}")
        exit(0)
    else:
        pass

    target_apis = []
    for target_api in all_target_apis:
        if target_api == target_dl_framework:
            target_apis.extend(all_target_apis[target_api])
            break

    top_k_os_similarities, top_k_ps_similarities = calculate_similarity(source_api_info, all_target_apis, target_apis, source_dl_framework,
                                              target_dl_framework, sim_type, topk, alpha, os_sim_h, calc_type="operation_sim")


    # top_k_ps_similarities = calculate_similarity(source_api_info, all_target_apis, api_name_list_without_os, source_dl_framework,
    #                                           target_dl_framework, sim_type, topk, alpha, ps_sim_h, calc_type="parameter_sim")
    os_result = {}
    ps_result = {}

    # for api_name, similarity in top_k_ps_similarities:
    #
    #     ps_result.append((source_api['name'], api_name))



    for api_name, similarity in top_k_os_similarities:
        os_result.update({api_name: similarity['final_similarity']})

    for api_name, similarity in top_k_ps_similarities:
        if source_api_info['name'] == api_name:
            continue
        for dl in most_common_params:
            # print(most_common_params[dl])
            for api in most_common_params[dl]:
                # print(api['param'], api['count'])
                if source_api_info['params'] == api['param']:
                    continue
        ps_result.update({api_name: similarity['final_similarity']})

    # if len(os_result) < topk:
    #     buggy_api_list = get_random_buggy_api(target_dl_framework, len(os_result), topk)
    # if len(ps_result) == 0:
    #     ps_result = os_result

    return os_result, ps_result

import os
import time
import json
from groq import Groq

from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer


ELASTIC_URL = os.getenv("ELASTIC_URL", "http://elasticsearch:9200")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "your-api-key-here")

groq_client =  Groq(api_key = GROQ_API_KEY)
es_client = Elasticsearch(ELASTIC_URL)


model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


# def elastic_search_text(query, course, index_name="course-questions"):
#     search_query = {
#         "size": 5,
#         "query": {
#             "bool": {
#                 "must": {
#                     "multi_match": {
#                         "query": query,
#                         "fields": ["question^3", "text", "section"],
#                         "type": "best_fields",
#                     }
#                 },
#                 "filter": {"term": {"course": course}},
#             }
#         },
#     }

#     response = es_client.search(index=index_name, body=search_query)
#     return [hit["_source"] for hit in response["hits"]["hits"]]


def elastic_search_knn(field, vector, group, index_name="vietnamese-questions"):
    knn = {
        "field": field,
        "query_vector": vector,
        "k": 5,
        "num_candidates": 10000,
        "filter": {"term": {"group": group}},
    }

    search_query = {
        "knn": knn,
        "_source": ["group", "context", "question", "answer", "id"],
    }

    es_results = es_client.search(index=index_name, body=search_query)

    return [hit["_source"] for hit in es_results["hits"]["hits"]]


def build_prompt(query, search_results):
    prompt_template = """
You're an assistant working in customer service. Your job is to provide answers to users' questions. Answer the QUESTION based on the CONTEXT from the documents database.
Use only the facts from the CONTEXT when answering the QUESTION. Provide answer in Vietnamese , in normal text form, not using any markdown form, no need to rewrite the question and make sure that is an answer, not listing questions. Also make sure that the answer provides most information from the CONTEXT as possible .

QUESTION: {question}

CONTEXT: 
{context}
""".strip()

    context = "\n\n".join(
        [
            f"group: {doc['group']}\nquestion: {doc['question']}\nanswer: {doc['answer']}\ncontext: {doc['context'][:1000]}"
            for doc in search_results
        ]
    )
    return prompt_template.format(question=query, context=context).strip()


def llm(prompt, model_choice):
    start_time = time.time()
    if model_choice.startswith('groq/'):
        response = groq_client.chat.completions.create(
            model=model_choice.split('/')[-1],
            messages=[{"role": "user", "content": prompt}]
        )
        answer = response.choices[0].message.content
        tokens = {
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens
        }
    else:
        raise ValueError(f"Unknown model choice: {model_choice}")
    
    end_time = time.time()
    response_time = end_time - start_time
    
    return answer, tokens, response_time


def evaluate_relevance(question, answer):
    prompt_template = """
    You are an expert evaluator for a Retrieval-Augmented Generation (RAG) system.
    Your task is to analyze the relevance of the generated answer to the given question.
    Based on the relevance of the generated answer, you will classify it
    as "NON_RELEVANT", "PARTLY_RELEVANT", or "RELEVANT".

    Here is the data for evaluation:

    Question: {question}
    Generated Answer: {answer}

    Please analyze the content and context of the generated answer in relation to the question
    and provide your evaluation in parsable JSON without using code blocks:

    {{
      "Relevance": "NON_RELEVANT" | "PARTLY_RELEVANT" | "RELEVANT",
      "Explanation": "[Provide a brief explanation for your evaluation]"
    }}
    """.strip()

    prompt = prompt_template.format(question=question, answer=answer)
    evaluation, tokens, _ = llm(prompt, 'groq/llama3-8b-8192')
    
    try:
        json_eval = json.loads(evaluation)
        return json_eval['Relevance'], json_eval['Explanation'], tokens
    except json.JSONDecodeError:
        try:
            str_eval = evaluation.rstrip('}') + '}'  # Ensure it ends with a closing brace
            json_eval = json.loads(str_eval)
            return json_eval['Relevance'], json_eval['Explanation'], tokens
        except json.JSONDecodeError:
            return "UNKNOWN", "Failed to parse evaluation", tokens


def calculate_groq_cost(model_choice, tokens):
    groq_cost = 0

    if model_choice == 'groq/llama3-8b-8192':
        groq_cost = (tokens['prompt_tokens'] * 0.0015 + tokens['completion_tokens'] * 0.002) / 1000
    elif model_choice in ['groq/gemma2-9b-it', 'groq/gemma-7b-it']:
        groq_cost = (tokens['prompt_tokens'] * 0.03 + tokens['completion_tokens'] * 0.06) / 1000

    return groq_cost

def get_answer(query, group, model_choice, search_type):
    if search_type == 'Vector':
        vector = model.encode(query)
        search_results = elastic_search_knn('question_context_answer_vector', vector, group)

    prompt = build_prompt(query, search_results)
    answer, tokens, response_time = llm(prompt, model_choice)
    
    relevance, explanation, eval_tokens = evaluate_relevance(query, answer)
    if relevance is None or explanation is None or eval_tokens is None:
        relevance, explanation, eval_tokens = "UNKNOWN", "Failed to evaluate relevance", {'prompt_tokens': 0, 'completion_tokens': 0, 'total_tokens': 0}

    groq_cost = calculate_groq_cost(model_choice, tokens)
 
    return {
        'answer': answer,
        'response_time': response_time,
        'relevance': relevance,
        'relevance_explanation': explanation,
        'model_used': model_choice,
        'prompt_tokens': tokens['prompt_tokens'],
        'completion_tokens': tokens['completion_tokens'],
        'total_tokens': tokens['total_tokens'],
        'eval_prompt_tokens': eval_tokens['prompt_tokens'],
        'eval_completion_tokens': eval_tokens['completion_tokens'],
        'eval_total_tokens': eval_tokens['total_tokens'],
        'groq_cost': groq_cost
    }
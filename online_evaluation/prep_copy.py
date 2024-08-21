import os
import requests
import pandas as pd
from sentence_transformers import SentenceTransformer
from elasticsearch import Elasticsearch
from tqdm.auto import tqdm
from dotenv import load_dotenv
import pickle
import json

from db import init_db

load_dotenv()

ELASTIC_URL = os.getenv("ELASTIC_URL_LOCAL")
MODEL_NAME = os.getenv("MODEL_NAME")
INDEX_NAME = os.getenv("INDEX_NAME")

BASE_PATH = "../data/vietnamese_rag"
BASE_URL = "https://github.com/vucongtuanduong/vietnamese-rag-project/tree/add_files_dev"



def load_documents_json_local(relative_path):
    file_path = f"{BASE_PATH}/{relative_path}"
    with open(file_path, 'rt', encoding='utf-8') as f_in:
            return (json.load(f_in))


def fetch_documents():
    print("Fetching documents...")
    relative_path = "documents-with-ids.json"
    documents = load_documents_json_local(relative_path)
    print(f"Fetched {len(documents)} documents")
    return documents


def fetch_ground_truth():
    print("Fetching ground truth data...")
    relative_path = "ground_truth_data/ground_truth_data.csv"
    ground_truth_path = f"{BASE_PATH}/{relative_path}"
    # print(ground_truth_url)
    df_ground_truth = pd.read_csv(ground_truth_path)
    ground_truth = df_ground_truth.to_dict(orient="records")
    print(f"Fetched {len(ground_truth)} ground truth records")
    return ground_truth

def load_model():
    print(f"Loading model: {MODEL_NAME}")
    return SentenceTransformer(MODEL_NAME)

def setup_elasticsearch():
    print("Setting up Elasticsearch...")
    es_client = Elasticsearch(ELASTIC_URL)

    index_settings = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0
        },
        "mappings": {
            "properties": {
                "group": {"type": "keyword"},
                "context": {"type": "text"},
                "question": {"type": "text"},
                "answer": {"type": "text"},
                "id": {"type": "keyword"},
                "question_vector": {
                    "type": "dense_vector",
                    "dims": 384,
                    "index": True,
                    "similarity": "cosine"
                }
            }
        }
    }

    es_client.indices.delete(index=INDEX_NAME, ignore_unavailable=True)
    es_client.indices.create(index=INDEX_NAME, body=index_settings)
    print(f"Elasticsearch index '{INDEX_NAME}' created")
    return es_client


def load_documents_json(relative_url):
    docs_url = f"{BASE_URL}/{relative_url}?raw=1"
    docs_response = requests.get(docs_url)
    document = docs_response.json()
    return document

def load_vectors(file_path):
    with open(file_path, 'rb') as file:
        return pickle.load(file)

def process_documents_new(es_client, documents, model):
    # json_path = f"{BASE_PATH}/documents-with-ids{i}.json"
    for doc in tqdm(documents):
        question = doc["question"]
        doc["question_vector"] = model.encode(question).tolist()
        es_client.index(index=INDEX_NAME, document=doc)

def process_documents(es_client):
    # json_path = f"{BASE_PATH}/documents-with-ids{i}.json"
    pickle_path = f"{BASE_PATH}/question_vector_pickle/question_vector.pkl"
    json_relative_path = "documents-with-ids.json"
    data = load_documents_json_local(json_relative_path)
    document_question_vector_list = load_vectors(pickle_path)

    for j in range(len(data)):
        data[j]['question_vector'] = document_question_vector_list[j]['question_vector']
    
    for doc in tqdm(data):
        es_client.index(index=INDEX_NAME, document=doc)

def index_documents(es_client, documents, model):
    print("Indexing documents...")
    # process_documents(es_client)
    process_documents_new(es_client, documents, model)
    print(f"Indexed {len(documents)} documents")

def main():
    print("Starting the indexing process...")

    documents = fetch_documents()
    ground_truth = fetch_ground_truth()
    model = load_model()
    es_client = setup_elasticsearch()
    index_documents(es_client, documents, model)

    print("Initializing database...")
    # create_database()
    init_db()

    print("Indexing process completed successfully!")

if __name__ == "__main__":
    main()
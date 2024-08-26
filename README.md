# Vietnamese RAG Project

## Introduction
This project aims to develop a simple Retrieval-Augmented Generation (RAG) model for generating Vietnamese text. By leveraging state-of-the-art machine learning techniques and comprehensive datasets, this project seeks to enhance the quality and relevance of generated text, assisting in various natural language processing tasks.

## Table of Contents

- [Tech stack](#tech-stack)
- [Dataset](#dataset)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Data](data/README.md)
- [Data Ingestion and Preparation](data_ingestion_and_preparation/README.md)
- [Evaluation](evaluation/README.md)
- [Grafana](grafana/README.md)
- [User Interface and online evaluation](UI_and_online_evaluation/README.md)
- [(Optional) My tasks to prepare data for this project- in other repository](#optional)



## Tech Stack
- **Programming Language**: Python
- **Libraries**: PyTorch, Transformers, Scikit-learn, Pandas, NumPy, Matplotlib
- **Search Engine**: Elastic Search
- **Embeddings**: Vector embeddings
- **Containerization**: Docker
- **Web Framework**: Streamlit
- **Database**: PostgreSQL
- **Monitoring**: Grafana


## Dataset
As a Vietnamese speaker, I thought of creating a simple Vietnamese RAG project for my final project. I found Vietnamese RAG datasets on Huggingface.

This is the link to my datasets: [My datasets](https://huggingface.co/datasets/DuyTa/vi_RAG/viewer/LegalRAG)

This dataset has four subsets, but I only use three of them: General Text, Legal, and Expert.

- The General subset contains data scraped from various internet sources, like newspapers, and includes text related to news.

- The Legal subset is about Vietnamese law.

- The Expert subset covers various fields, such as law, political science, biology, and physics.


## Project Structure

```bash
.
├── README.md
├── UI_and_online_evaluation
├── data
│   ├── README.md
│   └── vietnamese_rag
│       ├── answer_vector_pickle
│       ├── context_vector_pickle
│       ├── documents-with-ids.json
│       ├── documents-with-ids1.json
│       ├── documents-with-ids2.json
│       ├── documents-with-ids3.json
│       ├── documents-with-ids4.json
│       ├── documents-with-ids5.json
│       ├── documents.json
│       ├── evaluations_aqa
│       ├── evaluations_qa
│       ├── ground_truth_data
│       ├── llm_answer
│       ├── llm_answer_cosine.csv
│       ├── question_context_answer_vector_pickle
│       └── question_vector_pickle
├── data_ingestion_and_preparation
│   ├── README.md
│   ├── create_vector_embeddings.ipynb
│   └── load_datasets_and_create_documents.ipynb
├── evaluation
│   ├── README.md
│   ├── llm_answer_evaluation.ipynb
│   ├── llm_as_a_judge_aqa_evaluation.ipynb
│   ├── llm_as_a_judge_qa_evaluation.ipynb
│   └── retrieval_evaluation.ipynb
├── grafana
├── images
├── n.txt
└── requirements.txt
```

## Setup

I recommend you create a github codespace to run this repository

At the root directory, run this command to install dependencies:

```bash
pip install -r requirements.txt
```

## Optional

Before creating this repository, I created another repository to clean the datasets I chose from Huggingface. The data was too large, and I faced rate limits when calling the API, so I had to split it into many chunks and run them separately. This took a lot of time. If you want to understand more about how I did this, you can check this [repository](https://github.com/PTIT-D22KH/rag-experiment)
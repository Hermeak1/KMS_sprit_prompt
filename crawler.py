import requests
from bs4 import BeautifulSoup
import chromadb
import api_manager

MAX_DOC_LENGTH = 200


def crawl_page(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")
    texts = []
    for p in soup.find_all(["p", "li"]):
        text = p.get_text(strip=True)
        if len(text) > 20:
            texts.append(text[:MAX_DOC_LENGTH])
    return texts


def setup_collection():
    print("아르카나 데이터 수집 중...")
    arcana_texts = crawl_page("https://namu.wiki/w/신비의%20숲%20아르카나")
    story_texts  = crawl_page("https://namu.wiki/w/신비의%20숲%20아르카나/스토리%20및%20퀘스트")
    all_texts = list(dict.fromkeys(arcana_texts + story_texts))
    print(f"총 {len(all_texts)}개 문서 수집 완료 (중복 제거 후)")

    chroma_client = chromadb.Client()
    collection = chroma_client.create_collection(
        name="arcana",
        embedding_function=api_manager.call_api()
    )
    collection.add(
        documents=all_texts,
        ids=[f"doc_{i}" for i in range(len(all_texts))]
    )
    print("ChromaDB 저장 완료")
    return collection

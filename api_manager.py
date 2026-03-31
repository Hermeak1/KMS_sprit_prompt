import os
from dotenv import load_dotenv
from chromadb.utils import embedding_functions

load_dotenv()

#region openai gpt
def call_api():
    return embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name="text-embedding-3-small"
    )
#endregion

#region google gemini
"""
def call_api():
    return embedding_functions.GoogleGenerativeAiEmbeddingFunction(
        model_name="gemini-embedding-001"
    )
"""
#endregion

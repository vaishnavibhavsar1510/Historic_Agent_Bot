# backend/app/monument_search.py

import json
import os
from typing import List, Dict

from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from backend.app.config import settings

# Path to your local JSON file containing monument data
DATA_PATH = os.path.join(os.path.dirname(__file__), "../../data/monuments.json")


class MonumentSearch:
    def __init__(self):
        # Initialize OpenAIEmbeddings with your API key
        self.embeddings = OpenAIEmbeddings(openai_api_key=settings.openai_api_key)

        # Load the monuments JSON into a Python list of dicts
        self.monuments = self._load_monuments()

        # Build a FAISS vectorstore from the descriptions
        self.vectorstore = self._build_vectorstore()

    def _load_monuments(self) -> List[Dict]:
        """
        Load the JSON file at DATA_PATH and return a list of monuments,
        each being a dict with at least 'name', 'location', and 'description' keys.
        """
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)

    def _build_vectorstore(self):
        """
        Create a FAISS index from the monuments' descriptions. Each text entry
        is the 'description' field, and metadata includes name & location.
        """
        texts = [m["description"] for m in self.monuments]
        metadatas = [{"name": m["name"], "location": m["location"]} for m in self.monuments]

        # Build and return a FAISS vectorstore
        return FAISS.from_texts(texts, self.embeddings, metadatas=metadatas)

    def search(self, query: str, k: int = 2) -> List[Dict]:
        """
        Perform a similarity search on the FAISS index using the query.
        Returns up to 'k' results as a list of dicts, each containing:
        { "name": ..., "location": ..., "description": ... }.
        """
        results = self.vectorstore.similarity_search(query, k=k)
        return [
            {
                "name": r.metadata["name"],
                "location": r.metadata["location"],
                "description": r.page_content
            }
            for r in results
        ]


# Instantiate a singleton for use elsewhere in the app
monument_search = MonumentSearch()

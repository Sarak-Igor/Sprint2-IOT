import asyncio
from backend.apps.ai_knowledge.vector_store import _embed_texts
from dotenv import load_dotenv

load_dotenv()

async def main():
    print("Testing embeddings...")
    try:
        embeddings = _embed_texts(["This is a test"])
        print(f"Success! Dimension: {len(embeddings[0])}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

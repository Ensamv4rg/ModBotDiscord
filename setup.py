import asyncio
from concurrent.futures import ThreadPoolExecutor
from transformers import pipeline

def setup():
    executor = ThreadPoolExecutor(max_workers=4)
    semaphore = asyncio.Semaphore(4)


    classifier = pipeline(
        "zero-shot-classification",
        model="facebook/bart-large-mnli",
        device=-1
    )
setup()
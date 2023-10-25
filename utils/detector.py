from filecache import filecache
from langdetect import detect
from transformers import pipeline
import torch


@filecache(7 * 24 * 60 * 60)
def detector(text: str) -> str:
    try:
        return detect(text)
    except:
        return None

import re
from collections import Counter

from beartype import beartype


@beartype
def count_words(text: str) -> tuple[int, Counter]:
    words = re.findall(r"\b\w+\b", text.lower())
    return len(words), Counter(words)


@beartype
def clean_block(text: str) -> str:
    text = re.sub(r"-\n(\w)", r"\1", text)
    text = re.sub(r"\s*\n\s*", " ", text)
    return re.sub(r"\s{2,}", " ", text).strip()

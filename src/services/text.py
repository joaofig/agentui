import re

from beartype import beartype


@beartype
def count_words(text: str) -> int:
    words = re.findall(r"\b\w+\b", text.lower())
    return len(words)


@beartype
def clean_block(text: str) -> str:
    text = re.sub(r"-\n(\w)", r"\1", text)
    text = re.sub(r"\s*\n\s*", " ", text)
    return re.sub(r"\s{2,}", " ", text).strip()

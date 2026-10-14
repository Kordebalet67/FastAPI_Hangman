# utils.py
def load_words(filename: str) -> list[str]:
    with open(filename, encoding="utf-8") as f:
        return [w.strip().upper() for w in f if w.strip()]

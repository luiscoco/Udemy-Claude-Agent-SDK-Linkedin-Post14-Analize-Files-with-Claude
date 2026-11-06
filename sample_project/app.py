"""Illustrative source file for static analysis; no main() invocation is shown."""
from pathlib import Path


def read_file(path):
    return Path(path).read_text(encoding="utf-8")


def process_text(text):
    return text.strip().lower()


def main():
    text = read_file("input.txt")
    print(process_text(text))

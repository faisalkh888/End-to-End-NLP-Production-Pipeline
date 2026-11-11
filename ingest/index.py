import argparse
from pathlib import Path
from serving.retrieval import make_retriever


def main() -> None:
    parser = argparse.ArgumentParser(description="Incrementally index documentation")
    parser.add_argument("--source", type=Path, default=Path("data/docs"))
    args = parser.parse_args()
    retriever = make_retriever()
    count = retriever.index_directory(args.source)
    print(f"Indexed or updated {count} chunks from {args.source}")


if __name__ == "__main__":
    main()

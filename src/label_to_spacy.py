import json

import click
import spacy
from spacy.tokens import DocBin, Span


class CorpusConverter:
    def __init__(self, label_file: str, save_path: str):
        if not save_path.endswith(".spacy"):
            raise ValueError("save file must have a .spacy extension")
        self.save_path = save_path

        with open(label_file) as in_stream:
            self.label_corpus: list[dict] = json.load(in_stream)

        self.nlp = spacy.load("fr_core_news_lg")
        self.db = DocBin()

    def _convert_corpus(self) -> None:
        for text in self.label_corpus:
            doc = self.nlp(text["text"])
            spans = []

            for annotation in text["label"]:
                for label in annotation["labels"]:
                    # Label has spans in character offset, spacy wants then in token offset, so a little conversion is needed :
                    start_char = annotation["start"]
                    end_char = annotation["end"]

                    start_token = None
                    for i, token in enumerate(doc):
                        if token.idx <= start_char < token.idx + len(token.text):
                            start_token = i
                            break

                    end_token = None
                    for i, token in enumerate(doc):
                        if token.idx <= end_char <= token.idx + len(token.text):
                            end_token = i + 1  # +1 because spans are exclusive of end
                            break

                    if start_token is not None and end_token is not None:
                        spans.append(Span(doc, start_token, end_token, label))
            doc.spans["sc"] = spans
            self.db.add(doc)

    def __call__(self) -> None:
        self._convert_corpus()
        self.db.to_disk(self.save_path)


@click.command(
    help="Converts the annotated corpus from the exported label json into a spacy DocBin, the format used for training."
)
@click.option(
    "--label-file",
    type=str,
    help="Path to the annotated corpus (json file extracted from label studio)",
)
@click.option(
    "--save-path",
    type=str,
    help="Path where to save the spacy training file. Must end with .spacy",
)
def main(label_file: str, save_path: str) -> None:
    cc = CorpusConverter(label_file, save_path)
    cc()


if __name__ == "__main__":
    main()

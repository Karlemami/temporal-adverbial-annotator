import json
from tqdm import tqdm
from pathlib import Path

import click
import spacy


class PreAnnotator:
    """A class to pre-annotate a corpus before loading it into label studio.
    The annotations are saved in label studio's json format.
    """

    def __init__(self, corpus_folder: str, save_folder: str, model: str):
        self.save_folder = self._validate_folder(save_folder)
        self.corpus_files = self._extract_files_from_folder(corpus_folder)
        self.model = spacy.load(model)
        self.counter: int = 0

    def _validate_folder(self, folder: str) -> Path:
        _folder = Path(folder)
        if not _folder.is_dir():
            raise NotADirectoryError

        return _folder

    def _extract_files_from_folder(self, folder: str) -> list[Path]:
        try:
            _folder = self._validate_folder(folder)
        except NotADirectoryError:
            raise

        files = list(_folder.glob("*.txt"))
        if not files:
            raise ValueError(f"The {folder} folder has not txt files.")

        return files

    def _annotate_corpus(self) -> None:
        for file_path in tqdm(self.corpus_files, desc="Annotating files..."):
            file_annotation = self._annotate_file(file_path)
            self._write_annotation_to_file(file_annotation, file_path)

    def _annotate_file(self, file_path: Path) -> dict:
        text = file_path.read_text()
        doc = self.model(text)

        d = {}
        d["data"] = {"text": text}
        d["predictions"] = [{"model_version": 1, "result": []}]
        result = d["predictions"][0]["result"]

        for span in doc.spans["sc"]:
            value = {
                "start": span.start_char,
                "end": span.end_char,
                "text": str(span),
                "labels": [span.label_],
            }

            result.append(
                {
                    "value": value,
                    "id": int(
                        f"{hash(text)}{self.counter}"
                    ),  # The id has to be a unique integer, otherwise the label studio UI will be buggy
                    "from_name": "label",
                    "to_name": "text",
                    "type": "labels",
                    "readonly": False,
                    "hidden": False,
                }
            )
            self.counter += 1

        return d

    def _write_annotation_to_file(self, annotation: dict, file_obj: Path) -> None:
        with open(f"{self.save_folder}/{file_obj.stem}.json", "w") as out_stream:
            json.dump(annotation, out_stream, ensure_ascii=False)

    def __call__(self) -> None:
        self._annotate_corpus()


@click.command()
@click.option(
    "--corpus-folder",
    type=str,
    help="The path to the folder containing the files to annotate (txt files only)",
)
@click.option(
    "--save-folder",
    type=str,
    help="The path to the folder where the annotations are to be saved.",
)
@click.option(
    "--model",
    type=str,
    help='The path to the spacy model used to annotate. Defaults to "../model/v1"',
    default="../model/v1",
)
def main(corpus_folder: str, save_folder: str, model: str) -> None:
    annotator = PreAnnotator(corpus_folder, save_folder, model)
    annotator()


if __name__ == "__main__":
    main()

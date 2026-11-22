"""Treina em JSONL de treino e exporta predições e metadados, sem salvar pickle."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from teor import fit_tfidf, predict_tfidf


def _read_jsonl(path: Path) -> list[dict]:
    records = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{number}: JSON inválido") from exc
        if not isinstance(record, dict):
            raise ValueError(f"{path}:{number}: registro precisa ser um objeto")
        records.append(record)
    return records


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", required=True, type=Path, help="JSONL com split train explícito")
    parser.add_argument("--predict", required=True, type=Path, help="JSONL a classificar")
    parser.add_argument("--pairs", required=True, choices=("gold", "mentions"))
    parser.add_argument("--saida", required=True, type=Path, help="predições JSONL; arquivo novo")
    parser.add_argument("--metadata", required=True, type=Path, help="metadados JSON; arquivo novo")
    args = parser.parse_args(argv)
    inputs = {args.train.resolve(), args.predict.resolve()}
    if args.saida.resolve() == args.metadata.resolve() or inputs & {args.saida.resolve(), args.metadata.resolve()}:
        parser.error("saídas devem ser distintas das entradas e entre si")
    if args.saida.exists() or args.metadata.exists():
        parser.error("arquivos de saída já existem; escolha novos caminhos")
    try:
        training = _read_jsonl(args.train)
        if not training or any(record.get("split") != "train" for record in training):
            raise ValueError("CLI requer registros com split train explícito")
        records = _read_jsonl(args.predict)
        # Impede que uma notícia treinada seja apresentada como validação/teste.
        training_ids = {record.get("article_id") for record in training}
        if any(record.get("article_id") in training_ids and record.get("split") in {"validation", "test"}
               for record in records):
            raise ValueError("notícia de treino também aparece na validação/teste")
        model = fit_tfidf(training)
        predictions = predict_tfidf(model, records, pairs=args.pairs)
        metadata = {
            "training": model.training_metadata_, "pairs": args.pairs,
            "input_sha256": {
                "train": hashlib.sha256(args.train.read_bytes()).hexdigest(),
                "predict": hashlib.sha256(args.predict.read_bytes()).hexdigest(),
            },
            "cli_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "prediction": {
                "paragraphs": len(predictions),
                "pairs": sum(len(record["teor"]) for record in predictions),
                "unmarked_pairs": sum(record["prediction_config"]["unmarked_pairs"] for record in predictions),
            },
        }
        # Serializa tudo antes de abrir as saídas para não gravar JSON parcial.
        output = "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in predictions)
        report = json.dumps(metadata, ensure_ascii=False, indent=2) + "\n"
        with args.saida.open("x", encoding="utf-8") as handle:
            handle.write(output)
        with args.metadata.open("x", encoding="utf-8") as handle:
            handle.write(report)
    except (ValueError, OSError, ImportError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

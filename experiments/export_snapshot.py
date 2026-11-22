"""Exporta o escopo v1 de prisma-dev e audita as candidatas sem alterar a seleção."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
from collections import Counter
from pathlib import Path

import psycopg
import yaml
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "scripts"))
sys.path.insert(0, str(BASE_DIR / "src"))

from export_target_entities import (  # noqa: E402
    build_export_document, load_cargo_by_titulo, load_cargos_from_settings,
)
from entities_store import load_active_entities_from_db  # noqa: E402
from mentions import load_entities_snapshot, predict_mentions  # noqa: E402
from segmentation import segment  # noqa: E402

TARGET_DATABASE = "prisma-dev"
SNAPSHOT_PATH = BASE_DIR / "experiments/data/entidades.yaml"
AUDIT_PATH = BASE_DIR / "experiments/data/preparacao/snapshot-audit.json"
REVALIDATION_PATH = BASE_DIR / "experiments/data/preparacao/candidate-revalidation.json"
RAW_PATH = BASE_DIR / "data/raw/articles_202608191040.csv"
CANDIDATE_IDS_PATH = BASE_DIR / "experiments/data/preparacao/candidate_ids.txt"
PREVIOUS_SNAPSHOT_PATH = BASE_DIR / "data/exports/target_entities.yaml"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def connect_readonly():
    """Mesmo contrato de ambiente de storage; alvo e proteção locais à conexão."""
    return psycopg.connect(
        host=os.environ["POSTGRES_HOST"], port=os.environ["POSTGRES_PORT"],
        dbname=TARGET_DATABASE, user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"], connect_timeout=5,
        options="-c default_transaction_read_only=on",
    )


def collect_snapshot() -> dict:
    cargos = load_cargos_from_settings()
    conn = connect_readonly()
    try:
        conn.read_only = True
        conn.isolation_level = psycopg.IsolationLevel.REPEATABLE_READ
        with conn.cursor() as cur:
            cur.execute("SELECT current_database()")
            if cur.fetchone()[0] != TARGET_DATABASE:
                raise ValueError("Conexão fora do alvo prisma-dev; exportação cancelada")
        entities = load_active_entities_from_db(conn, cargos)
        cargo_by_titulo = load_cargo_by_titulo(
            conn, [e.id for e in entities if e.entity_type == "politico"])
        document = build_export_document(entities, cargo_by_titulo)
        document["source_database"] = TARGET_DATABASE
        document["scope_cargos"] = cargos
        validate_document(document)
        return document
    finally:
        try:
            conn.rollback()
        finally:
            conn.close()


def validate_document(document: dict) -> None:
    entities = document["entities"]
    if not entities or len({e["entity_id"] for e in entities}) != len(entities):
        raise ValueError("Snapshot vazio ou com IDs duplicados")
    for entity in entities:
        if (entity["entity_type"] not in {"politico", "partido"}
                or not isinstance(entity["entity_id"], str) or not entity["entity_id"].strip()
                or not isinstance(entity["nome_principal"], str) or not entity["nome_principal"].strip()
                or not isinstance(entity["aliases"], list)
                or any(not isinstance(a, str) or not a.strip() for a in entity["aliases"])):
            raise ValueError("Entidade inválida no snapshot")
        if entity["entity_type"] == "politico" and entity["cargo"] not in document["scope_cargos"]:
            raise ValueError("Cargo fora do escopo")
        if entity["entity_type"] == "partido" and entity["cargo"] is not None:
            raise ValueError("Partido com cargo")


def write_json(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True)
                    + "\n", encoding="utf-8")


def export_snapshot(snapshot_path=SNAPSHOT_PATH, audit_path=AUDIT_PATH) -> dict:
    document = collect_snapshot()
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text(yaml.safe_dump(document, allow_unicode=True, sort_keys=False),
                             encoding="utf-8")
    # Leitura pelo consumidor real verifica o contrato do arquivo persistido.
    load_entities_snapshot(snapshot_path)
    counts = dict(Counter(e["entity_type"] for e in document["entities"]))
    audit = {"generated_at": document["generated_at"], "source_database": TARGET_DATABASE,
             "read_only": True, "scope_cargos": document["scope_cargos"],
             "snapshot": str(snapshot_path.relative_to(BASE_DIR)) if snapshot_path.is_relative_to(BASE_DIR)
             else str(snapshot_path), "snapshot_sha256": sha256(snapshot_path),
             "entities": len(document["entities"]), "entity_types": counts,
             "aliases": sum(len(e["aliases"]) for e in document["entities"]),
             "integrity": {"unique_ids": True, "valid_cargos": True,
                           "party_scope": "partidos ativos vinculados às candidaturas pelo loader de produção"}}
    write_json(audit_path, audit)
    return audit


def revalidate_candidates(snapshot=SNAPSHOT_PATH, raw=RAW_PATH,
                          candidate_ids=CANDIDATE_IDS_PATH,
                          previous_snapshot=PREVIOUS_SNAPSHOT_PATH,
                          output=REVALIDATION_PATH) -> dict:
    """Evidência automática de DIR, sem modificar amostra nem consumir anotações."""
    entities = load_entities_snapshot(snapshot)
    previous = load_entities_snapshot(previous_snapshot)
    ids = candidate_ids.read_text(encoding="utf-8").splitlines()
    if len(ids) != len(set(ids)) or any(not i.strip() for i in ids):
        raise ValueError("IDs candidatos inválidos ou duplicados")
    csv.field_size_limit(10**9)
    with raw.open(encoding="utf-8", newline="") as stream:
        articles = {row["id"]: row for row in csv.DictReader(stream)}
    if set(ids) - articles.keys():
        raise ValueError("Candidatas ausentes do CSV bruto")
    records = []
    for article_id in ids:
        article = articles[article_id]
        if article["extraction_status"] != "success" or not article["full_text"].strip():
            raise ValueError("Candidata sem extração utilizável")
        records.extend({"article_id": article_id, "paragraph_index": i, "text": text}
                       for i, text in enumerate(segment("news_article", article["full_text"])))
    predictions = predict_mentions(records, entities, system="recency",
                                   include_party_descriptions=False)
    by_article = {i: Counter() for i in ids}
    for row in predictions:
        by_article[row["article_id"]].update(m["entity_id"] for m in row["mentions"]
                                            if m["type"] == "DIR")
    coverage = Counter()
    for counts in by_article.values():
        coverage.update(counts.keys())
    new_ids = {e.id for e in entities} - {e.id for e in previous}
    result = {"status": "REVALIDACAO_AUTOMATICA_PROVISORIA",
              "scenario": {"system": "recency", "include_party_descriptions": False,
                           "D10": "pendente; cenário sem descrições de partido"},
              "inputs_sha256": {str(p): sha256(p) for p in (snapshot, raw, candidate_ids, previous_snapshot)},
              "articles": [{"article_id": i, "direct_mentions": sum(by_article[i].values()),
                            "entity_ids": sorted(by_article[i]),
                            "eligible_by_direct_match": bool(by_article[i]),
                            "requires_review": not bool(by_article[i])} for i in ids],
              "summary": {"articles": len(ids), "with_direct_match": sum(bool(c) for c in by_article.values()),
                          "without_direct_match": [i for i in ids if not by_article[i]],
                          "entities_covered": len(coverage)},
              "entity_coverage": [{"entity_id": e.id, "name": e.canonical_name,
                                   "articles": coverage[e.id], "new_since_previous_snapshot": e.id in new_ids}
                                  for e in entities],
              "new_entity_ids": sorted(new_ids),
              "selection_modified": False}
    write_json(output, result)
    return result


def main() -> int:
    load_dotenv(BASE_DIR / ".env")
    try:
        audit = export_snapshot()
        result = revalidate_candidates()
    except psycopg.Error:
        # Mensagens do driver podem carregar host, DSN e outros dados privados.
        print("Falha de conexão/consulta em prisma-dev; detalhes privados omitidos.", file=sys.stderr)
        return 1
    print(f"prisma-dev: {audit['entities']} entidades -> {SNAPSHOT_PATH}")
    print(f"Auditoria -> {AUDIT_PATH}; revalidação -> {REVALIDATION_PATH}")
    print(f"Candidatas com DIR: {result['summary']['with_direct_match']}/{result['summary']['articles']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

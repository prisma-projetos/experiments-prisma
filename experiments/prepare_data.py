"""Prepara uma amostra PROVISÓRIA por notícia, sem rótulos ou splits.

Usa a elegibilidade histórica reconstruída da rodada 1. A seleção não
depende do matcher atual, cuja configuração já mudou desde aquela rodada.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import statistics
import sys
import unicodedata
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "src"))

import yaml  # noqa: E402
from segmentation import segment  # noqa: E402

REVIEWERS = ("anderson", "beatriz", "cristovam", "gustavo", "lucas", "nicolas")
STATE = "PROVISORIA"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_ids(path: Path) -> set[str]:
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def canonical_url(value: str) -> str:
    """Ignora fragmento, esquema e parâmetros conhecidos de rastreamento."""
    if not value.strip():
        return ""
    url = urlsplit(value.strip())
    query = sorted((k, v) for k, v in parse_qsl(url.query, keep_blank_values=True)
                   if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid"})
    return urlunsplit(("", url.netloc.lower(), url.path.rstrip("/"), urlencode(query), ""))


def text_hash(text: str) -> str:
    normalized = " ".join(unicodedata.normalize("NFC", text).casefold().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest() if normalized else ""


def duplicate_groups(articles: dict[str, dict]) -> list[set[str]]:
    """Componentes transitivos por URL canônica ou texto completo normalizado."""
    parent = {article_id: article_id for article_id in articles}

    def find(article_id):
        while parent[article_id] != article_id:
            parent[article_id] = parent[parent[article_id]]
            article_id = parent[article_id]
        return article_id

    seen = {}
    for article_id, article in sorted(articles.items()):
        urls = {canonical_url(article.get(key, ""))
                for key in ("canonical_link", "html_canonical_link")}
        if not any(urls):
            urls.add(canonical_url(article.get("resolved_link", "")))
        keys = [("url", url) for url in urls if url]
        content = text_hash(article["full_text"])
        if content:
            keys.append(("text", content))
        for key in keys:
            if key in seen:
                parent[find(article_id)] = find(seen[key])
            else:
                seen[key] = article_id
    groups = {}
    for article_id in sorted(articles):
        groups.setdefault(find(article_id), set()).add(article_id)
    return list(groups.values())


def select_candidates(articles, eligible_ids, round1_ids, pilot_ids, seed=42):
    required = eligible_ids | round1_ids | pilot_ids
    missing = required - articles.keys()
    if missing:
        raise ValueError(f"IDs ausentes da fonte: {sorted(missing)}")
    invalid = [a for a in required if articles[a]["extraction_status"] != "success"
               or not articles[a]["full_text"].strip()]
    if invalid:
        raise ValueError(f"IDs sem extração utilizável: {sorted(invalid)}")
    excluded = round1_ids | pilot_ids
    reserved = eligible_ids - round1_ids
    pool = []
    exclusions = []
    for group in duplicate_groups(articles):
        candidates = group & reserved
        if not candidates:
            continue
        blocked = group & excluded
        if blocked:
            for article_id in sorted(candidates):
                exclusions.append({"article_id": article_id, "reason": "rodada1_ou_piloto",
                                   "related_ids": ";".join(sorted(blocked))})
            continue
        representative = min(candidates)
        pool.append(representative)
        for article_id in sorted(candidates - {representative}):
            exclusions.append({"article_id": article_id, "reason": "duplicata_no_pool",
                               "related_ids": representative})
    pool.sort()
    if len(pool) < 60:
        raise ValueError(f"Pool insuficiente após exclusões: {len(pool)} notícias; necessárias 60")
    shuffled = pool.copy()
    random.Random(seed).shuffle(shuffled)
    selected = shuffled[:60]
    return pool, selected, make_assignments(selected), sorted(exclusions, key=lambda row: row["article_id"])


def make_assignments(selected):
    assignments = []
    for index, article_id in enumerate(selected):
        shared = index < 6
        reviewers = REVIEWERS if shared else (REVIEWERS[(index - 6) % len(REVIEWERS)],)
        for reviewer in reviewers:
            assignments.append({"article_id": article_id, "reviewer": reviewer,
                                "is_shared": str(shared).lower(), "status": STATE})
    return assignments


def replace_candidates(pool, selected, excluded_ids, seed=42, available_ids=None):
    """Continua a permutação histórica após as 60 originais, preservando os lugares."""
    allowed = set(pool) if available_ids is None else set(available_ids)
    selected_ids = set(selected)
    if len(selected) != 60 or len(set(selected)) != 60:
        raise ValueError("A amostra de origem precisa ter 60 IDs únicos")
    if not allowed <= set(pool) or not selected_ids <= allowed:
        raise ValueError("A amostra de origem contém IDs fora do pool deduplicado")
    if not excluded_ids or not excluded_ids <= selected_ids:
        raise ValueError("Os IDs para substituir devem ser uma lista não vazia da amostra de origem")
    historical_order = sorted(pool)
    random.Random(seed).shuffle(historical_order)
    available = [article_id for article_id in historical_order[60:]
                 if article_id in allowed and article_id not in selected_ids | excluded_ids]
    if len(available) < len(excluded_ids):
        raise ValueError("Pool insuficiente para substituir os IDs solicitados")
    replacements = []
    revised = selected.copy()
    for index, article_id in enumerate(selected):
        if article_id not in excluded_ids:
            continue
        replacement = available[len(replacements)]
        revised[index] = replacement
        replacements.append({"removed_article_id": article_id, "article_id": replacement,
                             "position": index, "is_shared": index < 6,
                             "reviewers": list(REVIEWERS) if index < 6 else
                             [REVIEWERS[(index - 6) % len(REVIEWERS)]],
                             "scope_review": "PENDENTE"})
    return revised, replacements


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def prepare(raw, manifest, pilot, eligible, provenance, snapshot, output, seed=42,
            replace_ids=None, base=None):
    if (replace_ids is None) != (base is None):
        raise ValueError("Use --replace-ids e --base juntos")
    if replace_ids is not None and output.exists():
        raise ValueError("A revisão exige --output novo; a pasta de saída já existe")
    csv.field_size_limit(10**9)
    with raw.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    articles = {row["id"]: row for row in rows}
    if len(rows) != len(articles):
        raise ValueError("CSV bruto contém IDs repetidos")
    with manifest.open(encoding="utf-8", newline="") as stream:
        round1 = {row["article_id"] for row in csv.DictReader(stream)}
    eligible_ids, pilot_ids = read_ids(eligible), read_ids(pilot)
    pool, selected, assignments, exclusions = select_candidates(
        articles, eligible_ids, round1, pilot_ids, seed)
    historical_pool = pool
    replacements = []
    if replace_ids is not None:
        base_metadata = json.loads((base / "metadata.json").read_text(encoding="utf-8"))
        if base_metadata.get("seed") != seed:
            raise ValueError("A revisão deve usar a mesma semente da amostra de origem")
        base_pool = read_ids(base / "pool_ids.txt")
        if not base_pool <= set(pool):
            raise ValueError("O pool de origem contém IDs fora do pool histórico deduplicado")
        pool = sorted(base_pool)
        source_ids = base / "candidate_ids.txt"
        selected = [line.strip() for line in source_ids.read_text(encoding="utf-8").splitlines()
                    if line.strip()]
        with (base / "assignments.csv").open(encoding="utf-8", newline="") as stream:
            original_assignments = list(csv.DictReader(stream))
        if original_assignments != make_assignments(selected):
            raise ValueError("As atribuições de origem não correspondem aos lugares planejados")
        with (base / "exclusions.csv").open(encoding="utf-8", newline="") as stream:
            exclusions = list(csv.DictReader(stream))
        excluded_ids = read_ids(replace_ids)
        selected, replacements = replace_candidates(historical_pool, selected, excluded_ids, seed,
                                                     available_ids=base_pool)
        assignments = make_assignments(selected)
        pool = sorted(set(pool) - excluded_ids)
        exclusions.extend({"article_id": row["removed_article_id"],
                           "reason": "substituicao_solicitada", "related_ids": row["article_id"]}
                          for row in replacements)
    snapshot_doc = yaml.safe_load(snapshot.read_text(encoding="utf-8"))
    entities = snapshot_doc["entities"]

    def summary(ids):
        lengths = [len(articles[a]["full_text"]) for a in ids]
        return {"articles": len(ids), "by_source": dict(sorted(Counter(
            articles[a]["source_name"] for a in ids).items())),
            "characters": {"min": min(lengths), "median": statistics.median(lengths),
                           "max": max(lengths)}}

    metadata = {
        "status": STATE, "seed": seed,
        "sampling": "aleatória simples sobre representantes de componentes deduplicados; sem cotas",
        "scope": "elegibilidade histórica rodada1; excluir rodada1, piloto e duplicatas por URL/texto",
        "pending": ["export novo de entidades", "fechar protocolo", "revalidar escopo da amostra"],
        "historical_eligibility": json.loads(provenance.read_text(encoding="utf-8")),
        "inputs_sha256": {str(p): sha256(p) for p in
                          (raw, manifest, pilot, eligible, provenance, snapshot)},
        "historical_eligible": len(eligible_ids), "round1": len(round1),
        "reserved_before_pilot_and_duplicates": len(eligible_ids - round1),
        "pilot": sorted(pilot_ids), "pool": summary(pool), "sample": summary(selected),
        "duplicate_components": [sorted(g) for g in duplicate_groups(articles) if len(g) > 1],
        "exclusions": len(exclusions),
        "assignment": {"unique_articles": 60, "shared_articles": 6,
                       "exclusive_per_reviewer": 9, "rows": len(assignments)},
        "snapshot": {"path": str(snapshot), "generated_at": snapshot_doc.get("generated_at"),
                     "definitive": False, "entities": len(entities),
                     "aliases": sum(len(e.get("aliases", [])) for e in entities),
                     "entity_types": dict(Counter(e["entity_type"] for e in entities))},
    }
    if replacements:
        metadata["sampling"] = ("amostra de origem preservada por posição; continuação da permutação "
                                "histórica após as 60 originais, pulando selecionadas e exclusões")
        metadata["pending"] = ["revisar foco e escopo das substitutas", "confirmar amostra definitiva"]
        metadata["inputs_sha256"].update({str(p): sha256(p) for p in
                                          (replace_ids, base / "candidate_ids.txt",
                                           base / "assignments.csv", base / "pool_ids.txt",
                                           base / "exclusions.csv", base / "metadata.json")})
        metadata["replacement"] = {"base": str(base), "count": len(replacements),
                                   "scope_review": "PENDENTE", "report": "replacement-report.json",
                                   "code_sha256": sha256(Path(__file__))}
    output.mkdir(parents=True, exist_ok=True)
    fields = ["article_id", "source_name", "canonical_link", "text_sha256", "characters",
              "paragraphs", "is_shared", "status"]
    candidates = [{"article_id": a, "source_name": articles[a]["source_name"],
                   "canonical_link": articles[a]["canonical_link"],
                   "text_sha256": text_hash(articles[a]["full_text"]),
                   "characters": len(articles[a]["full_text"]),
                   "paragraphs": len(segment("news_article", articles[a]["full_text"])),
                   "is_shared": str(i < 6).lower(), "status": STATE}
                  for i, a in enumerate(selected)]
    write_csv(output / "candidates.csv", candidates, fields)
    write_csv(output / "assignments.csv", assignments,
              ["article_id", "reviewer", "is_shared", "status"])
    write_csv(output / "exclusions.csv", exclusions, ["article_id", "reason", "related_ids"])
    (output / "pool_ids.txt").write_text("\n".join(pool) + "\n", encoding="utf-8")
    (output / "candidate_ids.txt").write_text("\n".join(selected) + "\n", encoding="utf-8")
    for reviewer in REVIEWERS:
        ids = [r["article_id"] for r in assignments if r["reviewer"] == reviewer]
        (output / f"ids_{reviewer}.txt").write_text("\n".join(ids) + "\n", encoding="utf-8")
    metadata["outputs_sha256"] = {p.name: sha256(p) for p in sorted(output.iterdir())
                                  if p.name.endswith((".csv", ".txt"))
                                  and p.name != eligible.name}
    (output / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False,
                                                    indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if replacements:
        report = {"status": STATE, "seed": seed, "base": str(base),
                  "selection_rule": "cauda da permutação histórica seed; pular selecionadas e exclusões",
                  "scope_review": "PENDENTE: confirmar foco em entidade do snapshot e texto íntegro",
                  "replacements": [{**row, "title": articles[row["article_id"]].get("title", ""),
                                     "source_name": articles[row["article_id"]]["source_name"],
                                     "canonical_link": articles[row["article_id"]]["canonical_link"]}
                                    for row in replacements],
                  "validation": {"unique_articles": len(set(selected)),
                                 "assignments": len(assignments),
                                 "removed_ids_absent": not bool(set(selected) & read_ids(replace_ids)),
                                 "split_generated": False, "labels_generated": False}}
        (output / "replacement-report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=Path("data/raw/articles_202608191040.csv"))
    parser.add_argument("--manifest", type=Path, default=Path("data/annotation/manifest.csv"))
    parser.add_argument("--pilot", type=Path, default=Path("experiments/data/piloto_ids.txt"))
    parser.add_argument("--eligible", type=Path, default=Path("experiments/data/preparacao/historical_eligible_ids.txt"))
    parser.add_argument("--provenance", type=Path, default=Path("experiments/data/preparacao/historical_eligibility.json"))
    parser.add_argument("--snapshot", type=Path, default=Path("data/exports/target_entities.yaml"))
    parser.add_argument("--output", type=Path, default=Path("experiments/data/preparacao"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--replace-ids", type=Path,
                        help="arquivo de IDs da amostra que devem ser substituídos, um por linha")
    parser.add_argument("--base", type=Path,
                        help="pasta da amostra original; exige --replace-ids e --output novo")
    args = parser.parse_args()
    metadata = prepare(**vars(args))
    print(f"{STATE}: {metadata['sample']['articles']} candidatas; pool={metadata['pool']['articles']}")
    if "replacement" in metadata:
        print(f"Substituições: {metadata['replacement']['count']}; revisão de escopo PENDENTE em "
              f"{args.output / 'replacement-report.json'}")


if __name__ == "__main__":
    main()

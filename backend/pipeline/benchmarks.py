"""Validate, build, and check the public finance benchmark catalog."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

import httpx


ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "benchmarks" / "registry.json"
BUILT = ROOT / "frontend" / "public" / "benchmarks.json"
DOC = ROOT / "docs" / "research" / "public-finance-accounting-benchmarks.md"
STATE = ROOT / "benchmarks" / "source-state.json"

PUBLISHER_TYPES = ("academic", "eval_lab", "vendor", "aggregator", "community", "consortium", "other")
KINDS = ("benchmark", "index", "dataset_suite")
DOMAINS = (
    "accounting", "audit", "tax", "financial_analysis", "modeling_spreadsheets",
    "investment_banking", "financial_nlp", "reporting_xbrl", "exams_knowledge", "general_work",
)
TASK_FORMATS = (
    "agentic", "document_qa", "qa", "extraction", "classification", "generation",
    "preference", "composite",
)
GRADERS = (
    "rubric_llm", "rubric", "reference_answer", "programmatic", "human_expert",
    "pairwise_votes", "composite", "unspecified",
)
DATA_ACCESS = ("open", "partial", "on_request", "private", "unknown")
RELEVANCE = ("core", "adjacent", "reference")
RESULTS_STATUSES = ("leaderboard", "snapshot", "archived", "unpublished", "unknown")
RESULT_SOURCE_TYPES = ("first_party", "vendor_report", "paper", "mirror")
PRODUCT_STATUSES = ("published", "claim_only", "none_found")
RESULT_KEYS = {
    "as_of", "metric", "leader", "leader_score", "models_evaluated",
    "source_url", "source_type", "note",
}
BENCHMARK_KEYS = {
    "id", "name", "publisher", "publisher_type", "kind", "domains", "summary",
    "task_format", "size", "stateful", "grader", "data_access", "license",
    "relevance", "relevance_note", "results_status", "results", "links",
    "first_published", "last_verified", "notes",
}
PRODUCT_KEYS = {
    "id", "name", "url", "status", "claim", "claim_source", "benchmark_ids",
    "last_verified",
}
LINK_KEYS = {"home", "leaderboard", "paper", "data", "code"}
ID_PATTERN = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
PERIOD_PATTERN = re.compile(r"^\d{4}(?:-\d{2}(?:-\d{2})?)?$")


def _parse_date(value: object) -> date | None:
    if not isinstance(value, str) or not PERIOD_PATTERN.fullmatch(value):
        return None
    try:
        if len(value) == 4:
            return date(int(value), 1, 1)
        if len(value) == 7:
            return date.fromisoformat(f"{value}-01")
        return date.fromisoformat(value)
    except ValueError:
        return None


def _is_https(value: object) -> bool:
    return isinstance(value, str) and value.startswith("https://")


def validate(registry: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(registry, dict):
        return ["registry must be an object"]
    catalog_updated = _parse_date(registry.get("catalog_updated"))
    if registry.get("schema_version") != 1 or isinstance(registry.get("schema_version"), bool):
        errors.append("schema_version must be 1")
    if catalog_updated is None or not isinstance(registry.get("catalog_updated"), str) or len(registry["catalog_updated"]) != 10:
        errors.append("catalog_updated must be an ISO date (YYYY-MM-DD)")

    benchmarks = registry.get("benchmarks")
    if not isinstance(benchmarks, list):
        errors.append("benchmarks must be a list")
        benchmarks = []
    benchmark_ids: set[str] = set()
    for index, benchmark in enumerate(benchmarks):
        prefix = f"benchmarks[{index}]"
        if not isinstance(benchmark, dict):
            errors.append(f"{prefix} must be an object")
            continue
        missing = BENCHMARK_KEYS - benchmark.keys()
        extra = benchmark.keys() - BENCHMARK_KEYS
        if missing:
            errors.append(f"{prefix} missing keys: {', '.join(sorted(missing))}")
        if extra:
            errors.append(f"{prefix} has unexpected keys: {', '.join(sorted(extra))}")

        identifier = benchmark.get("id")
        if not isinstance(identifier, str) or not ID_PATTERN.fullmatch(identifier):
            errors.append(f"{prefix}.id must be unique kebab-case")
        elif identifier in benchmark_ids:
            errors.append(f"{prefix}.id is duplicated: {identifier}")
        else:
            benchmark_ids.add(identifier)

        for field in ("name", "publisher", "summary", "relevance_note"):
            if not isinstance(benchmark.get(field), str):
                errors.append(f"{prefix}.{field} must be a string")
        for field in ("size", "license", "notes"):
            if benchmark.get(field) is not None and not isinstance(benchmark.get(field), str):
                errors.append(f"{prefix}.{field} must be a string or null")
        enum_fields = {
            "publisher_type": PUBLISHER_TYPES, "kind": KINDS, "task_format": TASK_FORMATS,
            "grader": GRADERS, "data_access": DATA_ACCESS, "relevance": RELEVANCE,
            "results_status": RESULTS_STATUSES,
        }
        for field, allowed in enum_fields.items():
            if benchmark.get(field) not in allowed:
                errors.append(f"{prefix}.{field} has unknown value: {benchmark.get(field)!r}")
        domains = benchmark.get("domains")
        if not isinstance(domains, list) or not domains:
            errors.append(f"{prefix}.domains must be a non-empty list")
        elif any(domain not in DOMAINS for domain in domains):
            errors.append(f"{prefix}.domains contains an unknown value")
        if not isinstance(benchmark.get("stateful"), bool):
            errors.append(f"{prefix}.stateful must be a boolean")

        verified = _parse_date(benchmark.get("last_verified"))
        if verified is None or not isinstance(benchmark.get("last_verified"), str) or len(benchmark["last_verified"]) != 10:
            errors.append(f"{prefix}.last_verified must be a full ISO date")
        elif catalog_updated is not None and verified > catalog_updated:
            errors.append(f"{prefix}.last_verified is after catalog_updated")
        if _parse_date(benchmark.get("first_published")) is None:
            errors.append(f"{prefix}.first_published must be YYYY, YYYY-MM, or YYYY-MM-DD")

        links = benchmark.get("links")
        if not isinstance(links, dict):
            errors.append(f"{prefix}.links must be an object")
            links = {}
        else:
            for key, value in links.items():
                if key not in LINK_KEYS:
                    errors.append(f"{prefix}.links has unknown key: {key}")
                if not _is_https(value):
                    errors.append(f"{prefix}.links.{key} must start with https://")

        status = benchmark.get("results_status")
        results = benchmark.get("results")
        source_url = None
        if status in ("leaderboard", "snapshot", "archived"):
            if not isinstance(results, dict):
                errors.append(f"{prefix}.results must be an object for {status}")
            else:
                missing_result_keys = RESULT_KEYS - results.keys()
                extra_result_keys = results.keys() - RESULT_KEYS
                if missing_result_keys:
                    errors.append(f"{prefix}.results missing keys: {', '.join(sorted(missing_result_keys))}")
                if extra_result_keys:
                    errors.append(f"{prefix}.results has unexpected keys: {', '.join(sorted(extra_result_keys))}")
                if results.get("as_of") is not None and _parse_date(results.get("as_of")) is None:
                    errors.append(f"{prefix}.results.as_of must be YYYY, YYYY-MM, YYYY-MM-DD, or null")
                for field in ("metric", "leader", "leader_score", "note"):
                    if results.get(field) is not None and not isinstance(results.get(field), str):
                        errors.append(f"{prefix}.results.{field} must be a string or null")
                models = results.get("models_evaluated")
                if models is not None and (not isinstance(models, int) or isinstance(models, bool)):
                    errors.append(f"{prefix}.results.models_evaluated must be an integer or null")
                source_url = results.get("source_url")
                if source_url is not None and not _is_https(source_url):
                    errors.append(f"{prefix}.results.source_url must start with https:// or be null")
                if results.get("source_type") not in RESULT_SOURCE_TYPES:
                    errors.append(f"{prefix}.results.source_type has unknown value: {results.get('source_type')!r}")
            if status == "leaderboard" and not links.get("leaderboard") and not (
                isinstance(results, dict) and _is_https(source_url)
            ):
                errors.append(f"{prefix} leaderboard requires links.leaderboard or results.source_url")
        elif status in ("unpublished", "unknown") and results is not None:
            errors.append(f"{prefix}.results must be null for {status}")

    products = registry.get("products")
    if not isinstance(products, list):
        errors.append("products must be a list")
        products = []
    product_ids: set[str] = set()
    for index, product in enumerate(products):
        prefix = f"products[{index}]"
        if not isinstance(product, dict):
            errors.append(f"{prefix} must be an object")
            continue
        missing = PRODUCT_KEYS - product.keys()
        extra = product.keys() - PRODUCT_KEYS
        if missing:
            errors.append(f"{prefix} missing keys: {', '.join(sorted(missing))}")
        if extra:
            errors.append(f"{prefix} has unexpected keys: {', '.join(sorted(extra))}")
        identifier = product.get("id")
        if not isinstance(identifier, str) or not identifier:
            errors.append(f"{prefix}.id must be a non-empty string")
        elif identifier in product_ids:
            errors.append(f"{prefix}.id is duplicated: {identifier}")
        else:
            product_ids.add(identifier)
        if not isinstance(product.get("name"), str):
            errors.append(f"{prefix}.name must be a string")
        if not _is_https(product.get("url")):
            errors.append(f"{prefix}.url must start with https://")
        status = product.get("status")
        if status not in PRODUCT_STATUSES:
            errors.append(f"{prefix}.status has unknown value: {status!r}")
        claim = product.get("claim")
        claim_source = product.get("claim_source")
        if claim is not None and not isinstance(claim, str):
            errors.append(f"{prefix}.claim must be a string or null")
        if claim_source is not None and not isinstance(claim_source, str):
            errors.append(f"{prefix}.claim_source must be a string or null")
        benchmark_refs = product.get("benchmark_ids")
        if not isinstance(benchmark_refs, list):
            errors.append(f"{prefix}.benchmark_ids must be a list")
            benchmark_refs = []
        if any(not isinstance(ref, str) for ref in benchmark_refs):
            errors.append(f"{prefix}.benchmark_ids must contain strings")
        if status == "claim_only" and (
            not isinstance(claim, str) or not claim or not _is_https(claim_source)
        ):
            errors.append(f"{prefix} claim_only requires claim and an https claim_source")
        if status == "published":
            if not benchmark_refs:
                errors.append(f"{prefix} published requires non-empty benchmark_ids")
            for ref in benchmark_refs:
                if ref not in benchmark_ids:
                    errors.append(f"{prefix} references missing benchmark: {ref}")
        if status == "none_found" and (claim is not None or claim_source is not None or benchmark_refs):
            errors.append(f"{prefix} none_found requires null claim/source and empty benchmark_ids")

    return errors


def _flags(benchmark: dict, catalog_updated: date) -> list[str]:
    flags: list[str] = []
    verified = _parse_date(benchmark.get("last_verified"))
    if verified is not None and (catalog_updated - verified).days > 45:
        flags.append("review_due")
    results = benchmark.get("results")
    if benchmark.get("results_status") == "leaderboard" and isinstance(results, dict):
        as_of = results.get("as_of")
        if as_of is None:
            flags.append("undated_results")
        else:
            results_date = _parse_date(as_of)
            if results_date is not None and (catalog_updated - results_date).days > 180:
                flags.append("results_stale")
    if benchmark.get("publisher_type") == "vendor":
        flags.append("vendor_published")
    if isinstance(results, dict) and results.get("source_type") == "mirror":
        flags.append("mirror_source")
    return flags


def _linked_benchmark(benchmark: dict) -> str:
    links = benchmark.get("links") or {}
    url = next((links[key] for key in ("leaderboard", "home", "paper", "code", "data") if links.get(key)), None)
    name = _cell(benchmark.get("name", ""))
    return f"[{name}]({url})" if url else name


def _cell(value: object) -> str:
    return str(value).replace("|", r"\|").replace("\n", " ")


def _benchmark_results(benchmark: dict) -> str:
    result = benchmark.get("results")
    label = benchmark.get("results_status", "")
    if not isinstance(result, dict):
        return _cell(label)
    if result.get("leader") is not None:
        label += f", leader {result['leader']}"
        if result.get("leader_score") is not None:
            label += f" score {result['leader_score']}"
    if result.get("as_of") is not None:
        label += f" (as of {result['as_of']})"
    return _cell(label)


def render_doc(registry: dict, built_benchmarks: list[dict]) -> str:
    catalog_date = registry["catalog_updated"]
    benchmarks = registry["benchmarks"]
    products = registry["products"]
    lines = [
        "<!-- Generated by backend/pipeline/benchmarks.py from benchmarks/registry.json. Do not edit by hand. -->",
        "",
        "# Public finance & accounting AI benchmarks",
        "",
        f"Catalog updated: {catalog_date} · {len(benchmarks)} benchmarks · {len(products)} products",
        "",
        "## How to read this",
        "",
        "Results status: **leaderboard** = maintained public results; **snapshot** = one-time results in a paper/report; "
        "**archived** = publisher stopped updating; **unpublished** = benchmark exists but no public model results; "
        "**unknown** = results not verified.",
        "",
    ]
    by_id = {benchmark["id"]: benchmark for benchmark in built_benchmarks}
    for domain in DOMAINS:
        lines.extend([
            f"## {domain}",
            "",
            "| Benchmark | Publisher | Format | Data | License | Grader | Stateful | Results | Relevance |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ])
        selected = [by_id[item["id"]] for item in benchmarks if item["domains"][0] == domain]
        for benchmark in selected:
            lines.append("| " + " | ".join((
                _linked_benchmark(benchmark),
                _cell(benchmark["publisher"]),
                _cell(benchmark["task_format"]),
                _cell(benchmark["data_access"]),
                _cell(benchmark["license"] if benchmark["license"] is not None else "—"),
                _cell(benchmark["grader"]),
                "yes" if benchmark["stateful"] else "no",
                _benchmark_results(benchmark),
                _cell(benchmark["relevance"]),
            )) + " |")
        lines.append("")
    lines.extend(["## Awaiting public results", ""])
    awaiting_benchmarks = [
        benchmark for benchmark in benchmarks
        if benchmark["results_status"] in ("unpublished", "unknown")
    ]
    if awaiting_benchmarks:
        for benchmark in sorted(awaiting_benchmarks, key=lambda item: item["name"].casefold()):
            lines.append(f"- {_linked_benchmark(benchmark)} — {_cell(benchmark['results_status'])}")
    awaiting_products = [product for product in products if product["status"] in ("claim_only", "none_found")]
    if awaiting_products:
        for product in awaiting_products:
            name = f"[{_cell(product['name'])}]({product['url']})"
            entry = f"- {name} — {_cell(product['status'])}"
            if product.get("claim"):
                claim = _cell(product["claim"])
                source = product.get("claim_source")
                entry += f"; claim: {claim}"
                if source:
                    entry += f" ([source]({source}))"
            lines.append(entry)
    if not awaiting_benchmarks and not awaiting_products:
        lines.append("- None")
    lines.extend([
        "",
        "## Sources",
        "",
        "Every figure links to its canonical source; results were not re-run by Calibration Arena.",
        "",
    ])
    return "\n".join(lines)


def build_outputs(registry: dict, built_path: Path, doc_path: Path) -> None:
    catalog_date = date.fromisoformat(registry["catalog_updated"])
    by_results_status = {status: 0 for status in RESULTS_STATUSES}
    for benchmark in registry["benchmarks"]:
        by_results_status[benchmark["results_status"]] += 1
    products_by_status = {status: 0 for status in PRODUCT_STATUSES}
    for product in registry["products"]:
        products_by_status[product["status"]] += 1

    entries = []
    for benchmark in registry["benchmarks"]:
        entries.append({**benchmark, "flags": _flags(benchmark, catalog_date)})
    entries.sort(key=lambda item: (RELEVANCE.index(item["relevance"]), item["name"].casefold()))
    built = {
        "schema_version": registry["schema_version"],
        "catalog_updated": registry["catalog_updated"],
        "source": "benchmarks/registry.json",
        "review_after_days": 45,
        "results_stale_after_days": 180,
        "counts": {
            "benchmarks": len(registry["benchmarks"]),
            "by_results_status": by_results_status,
            "products_by_status": products_by_status,
        },
        "benchmarks": entries,
        "products": registry["products"],
    }
    built_path.parent.mkdir(parents=True, exist_ok=True)
    built_path.write_text(json.dumps(built, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(render_doc(registry, entries), encoding="utf-8")


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in ("script", "style"):
            self.hidden_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in ("script", "style") and self.hidden_depth:
            self.hidden_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden_depth:
            self.parts.append(data)


def _visible_text(content: str) -> str:
    parser = _VisibleTextParser()
    parser.feed(content)
    return " ".join(" ".join(parser.parts).split())


def source_urls(registry: dict) -> list[str]:
    urls = set()
    for benchmark in registry["benchmarks"]:
        urls.update(value for value in benchmark.get("links", {}).values() if _is_https(value))
        results = benchmark.get("results")
        if isinstance(results, dict) and _is_https(results.get("source_url")):
            urls.add(results["source_url"])
    for product in registry["products"]:
        for field in ("url", "claim_source"):
            if _is_https(product.get(field)):
                urls.add(product[field])
    return sorted(urls)


def check_sources(
    registry: dict,
    client: httpx.Client,
    previous_state: dict | None = None,
    checked: str | None = None,
) -> dict:
    previous_state = previous_state or {}
    checked = checked or date.today().isoformat()
    urls = source_urls(registry)

    def fetch(url: str) -> tuple[str, dict]:
        try:
            response = client.get(url)
            text_hash = sha256(_visible_text(response.text).encode("utf-8")).hexdigest()
            return url, {
                "status": response.status_code,
                "final_url": str(response.url),
                "text_sha256": text_hash,
                "checked": checked,
            }
        except Exception as exc:
            return url, {
                "status": f"{type(exc).__name__}: {exc}",
                "final_url": url,
                "text_sha256": None,
                "checked": checked,
            }

    state = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(fetch, url) for url in urls]
        for future in as_completed(futures):
            url, record = future.result()
            state[url] = record
    state = dict(sorted(state.items()))
    unreachable = [
        (url, record) for url, record in state.items()
        if not isinstance(record["status"], int) or record["status"] >= 400
    ]
    redirected = [
        (url, record) for url, record in state.items()
        if record["final_url"] != url
    ]
    new = [url for url in urls if url not in previous_state]
    changed = [
        url for url in urls
        if url in previous_state
        and isinstance(state[url]["status"], int)
        and state[url]["status"] < 400
        and state[url]["text_sha256"] is not None
        and state[url]["text_sha256"] != previous_state[url].get("text_sha256")
    ]
    unchanged_count = sum(
        1 for url in urls
        if url in previous_state
        and isinstance(state[url]["status"], int)
        and state[url]["status"] < 400
        and state[url]["text_sha256"] is not None
        and state[url]["text_sha256"] == previous_state[url].get("text_sha256")
    )
    return {
        "state": state,
        "unreachable": unreachable,
        "redirected": redirected,
        "changed": changed,
        "new": new,
        "unchanged_count": unchanged_count,
    }


def _print_source_report(report: dict) -> None:
    for heading, entries in (
        ("Unreachable", report["unreachable"]),
        ("Redirected", report["redirected"]),
        ("Changed", [(url, report["state"][url]) for url in report["changed"]]),
        ("New", [(url, report["state"][url]) for url in report["new"]]),
    ):
        print(f"{heading}:")
        for url, record in entries:
            print(f"- {url} — status {record['status']}; final URL {record['final_url']}")
        if not entries:
            print("- None")
    print(f"Unchanged: {report['unchanged_count']}")


def _load_registry() -> dict:
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate")
    subparsers.add_parser("build")
    check_parser = subparsers.add_parser("check-sources")
    check_parser.add_argument("--write", action="store_true")
    subparsers.add_parser("report")
    args = parser.parse_args(argv)

    registry = _load_registry()
    errors = validate(registry)
    if args.command == "validate" or errors:
        for error in errors:
            print(error)
        if args.command == "validate":
            if not errors:
                print("Registry valid")
            return 1 if errors else 0
        if errors:
            return 1

    if args.command == "build":
        build_outputs(registry, BUILT, DOC)
        print(f"Built {BUILT.relative_to(ROOT)} and {DOC.relative_to(ROOT)}")
        return 0
    if args.command == "check-sources":
        previous_state = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
        headers = {
            "User-Agent": "CalibrationArenaCatalogBot/1.0 (+https://github.com/dmurguia/calibration-arena)"
        }
        with httpx.Client(follow_redirects=True, timeout=20, headers=headers) as client:
            report = check_sources(registry, client, previous_state)
        _print_source_report(report)
        if args.write:
            STATE.write_text(json.dumps(report["state"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return 0
    if args.command == "report":
        catalog_date = date.fromisoformat(registry["catalog_updated"])
        entries = [
            {**benchmark, "flags": _flags(benchmark, catalog_date)}
            for benchmark in registry["benchmarks"]
        ]
        print("# Benchmark review queue\n")
        print("## Review and results flags\n")
        queue_flags = {"review_due", "results_stale", "undated_results"}
        flagged = [item for item in entries if queue_flags.intersection(item["flags"])]
        for item in sorted(flagged, key=lambda value: value["name"].casefold()):
            print(
                f"- {_linked_benchmark(item)} — "
                f"{', '.join(flag for flag in item['flags'] if flag in queue_flags)}"
            )
        if not flagged:
            print("- None")
        print("\n## Awaiting public results\n")
        awaiting = [
            item for item in entries if item["results_status"] in ("unpublished", "unknown")
        ]
        for item in sorted(awaiting, key=lambda value: value["name"].casefold()):
            print(f"- {_linked_benchmark(item)} — {item['results_status']}")
        awaiting_products = [
            item for item in registry["products"] if item["status"] in ("claim_only", "none_found")
        ]
        for item in awaiting_products:
            print(f"- [{_cell(item['name'])}]({item['url']}) — {item['status']}")
        if not awaiting and not awaiting_products:
            print("- None")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

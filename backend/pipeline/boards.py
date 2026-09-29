"""Fetch publisher-reported per-model results into dated board snapshots.

Each adapter reads the structured data a publisher already ships with its
leaderboard page and records it verbatim. Nothing is rerun, rescaled across
benchmarks, or aggregated.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime
from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from typing import Callable

import httpx


ROOT = Path(__file__).resolve().parents[2]
BOARDS_DIR = ROOT / "benchmarks" / "boards"
MODELS = ROOT / "benchmarks" / "models.json"
REGISTRY = ROOT / "benchmarks" / "registry.json"
WEIGHTS = ("open", "closed", "unknown")

PREFIXES = ("anthropic ", "claude ", "openai ", "z.ai ", "google ", "meta ", "xai ")
KEY_ALIASES = {
    "geminipro3.1": "gemini3.1pro",
    "gemini3.1propreview": "gemini3.1pro",
    "nemotron3ultra550ba55b": "nemotron3ultra",
    "nemotronlightning3p530ba3b": "nemotron3.5lightning",
}
ORG_ALIASES = {"Zhipu": "Zhipu AI", "Kimi": "Moonshot AI", "SpaceXAI": "xAI"}
EFFORTS = {"xhigh": "XHigh"}
CLOSED_FAMILIES = re.compile(r"^(opus|sonnet|haiku|fable|3\.\d(sonnet|haiku)|gpt(?!oss)|o\d|gemini|grok|musespark)")
OPEN_FAMILIES = re.compile(
    r"^(gptoss|llama|gemma|deepseek(r1|v3)|qwen3235b|kimik2(instruct)?$|glm4\.[567]|minimaxm2|mistralsmall|magistralsmall|jamba|nemotron)"
)


def model_key(label: str) -> str:
    s = label.lower()
    for prefix in PREFIXES:
        if s.startswith(prefix):
            s = s[len(prefix):]
    s = re.sub(r"\((preview|thinking|nonthinking)\)", "", s)
    s = re.sub(r"\bpreview\b", "", s)
    s = re.sub(r"[^a-z0-9.]", "", s)
    return KEY_ALIASES.get(s, s)


def model_id(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", model_key(label)).strip("-")


class _Tokens(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tokens: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style", "svg"):
            self.hidden += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "svg") and self.hidden:
            self.hidden -= 1

    def handle_data(self, data: str) -> None:
        if not self.hidden and data.strip():
            self.tokens.append(data.strip())


def text_tokens(page: str) -> list[str]:
    parser = _Tokens()
    parser.feed(page)
    return parser.tokens


def _next_data(page: str) -> dict:
    match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', page, re.S)
    if not match:
        raise ValueError("no __NEXT_DATA__ payload")
    return json.loads(match.group(1))


def _astro(value: object) -> object:
    if isinstance(value, list) and len(value) == 2 and isinstance(value[0], int):
        tag, inner = value
        if tag == 0:
            return _astro(inner)
        if tag == 1:
            return [_astro(item) for item in inner]
        return inner
    if isinstance(value, dict):
        return {key: _astro(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_astro(item) for item in value]
    return value


def _pct(token: str) -> float | None:
    match = re.fullmatch(r"(\d+(?:\.\d+)?)%?", token)
    return float(match.group(1)) if match else None


VALS_ORGS = {
    "ai21labs": "AI21 Labs", "alibaba": "Alibaba", "ant": "Ant Group", "anthropic": "Anthropic",
    "arcee-ai": "Arcee AI", "cohere": "Cohere", "deepseek": "DeepSeek", "google": "Google",
    "grok": "xAI", "inception": "Inception", "kimi": "Moonshot AI", "meta": "Meta",
    "minimax": "MiniMax", "mistralai": "Mistral", "nvidia": "NVIDIA", "openai": "OpenAI",
    "poolside": "Poolside", "tencent": "Tencent", "thinkingmachines": "Thinking Machines",
    "xiaomi": "Xiaomi", "zai": "Zhipu AI",
}
VALS_WORDS = {
    "gpt": "GPT", "glm": "GLM", "mimo": "MiMo", "minimax": "MiniMax", "oss": "OSS",
    "deepseek": "DeepSeek", "it": "IT", "hy4": "HY4", "af": "AF", "rc3": "RC3",
}


def vals_label(vals_id: str) -> tuple[str, str | None, str | None]:
    """Return (label, config, org) for a Vals model id."""
    parts = vals_id.split("/")
    org_key = parts[-2] if len(parts) > 1 else ""
    if "nvidia" in parts:
        org_key = "nvidia"
    elif "meta-llama" in parts:
        org_key = "meta"
    elif "moonshotai" in parts:
        org_key = "kimi"
    elif org_key in ("fireworks", "together"):
        name = parts[-1].lower()
        org_key = next(
            (o for o, pat in (("deepseek", "deepseek"), ("openai", "gpt-oss"), ("meta", "llama"),
                              ("alibaba", "qwen"), ("nvidia", "nemotron")) if pat in name),
            org_key,
        )
    name = parts[-1].replace("_", "-")
    config = None
    for suffix, cfg in (("-non-reasoning", "Non-reasoning"), ("-reasoning", "Reasoning"), ("-thinking", "Thinking")):
        if name.endswith(suffix):
            name, config = name[: -len(suffix)], cfg
            break
    name = re.sub(r"-(20\d{6}|20\d\d-\d\d-\d\d)$", "", name)
    name = re.sub(r"-42e84561$", "", name)
    words: list[str] = []
    for token in name.split("-"):
        if words and re.fullmatch(r"\d{1,2}", token) and re.fullmatch(r"(\d{1,2}\.)*\d{1,2}", words[-1]):
            words[-1] += "." + token
            continue
        words.append(token)
    out = []
    for word in words:
        low = re.sub(r"^(v\d+)p(\d+)$", r"\1.\2", word.lower())
        if low in VALS_WORDS:
            out.append(VALS_WORDS[low])
        elif re.fullmatch(r"o\d|\d+o", low):
            out.append(low)
        elif re.fullmatch(r"[a-z]{0,2}\d[\w.]*", low):
            out.append(low.upper() if re.fullmatch(r"[a-z]{1,2}\d[\d.]*|\d+[a-z]\d*[a-z]?|[a-z]\d+[a-z]", low) else low)
        else:
            out.append(word[:1].upper() + word[1:])
    label = " ".join(out)
    if org_key == "anthropic" and not label.startswith("Claude"):
        label = "Claude " + label
    return label, config, VALS_ORGS.get(org_key)


def adapt_vals(page: str) -> dict:
    view = None
    for raw in re.findall(r'props="([^"]*)"', page):
        decoded = unescape(raw)
        if '"benchmarkView"' in decoded and '"tasks"' in decoded:
            view = _astro(json.loads(decoded))["benchmarkView"]
            break
    if view is None:
        raise ValueError("no Vals benchmarkView payload")
    meta = view["metadata"]
    entries = []
    for vals_id, row in view["tasks"]["overall"].items():
        label, config, org = vals_label(vals_id)
        entries.append({
            "label": label, "config": config, "org": org, "source_model_id": vals_id,
            "scores": {"accuracy": row["accuracy"]}, "cost": row.get("cost_per_test"),
        })
    return {
        "as_of": meta.get("updated"),
        "metrics": [{"key": "accuracy", "label": "Accuracy", "unit": "%"}],
        "cost_label": "USD per test (publisher-reported)" if meta.get("use_cost_per_test") else None,
        "archived": bool(meta.get("archived")),
        "entries": entries,
    }


APEX_METRICS = {"mean-score": "Mean score", "pass-1": "Pass@1"}


def _apex_config(effort: str | None, descriptors: list[str] | None) -> str | None:
    parts = [EFFORTS.get(effort, effort.capitalize())] if effort else []
    parts += descriptors or []
    return " · ".join(parts) or None


def adapt_apex_accounting(page: str, cost_rows: dict[str, float] | None = None) -> dict:
    rows = _next_data(page)["props"]["pageProps"]["benchmark"]["globalLeaderboard"]
    entries, seen = [], set()
    for row in rows:
        model = row["model"]
        scores, ci = {}, {}
        for item in row["passScores"]:
            if item["pass"] in APEX_METRICS:
                scores[item["pass"]] = item["score"]
                if item.get("error") is not None:
                    ci[item["pass"]] = [round(item["score"] - item["error"], 2), round(item["score"] + item["error"], 2)]
        config = _apex_config(model.get("effort"), model.get("descriptors"))
        dedupe = (model["modelName"], tuple(sorted(scores.items())), tuple(model.get("descriptors") or ()))
        if dedupe in seen:
            continue
        seen.add(dedupe)
        entries.append({
            "label": model["modelName"], "config": config, "org": model["provider"]["name"],
            "scores": scores, "ci": ci, "cost": None,
        })
    return {"as_of": None, "metrics": [{"key": k, "label": v, "unit": "%"} for k, v in APEX_METRICS.items()], "entries": entries}


def apex_cost_table(page: str) -> list[tuple[str, float, float]]:
    """Rows of (label, mean score, $/run) from the APEX cost-vs-score table."""
    out = []
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", page, re.S):
        cells = [unescape(re.sub(r"<[^>]+>|\s+", " ", c)).strip() for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", row, re.S)]
        if len(cells) == 3 and cells[2].startswith("$"):
            name = re.sub(r"\s*Top quadrant\s*", "", cells[0]).strip()
            score = _pct(cells[1].replace(" ", ""))
            if score is not None:
                out.append((name, score, float(cells[2].replace("$", "").replace(" ", ""))))
    return out


def attach_apex_costs(board: dict, costs: list[tuple[str, float, float]]) -> None:
    """Attach $/run only where the cost table reports the same mean score as the leaderboard row."""
    for name, score, cost in costs:
        key = model_key(name.split("-397B")[0])
        matches = [e for e in board["entries"] if model_key(e["label"]) == key and e["scores"].get("mean-score") == score]
        if len(matches) >= 1:
            matches[0]["cost"] = cost
    if any(e["cost"] is not None for e in board["entries"]):
        board["cost_label"] = "USD per run (publisher cost study, subset of models)"


def adapt_apex_agents(page: str) -> dict:
    rows = _next_data(page)["props"]["pageProps"]["leaderboardDict"]
    entries = []
    for row in rows.values():
        scores = {k: next(iter(v.values())) for k, v in row["score"].items() if k in APEX_METRICS}
        entries.append({
            "label": row["model_name"], "config": _apex_config(row.get("effort"), row.get("descriptors")),
            "org": None, "scores": scores, "cost": None,
        })
    return {"as_of": None, "metrics": [{"key": k, "label": v, "unit": "%"} for k, v in APEX_METRICS.items()], "entries": entries}


def adapt_dualentry(page: str) -> dict:
    tokens = text_tokens(page)
    start = next(n for n in range(1, len(tokens)) if tokens[n] == "License Type" and tokens[n - 1] == "Model Provider") + 1
    entries, i = [], start
    while i + 3 < len(tokens) and tokens[i + 1].endswith("%"):
        label, score, org = tokens[i], _pct(tokens[i + 1]), tokens[i + 3]
        i += 4
        weights = None
        if i < len(tokens) and tokens[i] in ("Open", "Closed"):
            weights = tokens[i].lower()
            i += 1
        entries.append({"label": label, "config": None, "org": org, "scores": {"accuracy": score}, "cost": None, "weights": weights})
    return {"as_of": None, "metrics": [{"key": "accuracy", "label": "Overall accuracy", "unit": "%"}], "entries": entries}


def adapt_entendre(page: str) -> dict:
    tokens = text_tokens(page)
    i = next(n for n in range(1, len(tokens)) if tokens[n] == "Mean score" and tokens[n - 1] == "Model") + 2
    entries = []
    while i + 2 < len(tokens):
        label = tokens[i]
        is_open = tokens[i + 1] == "OS"
        j = i + (2 if is_open else 1)
        score = _pct(tokens[j + 1]) if tokens[j + 1].endswith("%") else None
        if score is None:
            break
        entries.append({"label": label, "config": None, "org": None, "scores": {"mean": score}, "cost": None,
                        "weights": "open" if is_open else None})
        i = j + 2
    return {"as_of": None, "metrics": [{"key": "mean", "label": "Mean score", "unit": "%"}], "entries": entries}


def adapt_bigfinancebench(page: str) -> dict:
    s = page.replace('\\"', '"')
    start = s.index('"entries":[{"model_id"') + len('"entries":')
    depth = 0
    for end in range(start, len(s)):
        if s[end] == "[":
            depth += 1
        elif s[end] == "]":
            depth -= 1
            if depth == 0:
                break
    rows = json.loads(s[start:end + 1])
    entries = []
    for row in rows:
        entries.append({
            "label": row["name"], "config": None, "org": row.get("provider"), "source_model_id": row["model_id"],
            "scores": {"answer": round(row["answer_accuracy"] * 100, 2), "rubric": round(row["rubric_score"] * 100, 2)},
            "ci": {"answer": [round(row["answer_ci_lo"] * 100, 2), round(row["answer_ci_hi"] * 100, 2)],
                   "rubric": [round(row["rubric_ci_lo"] * 100, 2), round(row["rubric_ci_hi"] * 100, 2)]},
            "cost": row.get("cost_per_question_usd"),
            "weights": "open" if row.get("open_weight") is True else "closed" if row.get("open_weight") is False else None,
        })
    updated = re.search(r">Updated</[^>]+>\s*<[^>]+>([A-Z][a-z]{2} \d{1,2}, \d{4})<", page)
    as_of = None
    if updated:
        as_of = datetime.strptime(updated.group(1), "%b %d, %Y").date().isoformat()
    return {
        "as_of": as_of,
        "metrics": [{"key": "answer", "label": "Final answer accuracy", "unit": "%"},
                    {"key": "rubric", "label": "Rubric score", "unit": "%"}],
        "cost_label": "USD per question (publisher-reported)",
        "entries": entries,
    }


SOURCES: dict[str, dict] = {
    "apex-accounting": {"url": "https://www.mercor.com/apex/apex-accounting-leaderboard/?pass=mean-score", "adapter": "apex_accounting"},
    "dualentry-accounting-ai-benchmark": {"url": "https://www.dualentry.com/accounting-ai-benchmark", "adapter": "dualentry"},
    "vals-finance-agent-v2": {"url": "https://www.vals.ai/benchmarks/fabv2", "adapter": "vals"},
    "vals-corpfin-v2": {"url": "https://www.vals.ai/benchmarks/corp_fin_v2", "adapter": "vals"},
    "vals-taxeval-v2": {"url": "https://www.vals.ai/benchmarks/tax_eval_v2", "adapter": "vals"},
    "vals-mortgagetax": {"url": "https://www.vals.ai/benchmarks/mortgage_tax", "adapter": "vals"},
    "taxbench-entendre": {"url": "https://entendre.ai/research/taxbench/", "adapter": "entendre"},
    "apex-agents-ib": {"url": "https://www.mercor.com/apex/apex-agents-leaderboard/investment-banking-analyst-agent/", "adapter": "apex_agents"},
    "bigfinancebench": {"url": "https://bigfinancebench.com/", "adapter": "bigfinancebench"},
}
ADAPTERS: dict[str, Callable[[str], dict]] = {
    "vals": adapt_vals, "apex_accounting": adapt_apex_accounting, "apex_agents": adapt_apex_agents,
    "dualentry": adapt_dualentry, "entendre": adapt_entendre, "bigfinancebench": adapt_bigfinancebench,
}


def build_board(benchmark_id: str, page: str, retrieved: str) -> tuple[dict, list[dict]]:
    source = SOURCES[benchmark_id]
    parsed = ADAPTERS[source["adapter"]](page)
    if source["adapter"] == "apex_accounting":
        attach_apex_costs(parsed, apex_cost_table(page))
    metrics = parsed["metrics"]
    entries = []
    for entry in parsed["entries"]:
        row = {"model": model_id(entry["label"]), "label": entry["label"], "config": entry.get("config"),
               "scores": entry["scores"]}
        if entry.get("ci"):
            row["ci"] = entry["ci"]
        row["cost"] = entry.get("cost") if parsed.get("cost_label") else None
        entries.append(row)
    primary = metrics[0]["key"]
    entries.sort(key=lambda e: (-(e["scores"].get(primary) if e["scores"].get(primary) is not None else -1), e["label"], e["config"] or ""))
    board = {
        "benchmark_id": benchmark_id,
        "source_url": source["url"],
        "adapter": source["adapter"],
        "as_of": parsed.get("as_of"),
        "retrieved": retrieved,
        "metrics": metrics,
        "cost_label": parsed.get("cost_label") if any(e["cost"] is not None for e in entries) else None,
        "entries": entries,
    }
    return board, parsed["entries"]


def display_name(label: str, org: str | None) -> str:
    name = re.sub(r"^(Z\.ai|OpenAI|Meta)\s+", "", label)
    if org == "Anthropic" and not name.startswith("Claude"):
        name = "Claude " + name
    return name


def sync_registry(registry: dict, board: dict) -> None:
    """Refresh the registry's headline result from the board's primary metric."""
    benchmark = next(b for b in registry["benchmarks"] if b["id"] == board["benchmark_id"])
    results = benchmark["results"]
    metric = board["metrics"][0]
    top = board["entries"][0]
    score = top["scores"][metric["key"]]
    results["leader"] = top["label"] + (f" ({top['config']})" if top["config"] else "")
    results["leader_score"] = f"{round(score, 2):g}{'%' if metric['unit'] == '%' else ''}"
    results["metric"] = metric["label"]
    results["models_evaluated"] = len({e["model"] for e in board["entries"]})
    results["as_of"] = board["as_of"] or board["retrieved"]


def merge_models(models: dict[str, dict], benchmark_id: str, raw_entries: list[dict]) -> None:
    for entry in raw_entries:
        mid = model_id(entry["label"])
        record = models.setdefault(mid, {"id": mid, "name": display_name(entry["label"], entry.get("org")), "org": None, "weights_reported": {}})
        if not record["org"] and entry.get("org"):
            record["org"] = ORG_ALIASES.get(entry["org"], entry["org"])
        if entry.get("weights") in ("open", "closed"):
            record["weights_reported"][benchmark_id] = entry["weights"]


def resolve_weights(record: dict) -> tuple[str, str]:
    reported = set(record["weights_reported"].values())
    if len(reported) == 1:
        return reported.pop(), "publisher"
    if len(reported) > 1:
        return "unknown", "conflict"
    key = model_key(record["name"])
    if OPEN_FAMILIES.match(key):
        return "open", "family"
    if CLOSED_FAMILIES.match(key):
        return "closed", "family"
    return "unknown", "none"


def write_models(models: dict[str, dict], path: Path) -> None:
    out = []
    for mid in sorted(models):
        record = dict(models[mid])
        record["weights"], record["weights_basis"] = resolve_weights(record)
        record["weights_reported"] = dict(sorted(record["weights_reported"].items()))
        out.append(record)
    path.write_text(json.dumps({"models": out}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def fetch(ids: list[str], client: httpx.Client, retrieved: str) -> None:
    models: dict[str, dict] = {}
    if MODELS.exists():
        for record in json.loads(MODELS.read_text(encoding="utf-8"))["models"]:
            models[record["id"]] = {k: record[k] for k in ("id", "name", "org", "weights_reported")}
    BOARDS_DIR.mkdir(parents=True, exist_ok=True)
    for benchmark_id in ids:
        response = client.get(SOURCES[benchmark_id]["url"])
        response.raise_for_status()
        board, raw = build_board(benchmark_id, response.text, retrieved)
        if not board["entries"]:
            raise ValueError(f"{benchmark_id}: adapter returned no entries")
        path = BOARDS_DIR / f"{benchmark_id}.json"
        path.write_text(json.dumps(board, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        merge_models(models, benchmark_id, raw)
        print(f"{benchmark_id}: {len(board['entries'])} entries")
    write_models(models, MODELS)
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    for benchmark_id in ids:
        sync_registry(registry, json.loads((BOARDS_DIR / f"{benchmark_id}.json").read_text(encoding="utf-8")))
    REGISTRY.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ids", nargs="*", help="benchmark ids to refresh (default: all)")
    args = parser.parse_args(argv)
    ids = args.ids or list(SOURCES)
    unknown = [i for i in ids if i not in SOURCES]
    if unknown:
        print(f"no adapter for: {', '.join(unknown)}")
        return 1
    headers = {"User-Agent": "Mozilla/5.0 (compatible; CalibrationArenaCatalogBot/1.0; +https://github.com/dmurguia/calibration-arena)"}
    with httpx.Client(follow_redirects=True, timeout=30, headers=headers) as client:
        fetch(ids, client, date.today().isoformat())
    return 0


if __name__ == "__main__":
    sys.exit(main())

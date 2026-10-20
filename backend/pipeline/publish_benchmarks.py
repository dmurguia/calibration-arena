"""Atomically publish an already validated directory to the benchmark-data branch."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import httpx


def publish(directory: Path, repository: str, token: str) -> str:
    branch = "benchmark-data"
    with httpx.Client(base_url=f"https://api.github.com/repos/{repository}/", timeout=60,
                      headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}) as client:
        def post(path, payload):
            response = client.post(path, json=payload)
            response.raise_for_status()
            return response.json()

        response = client.get(f"git/ref/heads/{branch}")
        if response.status_code == 404:
            parent = None
        else:
            response.raise_for_status()
            parent = response.json()["object"]["sha"]
        paths = sorted(p for p in directory.rglob("*") if p.is_file())
        allowed = {"benchmarks.json", "catalog.md", "benchmarks/models.json", "benchmarks/registry.json"}
        tree = []
        # Both Vercel projects use subdirectory roots. Data commits must not
        # trigger frontend/marketing builds on this deliberately code-free branch.
        for config in ("vercel.json", "frontend/vercel.json", "marketing/vercel.json"):
            tree.append({"path": config, "mode": "100644", "type": "blob",
                         "content": '{"git":{"deploymentEnabled":false}}\n'})
        for path in paths:
            relative = path.relative_to(directory).as_posix()
            if relative not in allowed and not (relative.startswith("benchmarks/boards/") and path.suffix == ".json"):
                raise ValueError(f"Unexpected publication file: {relative}")
            tree.append({"path": relative, "mode": "100644", "type": "blob", "content": path.read_text()})
        tree_sha = post("git/trees", {"tree": tree})["sha"]
        commit = post("git/commits", {"message": "Refresh public benchmark snapshots", "tree": tree_sha,
                                      "parents": [parent] if parent else []})["sha"]
        if parent:
            response = client.patch(f"git/refs/heads/{branch}", json={"sha": commit, "force": False})
            response.raise_for_status()
        else:
            post("git/refs", {"ref": f"refs/heads/{branch}", "sha": commit})
        return commit


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--repository", required=True)
    args = parser.parse_args()
    print(publish(args.directory, args.repository, os.environ["GH_TOKEN"]))

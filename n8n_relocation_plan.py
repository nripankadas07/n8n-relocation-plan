"""Plan and safely apply explicit reference relocation in n8n JSON exports."""

import argparse
import hashlib
import html
import json
import sys
from copy import deepcopy
from pathlib import Path


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode()
    ).hexdigest()


def workflow_check(w):
    if (
        not isinstance(w, dict)
        or not isinstance(w.get("nodes"), list)
        or len(w["nodes"]) > 2000
    ):
        raise ValueError("expected one exported workflow with at most 2000 nodes")
    seen = set()
    for node in w["nodes"]:
        if (
            not isinstance(node, dict)
            or not isinstance(node.get("id"), str)
            or not node["id"]
            or node["id"] in seen
        ):
            raise ValueError("node IDs must be unique nonempty strings")
        seen.add(node["id"])
        if not isinstance(node.get("parameters", {}), dict):
            raise TypeError("node parameters must be an object")
        if not isinstance(node.get("credentials", {}), dict):
            raise TypeError("credentials must be a reference mapping")
        for typ, ref in node.get("credentials", {}).items():
            if (
                not isinstance(typ, str)
                or not isinstance(ref, dict)
                or set(ref) - {"id", "name"}
                or not isinstance(ref.get("id"), str)
                or not isinstance(ref.get("name"), str)
            ):
                raise ValueError(
                    "only credential reference id/name metadata is accepted; not credential data"
                )


def plan(workflow, catalog):
    workflow_check(workflow)
    if not isinstance(catalog, dict) or set(catalog) - {
        "credentials",
        "workflows",
        "explicit_credentials",
    }:
        raise ValueError(
            "catalog accepts credential metadata, workflow ID mapping and explicit credential mapping"
        )
    creds = catalog.get("credentials", [])
    mapping = catalog.get("workflows", {})
    explicit = catalog.get("explicit_credentials", {})
    if (
        not isinstance(creds, list)
        or len(creds) > 5000
        or not isinstance(mapping, dict)
        or not isinstance(explicit, dict)
    ):
        raise ValueError("invalid catalog")
    for c in creds:
        if (
            not isinstance(c, dict)
            or set(c) != {"id", "name", "type"}
            or not all(isinstance(v, str) and v for v in c.values())
        ):
            raise ValueError(
                "catalog credential records require only id, name and type; never secrets"
            )
    if len({c["id"] for c in creds}) != len(creds):
        raise ValueError("duplicate catalog credential IDs")
    if not all(
        isinstance(k, str) and k and isinstance(v, str) and v and not v.startswith("=")
        for k, v in mapping.items()
    ):
        raise ValueError("workflow mappings must use literal nonempty string IDs")
    if not all(isinstance(k, str) and isinstance(v, str) for k, v in explicit.items()):
        raise ValueError("explicit mappings must be strings")
    ops = []
    unresolved = []
    for i, node in enumerate(workflow["nodes"]):
        for typ, ref in sorted(node.get("credentials", {}).items()):
            key = typ + ":" + ref["id"]
            if key in explicit:
                choices = [
                    c for c in creds if c["id"] == explicit[key] and c["type"] == typ
                ]
            else:
                choices = [
                    c for c in creds if c["name"] == ref["name"] and c["type"] == typ
                ]
            if len(choices) != 1:
                unresolved.append(
                    {
                        "node_id": node["id"],
                        "kind": "credential",
                        "type": typ,
                        "source_id": ref["id"],
                        "reason": "missing or ambiguous compatible target",
                        "candidate_ids": [c["id"] for c in choices],
                    }
                )
            else:
                c = choices[0]
                ops.append(
                    {
                        "node_index": i,
                        "node_id": node["id"],
                        "kind": "credential",
                        "type": typ,
                        "before": ref,
                        "after": {"id": c["id"], "name": c["name"]},
                    }
                )
        if node.get("type") == "n8n-nodes-base.executeWorkflow":
            raw = node.get("parameters", {}).get("workflowId")
            value = raw.get("value") if isinstance(raw, dict) else raw
            if (
                not isinstance(value, str)
                or value.startswith("=")
                or value not in mapping
            ):
                unresolved.append(
                    {
                        "node_id": node["id"],
                        "kind": "workflow",
                        "reason": "dynamic, absent or unmapped workflow ID",
                    }
                )
            else:
                after = (
                    {**raw, "value": mapping[value]}
                    if isinstance(raw, dict)
                    else mapping[value]
                )
                ops.append(
                    {
                        "node_index": i,
                        "node_id": node["id"],
                        "kind": "workflow",
                        "before": raw,
                        "after": after,
                    }
                )
    return {
        "schema": "n8n-relocation/v1",
        "source_sha256": digest(workflow),
        "catalog_sha256": digest(catalog),
        "operations": ops,
        "unresolved": unresolved,
        "ready": not unresolved,
        "limits": "Reference mapping only; no credential access, activation or server import is performed.",
    }


def apply_plan(workflow, catalog, reviewed):
    expected = plan(workflow, catalog)
    if expected != reviewed:
        raise ValueError(
            "plan differs from the current workflow/catalog; regenerate and review it"
        )
    if not reviewed["ready"]:
        raise ValueError("unresolved references prevent application")
    result = deepcopy(workflow)
    for op in reviewed["operations"]:
        node = result["nodes"][op["node_index"]]
        if op["kind"] == "credential":
            node["credentials"][op["type"]] = deepcopy(op["after"])
        else:
            node["parameters"]["workflowId"] = deepcopy(op["after"])
    # Exported activation state is deliberately disabled in the relocated output.
    result["active"] = False
    return result


def analyze(data):
    if not isinstance(data, dict) or set(data) != {"workflow", "catalog"}:
        raise ValueError("expected workflow and catalog")
    return plan(data["workflow"], data["catalog"])


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("input")
    p.add_argument("--html")
    p.add_argument("--apply-plan")
    p.add_argument("--output")
    args = p.parse_args(argv)
    try:
        data = load(args.input)
        result = analyze(data)
        if args.apply_plan:
            if not args.output:
                raise ValueError("--apply-plan requires a distinct --output")
            out = Path(args.output)
            if out.exists() or out.resolve() == Path(args.input).resolve():
                raise ValueError("output must be a new file")
            relocated = apply_plan(
                data["workflow"], data["catalog"], load(args.apply_plan)
            )
            with out.open("x", encoding="utf-8") as f:
                json.dump(relocated, f, indent=2, ensure_ascii=False)
            result = {**result, "output_written": str(out)}
        elif args.output:
            out = Path(args.output)
            if out.exists():
                raise ValueError("plan output must be a new file")
            with out.open("x", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
        if args.html:
            write_html(result, args.html)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["ready"] else 1
    except (ValueError, OSError, TypeError, KeyError) as e:
        print(str(e), file=sys.stderr)
        return 2


def load(path):
    p = Path(path)
    if p.stat().st_size > 4 * 1024 * 1024:
        raise ValueError("input exceeds 4 MiB")

    def pairs(items):
        d = {}
        for k, v in items:
            if k in d:
                raise ValueError("duplicate JSON key: " + k)
            d[k] = v
        return d

    return json.loads(
        p.read_text(encoding="utf-8"),
        object_pairs_hook=pairs,
        parse_constant=lambda x: (_ for _ in ()).throw(ValueError("nonfinite number")),
    )


def write_html(report, path):
    """Render escaped, searchable evidence tables without external assets."""
    esc = lambda x: html.escape(str(x))

    def table(headers, rows):
        return (
            "<table><thead><tr>"
            + "".join("<th>" + esc(x) + "</th>" for x in headers)
            + "</tr></thead><tbody>"
            + "".join(
                "<tr>" + "".join("<td>" + esc(x) + "</td>" for x in row) + "</tr>"
                for row in rows
            )
            + "</tbody></table>"
        )

    schema = report["schema"]
    sections = []
    cards = []
    if schema == "join-fanout/v1":
        title = "Where the extra join rows come from"
        subtitle = "Polars equi-join rehearsal. Group counts explain row growth before an expanded join is materialized."
        cards = [
            ("Left rows", report["left_rows"]),
            ("Right rows", report["right_rows"]),
            ("Output rows", report["output_rows"]),
            ("Row budget", report["max_rows"]),
        ]
        sections.append(
            "<h2>Keys contributing the most rows</h2>"
            + table(
                ["Key", "Left", "Right", "Matched pairs", "Output"],
                [
                    (
                        json.dumps(x["key"]),
                        x["left_rows"],
                        x["right_rows"],
                        x["matched_pairs"],
                        x["output_rows"],
                    )
                    for x in report["top_keys"]
                ],
            )
        )
        state = "Over row budget" if report["over_budget"] else "Within row budget"
    elif schema == "group-split-audit/v1":
        title = "Cross-validation split review"
        subtitle = "Review observable group, duplicate and time-window overlap before interpreting a validation score."
        cards = [
            ("Observations", report["rows"]),
            ("Folds", len(report["folds"])),
            ("Folds to review", sum(f["needs_review"] for f in report["folds"])),
        ]
        sections.append(
            "<h2>Fold findings</h2>"
            + table(
                [
                    "Fold",
                    "Train / test",
                    "Shared groups",
                    "Shared fingerprints",
                    "Window pairs",
                    "Unseen labels",
                ],
                [
                    (
                        f["fold"],
                        str(f["train_rows"]) + " / " + str(f["test_rows"]),
                        ", ".join(f["shared_groups"]) or "None",
                        ", ".join(f["shared_fingerprints"]) or "None",
                        f["overlapping_window_pairs"],
                        ", ".join(f["test_labels_absent_from_train"]) or "None",
                    )
                    for f in report["folds"]
                ],
            )
        )
        state = (
            "Review findings" if report["needs_review"] else "No declared overlap found"
        )
    elif schema == "compose-readiness-replay/v1":
        title = "What blocked startup"
        subtitle = "One ordered startup attempt, replayed against declared Compose dependency barriers."
        cards = [
            ("Events", len(report["timeline"])),
            ("Early starts", len(report["violations"])),
            ("Not started", len(report["not_started"])),
        ]
        sections.append(
            "<h2>Starts before their barriers were met</h2>"
            + table(
                ["Tick", "Service", "Waiting for"],
                [
                    (x["at"], x["service"], json.dumps(x["blocked_by"]))
                    for x in report["violations"]
                ],
            )
        )
        sections.append(
            "<h2>Observed event timeline</h2>"
            + table(
                ["Tick", "Service", "Event", "Ready to start after event"],
                [
                    (
                        x["at"],
                        x["service"],
                        x["event"],
                        ", ".join(x["ready_to_start"]) or "None",
                    )
                    for x in report["timeline"]
                ],
            )
        )
        state = (
            "Review findings"
            if report["needs_review"]
            else "Observed barriers respected"
        )
    elif schema == "n8n-relocation/v1":
        title = "Workflow relocation review"
        subtitle = "Local export reference mappings only. No server access, credential payloads or workflow activation."
        cards = [
            ("Planned mappings", len(report["operations"])),
            ("Unresolved references", len(report["unresolved"])),
        ]
        sections.append(
            "<h2>Reference changes</h2>"
            + table(
                ["Node", "Reference", "Before", "After"],
                [
                    (
                        x["node_id"],
                        x["kind"],
                        json.dumps(x["before"]),
                        json.dumps(x["after"]),
                    )
                    for x in report["operations"]
                ],
            )
        )
        sections.append(
            "<h2>Unresolved references</h2>"
            + table(
                ["Node", "Kind", "Reason"],
                [(x["node_id"], x["kind"], x["reason"]) for x in report["unresolved"]],
            )
        )
        state = (
            "Ready for review and local application"
            if report["ready"]
            else "Mapping is incomplete"
        )
    else:
        title = "Proxy wiring rehearsal"
        subtitle = "Local ASGI probes compare public redirects, documentation URLs and OpenAPI server prefixes."
        cards = [
            ("Scenarios", len(report["scenarios"])),
            ("Passing scenarios", sum(x["passed"] for x in report["scenarios"])),
        ]
        for scenario in report["scenarios"]:
            sections.append(
                "<h2>"
                + esc(scenario["name"])
                + (" · Pass" if scenario["passed"] else " · Review")
                + "</h2>"
                + table(
                    ["Public path", "Status", "Redirect / schema URL"],
                    [
                        (
                            x["path"],
                            x["status"],
                            x.get("location", x.get("docs_schema_url", "")),
                        )
                        for x in scenario["responses"]
                    ],
                )
            )
            sections.append(
                table(
                    ["Finding", "Path", "Evidence"],
                    [
                        (x["kind"], x["path"], json.dumps(x))
                        for x in scenario["findings"]
                    ],
                )
            )
        state = (
            "Review scenario differences"
            if report["needs_review"]
            else "All probe contracts passed"
        )
    body = html.escape(json.dumps(report, indent=2, ensure_ascii=False))
    css = "body{font:16px/1.6 system-ui;background:#f3f6fa;color:#182438;max-width:1100px;margin:40px auto;padding:0 24px}header{border-bottom:3px solid #137a68;padding-bottom:24px}h1{font-size:2.25rem;line-height:1.15;max-width:800px}h2{margin-top:40px;font-size:1.2rem}.cards{display:flex;gap:12px;flex-wrap:wrap;margin:24px 0}.card{background:white;padding:16px 22px;border:1px solid #d2dae5;border-radius:10px;min-width:140px}.card b{display:block;font-size:1.7rem;color:#0b6555}table{border-collapse:collapse;width:100%;background:white;margin-bottom:22px;display:block;overflow:auto}th,td{text-align:left;padding:12px;border-bottom:1px solid #d6deea;vertical-align:top}th{background:#e3eaf2}td{overflow-wrap:anywhere}input{font:inherit;padding:10px;width:min(90%,600px);border:1px solid #8593a6;border-radius:6px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:white;padding:20px;border:1px solid #d2dae5}.status{font-weight:700;color:#0b6555}footer{margin-top:40px;color:#4a5b73}details{margin-top:30px}label{display:block}"
    card_html = (
        '<div class="cards">'
        + "".join(
            '<div class="card">' + esc(k) + "<b>" + esc(v) + "</b></div>"
            for k, v in cards
        )
        + "</div>"
    )
    page = (
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'
        + esc(title)
        + "</title><style>"
        + css
        + "</style><header><p>LOCAL DIAGNOSTICS · SYNTHETIC EXAMPLE WHEN USING THE BUNDLED FIXTURE</p><h1>"
        + esc(title)
        + "</h1><p>"
        + esc(subtitle)
        + '</p><p class="status">'
        + esc(state)
        + "</p></header>"
        + card_html
        + '<label>Filter evidence rows <input id="q" type="search" placeholder="Service, key, group, path or finding"></label>'
        + "".join(sections)
        + "<details><summary>Complete JSON evidence</summary><pre>"
        + body
        + '</pre></details><footer>Read the repository limitations before acting. These results describe supplied inputs; they do not certify a live system.</footer><script>document.querySelector("#q").addEventListener("input",e=>{const q=e.target.value.toLowerCase();document.querySelectorAll("tbody tr").forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q))});</script></html>'
    )
    Path(path).write_text(page, encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())

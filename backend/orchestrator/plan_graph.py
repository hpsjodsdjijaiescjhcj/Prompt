from __future__ import annotations

import copy
import re


def build_plan_graph(spec: dict) -> dict | None:
    task_type = spec.get("task_type")
    if task_type == "email":
        return _build_email_graph(spec)
    if task_type == "generic":
        return _build_generic_graph(spec)
    return None


def validate_plan_graph(spec: dict, plan_graph: dict | None) -> dict:
    if not plan_graph:
        return {
            "pass": True,
            "phase": "preflight",
            "risk_level": "low",
            "plan_graph": None,
            "graph_findings": [],
            "precondition_issues": [],
            "broken_dependencies": [],
            "residual_targets": [],
            "repair_prompt": "",
            "node_statuses": {},
            "edge_statuses": {},
        }

    graph = copy.deepcopy(plan_graph)
    available_facts = _extract_available_facts(spec)
    node_statuses: dict[str, dict] = {}
    edge_statuses: dict[str, dict] = {}
    satisfied_nodes: set[str] = set()
    graph_findings: list[dict] = []
    precondition_issues: list[dict] = []
    broken_dependencies: list[dict] = []

    for node in graph.get("nodes", []):
        node_id = node["id"]
        unmet_dependencies = [dep for dep in node.get("depends_on", []) if dep not in satisfied_nodes]
        missing_inputs = [fact for fact in node.get("inputs", []) if fact not in available_facts]
        passed = not unmet_dependencies and not missing_inputs
        status = "pass" if passed else ("fail" if node.get("required", True) else "skipped")

        node_statuses[node_id] = {
            "status": status,
            "pass": passed,
            "missing_inputs": missing_inputs,
            "unmet_dependencies": unmet_dependencies,
        }

        if passed:
            satisfied_nodes.add(node_id)
            available_facts.update(node.get("outputs", []))
        else:
            if missing_inputs:
                entry = {
                    "type": "missing_input",
                    "message": f"Node '{node_id}' is missing required inputs: {', '.join(missing_inputs)}.",
                    "node_id": node_id,
                    "missing_inputs": missing_inputs,
                }
                graph_findings.append(entry)
                if node.get("required", True):
                    precondition_issues.append(entry)
            for dep in unmet_dependencies:
                edge_id = f"{dep}->{node_id}"
                broken = {
                    "type": "broken_dependency",
                    "message": f"Node '{node_id}' depends on '{dep}', which is not satisfiable yet.",
                    "node_id": node_id,
                    "edge_id": edge_id,
                    "from": dep,
                    "to": node_id,
                }
                broken_dependencies.append(broken)

    for edge in graph.get("edges", []):
        edge_id = f"{edge['from']}->{edge['to']}"
        edge_statuses[edge_id] = {
            "pass": edge["from"] in satisfied_nodes and edge["to"] in satisfied_nodes,
            "reason": edge.get("reason", ""),
        }

    graph_findings.extend(_validate_graph_rules(graph, available_facts))
    broken_dependencies.extend(_validate_exit_paths(graph, satisfied_nodes))
    graph_findings.extend(_validate_acceptance_mapping(spec, graph))

    residual_targets = _collect_graph_residual_targets(graph_findings, broken_dependencies, graph)
    graph["residual_targets"] = residual_targets
    graph["node_statuses"] = node_statuses
    graph["edge_statuses"] = edge_statuses

    pass_check = not any(item.get("severity", "error") == "error" for item in graph_findings) and not broken_dependencies and not precondition_issues

    return {
        "pass": pass_check,
        "phase": "preflight",
        "risk_level": _risk_level(len(graph_findings), len(broken_dependencies), len(precondition_issues)),
        "plan_graph": graph,
        "graph_findings": graph_findings,
        "precondition_issues": precondition_issues,
        "broken_dependencies": broken_dependencies,
        "residual_targets": residual_targets,
        "repair_prompt": _build_graph_repair_prompt(spec, graph_findings, broken_dependencies),
        "node_statuses": node_statuses,
        "edge_statuses": edge_statuses,
    }


def _build_email_graph(spec: dict) -> dict:
    constraints = spec.get("constraints") or {}
    deadline_required = bool(constraints.get("must_include_deadline"))
    bullets_required = bool(constraints.get("must_include_bullets"))
    acceptance_refs = [f"acc_{idx}" for idx, _ in enumerate(spec.get("acceptance_criteria") or [], start=1)]

    nodes = [
        {
            "id": "email_context",
            "label": "Context Establishment",
            "kind": "context",
            "required": True,
            "inputs": ["objective", "background", "recipient"],
            "outputs": ["context_ready"],
            "depends_on": [],
            "acceptance_refs": acceptance_refs[:1],
        },
        {
            "id": "email_request",
            "label": "Request Statement",
            "kind": "request",
            "required": True,
            "inputs": ["context_ready", "objective"],
            "outputs": ["request_ready"],
            "depends_on": ["email_context"],
            "acceptance_refs": acceptance_refs[1:2],
        },
        {
            "id": "email_commitment",
            "label": "Deadline and Action Items",
            "kind": "commitment",
            "required": True,
            "inputs": ["request_ready"] + (["deadline_value"] if deadline_required else []) + (["action_items_source"] if bullets_required else []),
            "outputs": ["commitment_ready"],
            "depends_on": ["email_request"],
            "acceptance_refs": acceptance_refs,
        },
        {
            "id": "email_close_loop",
            "label": "Response Loop Closure",
            "kind": "closure",
            "required": True,
            "inputs": ["commitment_ready"],
            "outputs": ["delivery_ready"],
            "depends_on": ["email_commitment"],
            "acceptance_refs": acceptance_refs,
        },
    ]
    edges = [
        {"from": "email_context", "to": "email_request", "reason": "the ask depends on concrete context"},
        {"from": "email_request", "to": "email_commitment", "reason": "the commitment should refine the concrete ask"},
        {"from": "email_commitment", "to": "email_close_loop", "reason": "response expectations depend on the stated commitments"},
    ]
    rules = [
        {
            "id": "email_acceptance_mapping",
            "label": "Acceptance criteria must map to graph nodes",
            "kind": "acceptance_mapping",
            "mapped_acceptance": acceptance_refs,
        }
    ]
    if deadline_required:
        rules.append(
            {
                "id": "email_deadline_rule",
                "label": "Deadline requirement must map to commitment node",
                "kind": "required_facts",
                "node_id": "email_commitment",
                "required_facts": ["deadline_value"],
            }
        )
    if bullets_required:
        rules.append(
            {
                "id": "email_bullets_rule",
                "label": "Action item requirement must map to commitment node",
                "kind": "required_facts",
                "node_id": "email_commitment",
                "required_facts": ["action_items_source"],
            }
        )
    return {
        "type": "task_graph",
        "task_type": "email",
        "nodes": nodes,
        "edges": edges,
        "entry_nodes": ["email_context"],
        "exit_nodes": ["email_close_loop"],
        "validation_rules": rules,
        "risk_edges": [
            {"from": "email_request", "to": "email_commitment", "reason": "deadline or action-item commitments are often underspecified"},
            {"from": "email_commitment", "to": "email_close_loop", "reason": "response loops often fail when no explicit ask-back exists"},
        ],
        "residual_targets": [],
    }


def _build_generic_graph(spec: dict) -> dict:
    weather = (spec.get("context") or {}).get("weather") or {}
    acceptance_refs = [f"acc_{idx}" for idx, _ in enumerate(spec.get("acceptance_criteria") or [], start=1)]
    nodes = [
        {
            "id": "generic_objective",
            "label": "Objective Framing",
            "kind": "objective",
            "required": True,
            "inputs": ["objective"],
            "outputs": ["objective_ready"],
            "depends_on": [],
            "acceptance_refs": acceptance_refs[:1],
        },
        {
            "id": "generic_context",
            "label": "Context Grounding",
            "kind": "context",
            "required": True,
            "inputs": ["objective_ready", "context_source"],
            "outputs": ["context_ready"],
            "depends_on": ["generic_objective"],
            "acceptance_refs": acceptance_refs[:2],
        },
    ]
    edges = [
        {"from": "generic_objective", "to": "generic_context", "reason": "context must ground a concrete objective"},
    ]
    if weather:
        nodes.append(
            {
                "id": "generic_weather_context",
                "label": "Weather Context",
                "kind": "context",
                "required": True,
                "inputs": ["context_ready", "weather_location", "weather_time_range"],
                "outputs": ["weather_ready"],
                "depends_on": ["generic_context"],
                "acceptance_refs": [],
            }
        )
        edges.append(
            {"from": "generic_context", "to": "generic_weather_context", "reason": "weather requests require explicit place and time grounding"}
        )
        output_inputs = ["weather_ready", "output_contract"]
        output_deps = ["generic_weather_context"]
    else:
        output_inputs = ["context_ready", "output_contract"]
        output_deps = ["generic_context"]
    nodes.extend(
        [
            {
                "id": "generic_output",
                "label": "Output Shaping",
                "kind": "output",
                "required": True,
                "inputs": output_inputs,
                "outputs": ["output_ready"],
                "depends_on": output_deps,
                "acceptance_refs": acceptance_refs,
            },
            {
                "id": "generic_acceptance",
                "label": "Acceptance Coverage",
                "kind": "validation",
                "required": True,
                "inputs": ["output_ready", "acceptance_defined"],
                "outputs": ["delivery_ready"],
                "depends_on": ["generic_output"],
                "acceptance_refs": acceptance_refs,
            },
        ]
    )
    edges.extend(
        [
            {"from": output_deps[0], "to": "generic_output", "reason": "the output format must be grounded in available context"},
            {"from": "generic_output", "to": "generic_acceptance", "reason": "the result should be checked against acceptance criteria before delivery"},
        ]
    )
    rules = [
        {
            "id": "generic_output_contract_rule",
            "label": "Generic output contract must map to the output-shaping node",
            "kind": "required_facts",
            "node_id": "generic_output",
            "required_facts": ["output_contract"],
        },
        {
            "id": "generic_acceptance_mapping",
            "label": "Acceptance criteria must map to graph validation",
            "kind": "acceptance_mapping",
            "mapped_acceptance": acceptance_refs,
        },
    ]
    if weather:
        rules.append(
            {
                "id": "generic_weather_rule",
                "label": "Weather tasks must declare location and time range",
                "kind": "required_facts",
                "node_id": "generic_weather_context",
                "required_facts": ["weather_location", "weather_time_range"],
            }
        )
    return {
        "type": "task_graph",
        "task_type": "generic",
        "nodes": nodes,
        "edges": edges,
        "entry_nodes": ["generic_objective"],
        "exit_nodes": ["generic_acceptance"],
        "validation_rules": rules,
        "risk_edges": [
            {"from": "generic_context", "to": "generic_output", "reason": "generic tasks often jump to output without enough grounded context"},
            {"from": "generic_output", "to": "generic_acceptance", "reason": "generic tasks often look complete while still missing acceptance coverage"},
        ],
        "residual_targets": [],
    }


def _extract_available_facts(spec: dict) -> set[str]:
    facts: set[str] = set()
    objective = (spec.get("objective") or "").strip()
    original_request = (spec.get("original_request") or "").strip()
    context = spec.get("context") or {}
    audience = spec.get("audience") or {}
    output_format = spec.get("output_format") or {}
    acceptance = spec.get("acceptance_criteria") or []
    constraints = spec.get("constraints") or {}
    weather = context.get("weather") or {}

    if objective:
        facts.add("objective")
    if original_request:
        facts.add("original_request")
    if (context.get("background") or "").strip():
        facts.add("background")
    if facts.intersection({"background", "original_request"}):
        facts.add("context_source")
    if audience.get("recipient_type") or audience.get("recipient_label") or audience.get("target"):
        facts.add("recipient")
    if acceptance:
        facts.add("acceptance_defined")
        for idx, _ in enumerate(acceptance, start=1):
            facts.add(f"acc_{idx}")
    if output_format.get("type") or output_format.get("sections"):
        facts.add("output_contract")
    if output_format.get("sections"):
        facts.add("output_sections")
    if constraints.get("must_include_bullets") is False or output_format.get("bullet_list_required") or output_format.get("sections") or (spec.get("must_include") or []):
        facts.add("action_items_source")

    deadline_sources = [
        (context.get("deadline_text") or "").strip(),
        "\n".join(spec.get("must_include") or []),
        objective,
        (context.get("background") or "").strip(),
    ]
    if any(_contains_concrete_deadline(text) for text in deadline_sources):
        facts.add("deadline_value")

    if weather.get("location"):
        facts.add("weather_location")
    if weather.get("time_range"):
        facts.add("weather_time_range")

    return facts


def _validate_graph_rules(graph: dict, available_facts: set[str]) -> list[dict]:
    findings = []
    for rule in graph.get("validation_rules", []):
        if rule.get("kind") == "required_facts":
            missing = [fact for fact in rule.get("required_facts", []) if fact not in available_facts]
            if missing:
                findings.append(
                    {
                        "type": "rule_failure",
                        "message": f"Rule '{rule['id']}' failed: missing facts {', '.join(missing)}.",
                        "node_id": rule.get("node_id"),
                        "rule_id": rule["id"],
                        "missing_facts": missing,
                        "severity": "error",
                    }
                )
    return findings


def _validate_exit_paths(graph: dict, satisfied_nodes: set[str]) -> list[dict]:
    broken = []
    for exit_node in graph.get("exit_nodes", []):
        if exit_node not in satisfied_nodes:
            broken.append(
                {
                    "type": "broken_exit_path",
                    "message": f"No valid path reaches exit node '{exit_node}'.",
                    "node_id": exit_node,
                    "edge_id": f"path::{exit_node}",
                    "from": None,
                    "to": exit_node,
                }
            )
    return broken


def _validate_acceptance_mapping(spec: dict, graph: dict) -> list[dict]:
    criteria = spec.get("acceptance_criteria") or []
    mapped = set()
    for node in graph.get("nodes", []):
        mapped.update(node.get("acceptance_refs", []))
    for rule in graph.get("validation_rules", []):
        mapped.update(rule.get("mapped_acceptance", []))

    findings = []
    for idx, _ in enumerate(criteria, start=1):
        acc_id = f"acc_{idx}"
        if acc_id not in mapped:
            findings.append(
                {
                    "type": "acceptance_unmapped",
                    "message": f"Acceptance criterion '{acc_id}' is not mapped to any graph node or rule.",
                    "node_id": None,
                    "rule_id": "acceptance_mapping",
                    "severity": "error",
                }
            )
    return findings


def _collect_graph_residual_targets(graph_findings: list[dict], broken_dependencies: list[dict], graph: dict) -> list[dict]:
    node_labels = {node["id"]: node["label"] for node in graph.get("nodes", [])}
    targets: dict[str, dict] = {}

    for finding in graph_findings:
        node_id = finding.get("node_id") or "graph_contract"
        target = targets.setdefault(
            node_id,
            {
                "target_id": node_id,
                "target_type": "node" if node_id in node_labels else "graph",
                "label": node_labels.get(node_id, "Graph Contract"),
                "issue_types": [],
                "messages": [],
            },
        )
        target["issue_types"].append(finding["type"])
        target["messages"].append(finding["message"])

    for broken in broken_dependencies:
        node_id = broken.get("to") or "graph_contract"
        target = targets.setdefault(
            node_id,
            {
                "target_id": node_id,
                "target_type": "node" if node_id in node_labels else "graph",
                "label": node_labels.get(node_id, "Graph Contract"),
                "issue_types": [],
                "messages": [],
            },
        )
        target["issue_types"].append(broken["type"])
        target["messages"].append(broken["message"])

    return list(targets.values())


def _build_graph_repair_prompt(spec: dict, graph_findings: list[dict], broken_dependencies: list[dict]) -> str:
    if not graph_findings and not broken_dependencies:
        return ""
    issue_lines = "\n".join(
        [f"- {row['type']}: {row['message']}" for row in graph_findings]
        + [f"- {row['type']}: {row['message']}" for row in broken_dependencies]
    )
    return (
        "Repair only the broken plan graph regions before execution.\n"
        f"Task type: {spec.get('task_type', '')}\n"
        f"Objective: {spec.get('objective', '')}\n"
        "Do not rewrite the entire task. Fix the failing nodes or dependencies below:\n"
        f"{issue_lines}\n"
        "Return an updated spec or plan patch that resolves these graph failures."
    )


def _risk_level(graph_count: int, broken_count: int, precondition_count: int) -> str:
    total = graph_count + broken_count + precondition_count
    if total >= 4:
        return "high"
    if total >= 2:
        return "medium"
    return "low"


def _contains_concrete_deadline(text: str) -> bool:
    if not text:
        return False
    patterns = [
        r"\d{1,2}月\d{1,2}日",
        r"\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?",
        r"before\s+\w+",
        r"截至",
        r"截止",
        r"最?晚",
    ]
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)

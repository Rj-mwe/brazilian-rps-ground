"""
AST Architectural Linter: Domain Isolation Audit for Ground Segment.
Ensures that rps_ground/core/domain never imports from adapters or infrastructure layers.
Follows strict Hexágono Dourado boundary rules.
"""
import ast
import sys
from pathlib import Path
from typing import Any, Dict, List


def audit_domain_isolation() -> Dict[str, Any]:
    current_dir = Path(__file__).resolve()
    repo_root = next(p for p in current_dir.parents if (p / "rps_ground").exists())
    domain_dir = repo_root / "rps_ground" / "core" / "domain"

    violations: List[str] = []
    forbidden_prefixes = ("rps_ground.adapters", "rps_ground.infrastructure")

    for py_file in domain_dir.rglob("*.py"):
        if py_file.name.startswith("__pycache__"):
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        except Exception as e:
            violations.append(f"Syntax error parsing {py_file}: {e}")
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if any(alias.name.startswith(p) for p in forbidden_prefixes):
                        violations.append(f"{py_file.name}:{node.lineno} imports forbidden module '{alias.name}'")
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if any(mod.startswith(p) for p in forbidden_prefixes):
                    violations.append(f"{py_file.name}:{node.lineno} imports from forbidden module '{mod}'")

    status = "PASSED" if not violations else "FAILED"
    return {
        "audit": "Ground Domain Strict Encapsulation (Hexágono Dourado)",
        "status": status,
        "violations": violations,
        "detail": (
            "Zero forbidden imports detected in rps_ground/core/domain/"
            if not violations
            else f"{len(violations)} boundary violations found!"
        )
    }


if __name__ == "__main__":
    result = audit_domain_isolation()
    print(f"[{result['status']}] {result['audit']}: {result['detail']}")
    if result["violations"]:
        for v in result["violations"]:
            print(f"  ❌ {v}")
        sys.exit(1)
    else:
        print("  ✅ All domain sub-cores strictly isolated.")
        sys.exit(0)

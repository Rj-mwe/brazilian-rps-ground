"""
AST Architectural Linter: Immutability Audit for Value Objects.
Ensures that all Value Objects in the domain layer are decorated with @dataclass(frozen=True).
"""
import ast
import sys
from pathlib import Path
from typing import Any, Dict, List


def audit_immutability() -> Dict[str, Any]:
    current_dir = Path(__file__).resolve()
    repo_root = next(p for p in current_dir.parents if (p / "rps_ground").exists())
    domain_dir = repo_root / "rps_ground" / "core" / "domain"

    violations: List[str] = []
    checked_count = 0

    for py_file in domain_dir.rglob("*.py"):
        if py_file.name.startswith("__"):
            continue
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        except Exception as e:
            violations.append(f"Syntax error in {py_file}: {e}")
            continue

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                # Check classes ending in 'VO'
                if node.name.endswith("VO"):
                    checked_count += 1
                    is_frozen = False
                    for dec in node.decorator_list:
                        if isinstance(dec, ast.Call):
                            for kw in dec.keywords:
                                if kw.arg == "frozen" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                                    is_frozen = True
                    if not is_frozen:
                        violations.append(f"Class '{node.name}' in {py_file.name} is NOT declared with @dataclass(frozen=True)")

    status = "PASSED" if not violations else "FAILED"
    return {
        "audit": "Value Object Immutability Enforcement (Hexágono Dourado)",
        "status": status,
        "violations": violations,
        "detail": (
            f"All {checked_count} Value Objects verified with frozen=True"
            if not violations
            else f"{len(violations)} mutable Value Objects detected!"
        )
    }


if __name__ == "__main__":
    result = audit_immutability()
    print(f"[{result['status']}] {result['audit']}: {result['detail']}")
    if result["violations"]:
        for v in result["violations"]:
            print(f"  ❌ {v}")
        sys.exit(1)
    else:
        print("  ✅ All Value Objects are strictly frozen and immutable.")
        sys.exit(0)

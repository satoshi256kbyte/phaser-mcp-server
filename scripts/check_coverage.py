#!/usr/bin/env python3
"""
Coverage threshold checker for Phaser MCP Server.

This script checks that each module meets its individual coverage threshold
and provides detailed reporting.
"""

import sys
from pathlib import Path
from typing import Dict

try:
    import coverage
except ImportError:
    print("❌ Coverage package not found. Please run tests with coverage first:")
    print("   uv run pytest --cov=phaser_mcp_server --cov-report=xml")
    sys.exit(1)


def check_module_coverage() -> bool:
    """Check coverage thresholds for each module."""
    # Define module coverage thresholds
    thresholds = {
        "phaser_mcp_server/models.py": 98,
        "phaser_mcp_server/parser.py": 90,
        "phaser_mcp_server/client.py": 90,
        "phaser_mcp_server/server.py": 90,
        "phaser_mcp_server/utils.py": 100,
    }

    # Load coverage data
    cov = coverage.Coverage()
    try:
        cov.load()
    except coverage.CoverageException as e:
        print(f"❌ Could not load coverage data: {e}")
        print("Run tests with coverage first: uv run pytest --cov=phaser_mcp_server")
        return False

    print("📊 Module Coverage Report")
    print("=" * 50)

    failed = False
    results = {}

    # Check each module
    for module, threshold in thresholds.items():
        try:
            # Check if file exists
            if not Path(module).exists():
                print(f"⚠️  Module {module} not found, skipping...")
                continue

            analysis = cov.analysis2(module)
            total_lines = len(analysis[1]) + len(analysis[2])
            covered_lines = len(analysis[1])
            coverage_pct = (covered_lines / total_lines) * 100 if total_lines > 0 else 0

            results[module] = {
                "coverage": coverage_pct,
                "threshold": threshold,
                "covered": covered_lines,
                "total": total_lines,
                "missing": len(analysis[2]),
            }

            status = "✅" if coverage_pct >= threshold else "❌"
            print(f"{status} {module}")
            print(f"   Coverage: {coverage_pct:.2f}% (threshold: {threshold}%)")
            print(
                f"   Lines: {covered_lines}/{total_lines} covered, {len(analysis[2])} missing"
            )

            if coverage_pct < threshold:
                failed = True
                print(f"   Missing lines: {analysis[2]}")

            print()

        except Exception as e:
            print(f"⚠️  Could not check coverage for {module}: {e}")
            print()

    # Overall summary
    print("📈 Summary")
    print("=" * 50)

    total_coverage = sum(r["covered"] for r in results.values())
    total_lines = sum(r["total"] for r in results.values())
    overall_pct = (total_coverage / total_lines) * 100 if total_lines > 0 else 0

    print(f"Overall coverage: {overall_pct:.2f}%")
    print(f"Total lines: {total_coverage}/{total_lines}")

    if failed:
        print("\n❌ Some modules are below their coverage thresholds!")
        return False
    else:
        print("\n✅ All modules meet their coverage thresholds!")
        return True


def main():
    """Main entry point."""
    success = check_module_coverage()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Generate a comprehensive test summary report
"""
import json
import subprocess
import sys
from pathlib import Path
import re


def run_command(cmd, capture_output=True):
    """Run a shell command and return the result"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=capture_output, text=True
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def get_test_metrics():
    """Get comprehensive test metrics"""
    print("🔍 Analyzing test metrics...")
    
    # Run pytest with coverage and collect output
    cmd = "python -m pytest tests/ --cov=app --cov-report=json:coverage/coverage.json --cov-report=term -q"
    returncode, stdout, stderr = run_command(cmd)
    
    # Parse coverage report
    coverage_file = Path("coverage/coverage.json")
    coverage_data = {}
    if coverage_file.exists():
        with open(coverage_file) as f:
            coverage_data = json.load(f)
    
    # Extract test results from output
    lines = stdout.split('\n') + stderr.split('\n')
    
    # Parse test counts
    test_counts = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0}
    coverage_percent = 0
    
    for line in lines:
        if "failed," in line and "passed" in line:
            # Extract numbers from line like "23 failed, 61 passed in 75.41s"
            numbers = re.findall(r'(\d+)', line)
            if len(numbers) >= 2:
                test_counts["failed"] = int(numbers[0])
                test_counts["passed"] = int(numbers[1])
        elif line.startswith("TOTAL") and "%" in line:
            # Extract coverage percentage
            match = re.search(r'(\d+)%', line)
            if match:
                coverage_percent = int(match.group(1))
    
    return {
        "test_counts": test_counts,
        "coverage_percent": coverage_percent,
        "coverage_data": coverage_data,
        "returncode": returncode
    }


def analyze_file_coverage(coverage_data):
    """Analyze coverage by file"""
    if not coverage_data or "files" not in coverage_data:
        return []
    
    file_coverage = []
    for filepath, data in coverage_data["files"].items():
        if filepath.startswith("app/"):
            summary = data["summary"]
            file_coverage.append({
                "file": filepath,
                "lines_covered": summary["covered_lines"],
                "lines_total": summary["num_statements"],
                "coverage_percent": round(summary["percent_covered"], 1),
                "missing_lines": summary["missing_lines"]
            })
    
    # Sort by coverage percentage
    file_coverage.sort(key=lambda x: x["coverage_percent"])
    return file_coverage


def generate_improvement_plan(file_coverage, test_counts):
    """Generate improvement recommendations"""
    improvements = []
    
    # Coverage improvements
    low_coverage_files = [f for f in file_coverage if f["coverage_percent"] < 70]
    if low_coverage_files:
        improvements.append({
            "priority": "HIGH",
            "category": "Coverage",
            "description": f"Improve test coverage for {len(low_coverage_files)} files with <70% coverage",
            "files": [f["file"] for f in low_coverage_files[:5]],  # Top 5
            "action": "Add unit tests for uncovered code paths"
        })
    
    # Test failures
    if test_counts["failed"] > 0:
        improvements.append({
            "priority": "CRITICAL", 
            "category": "Test Failures",
            "description": f"Fix {test_counts['failed']} failing tests",
            "action": "Debug and fix failing test cases"
        })
    
    # Missing test files
    app_modules = list(Path("app").rglob("*.py"))
    test_modules = list(Path("tests").rglob("test_*.py"))
    
    missing_tests = []
    for module in app_modules:
        if module.name != "__init__.py" and "test_" not in module.name:
            test_name = f"test_{module.stem}.py"
            test_path = Path("tests/unit") / test_name
            if not test_path.exists():
                missing_tests.append(str(module))
    
    if missing_tests:
        improvements.append({
            "priority": "MEDIUM",
            "category": "Missing Tests",
            "description": f"Create tests for {len(missing_tests)} modules without test coverage",
            "files": missing_tests[:3],  # Top 3
            "action": "Create comprehensive test suites"
        })
    
    return improvements


def generate_report():
    """Generate the complete test report"""
    print("📊 HomePro Scraper - Test Quality Report")
    print("=" * 50)
    
    # Get metrics
    metrics = get_test_metrics()
    file_coverage = analyze_file_coverage(metrics["coverage_data"])
    improvements = generate_improvement_plan(file_coverage, metrics["test_counts"])
    
    # Test Summary
    total_tests = sum(metrics["test_counts"].values())
    pass_rate = (metrics["test_counts"]["passed"] / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n🎯 TEST SUMMARY")
    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {metrics['test_counts']['passed']} ({pass_rate:.1f}%)")
    print(f"❌ Failed: {metrics['test_counts']['failed']}")
    print(f"⏭️  Skipped: {metrics['test_counts']['skipped']}")
    print(f"💥 Errors: {metrics['test_counts']['errors']}")
    
    # Coverage Summary
    print(f"\n📈 COVERAGE SUMMARY")
    print(f"Overall Coverage: {metrics['coverage_percent']}%")
    
    if file_coverage:
        print(f"Files with Tests: {len(file_coverage)}")
        
        # Best coverage
        best_files = [f for f in file_coverage if f["coverage_percent"] >= 80]
        print(f"High Coverage (≥80%): {len(best_files)} files")
        
        # Worst coverage
        worst_files = [f for f in file_coverage if f["coverage_percent"] < 50]
        print(f"Low Coverage (<50%): {len(worst_files)} files")
        
        print(f"\n📋 COVERAGE BY FILE (Top 10 lowest)")
        for i, file_info in enumerate(file_coverage[:10]):
            print(f"{i+1:2d}. {file_info['file']:<40} {file_info['coverage_percent']:>5.1f}%")
    
    # Improvements
    print(f"\n🔧 IMPROVEMENT RECOMMENDATIONS")
    for i, improvement in enumerate(improvements, 1):
        priority_emoji = {"CRITICAL": "🚨", "HIGH": "⚠️", "MEDIUM": "📋", "LOW": "💡"}
        emoji = priority_emoji.get(improvement["priority"], "🔹")
        
        print(f"{i}. {emoji} {improvement['priority']} - {improvement['category']}")
        print(f"   {improvement['description']}")
        print(f"   Action: {improvement['action']}")
        if "files" in improvement:
            print(f"   Files: {', '.join(improvement['files'][:3])}")
            if len(improvement['files']) > 3:
                print(f"   ... and {len(improvement['files']) - 3} more")
        print()
    
    # Quality Score
    quality_score = calculate_quality_score(metrics, file_coverage)
    print(f"🏆 OVERALL QUALITY SCORE: {quality_score}/100")
    print(f"   {'🟢 EXCELLENT' if quality_score >= 90 else '🟡 GOOD' if quality_score >= 70 else '🟠 NEEDS IMPROVEMENT' if quality_score >= 50 else '🔴 CRITICAL'}")
    
    return metrics["returncode"] == 0


def calculate_quality_score(metrics, file_coverage):
    """Calculate an overall quality score"""
    score = 0
    
    # Test pass rate (40 points)
    total_tests = sum(metrics["test_counts"].values())
    if total_tests > 0:
        pass_rate = metrics["test_counts"]["passed"] / total_tests
        score += int(pass_rate * 40)
    
    # Coverage (40 points)
    score += int(metrics["coverage_percent"] * 0.4)
    
    # Number of test files (10 points)
    test_files = len([f for f in file_coverage if f["coverage_percent"] > 0])
    score += min(test_files * 2, 10)
    
    # Bonus for high coverage files (10 points)
    high_coverage_files = len([f for f in file_coverage if f["coverage_percent"] >= 90])
    score += min(high_coverage_files, 10)
    
    return min(score, 100)


if __name__ == "__main__":
    # Ensure we're in the right directory
    if not Path("app").exists():
        print("❌ Please run this script from the project root directory")
        sys.exit(1)
    
    # Create coverage directory
    Path("coverage").mkdir(exist_ok=True)
    
    success = generate_report()
    sys.exit(0 if success else 1)
#!/bin/bash
# Test runner script for native scraping system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to run tests with coverage
run_tests_with_coverage() {
    local test_type="$1"
    local test_path="$2"
    local markers="$3"
    
    print_status "Running $test_type tests..."
    
    if [ -n "$markers" ]; then
        pytest "$test_path" -m "$markers" --cov=src --cov-report=html --cov-report=xml --cov-report=term-missing --cov-append
    else
        pytest "$test_path" --cov=src --cov-report=html --cov-report=xml --cov-report=term-missing --cov-append
    fi
    
    if [ $? -eq 0 ]; then
        print_success "$test_type tests passed!"
    else
        print_error "$test_type tests failed!"
        return 1
    fi
}

# Function to run tests without coverage
run_tests_simple() {
    local test_type="$1"
    local test_path="$2"
    local markers="$3"
    
    print_status "Running $test_type tests..."
    
    if [ -n "$markers" ]; then
        pytest "$test_path" -m "$markers" -v
    else
        pytest "$test_path" -v
    fi
    
    if [ $? -eq 0 ]; then
        print_success "$test_type tests passed!"
    else
        print_error "$test_type tests failed!"
        return 1
    fi
}

# Default values
COVERAGE=false
UNIT_TESTS=false
INTEGRATION_TESTS=false
E2E_TESTS=false
PERFORMANCE_TESTS=false
ALL_TESTS=false
VERBOSE=false
PARALLEL=false
FAIL_FAST=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --coverage)
            COVERAGE=true
            shift
            ;;
        --unit)
            UNIT_TESTS=true
            shift
            ;;
        --integration)
            INTEGRATION_TESTS=true
            shift
            ;;
        --e2e)
            E2E_TESTS=true
            shift
            ;;
        --performance)
            PERFORMANCE_TESTS=true
            shift
            ;;
        --all)
            ALL_TESTS=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --parallel)
            PARALLEL=true
            shift
            ;;
        --fail-fast)
            FAIL_FAST=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --coverage         Run tests with coverage reporting"
            echo "  --unit             Run unit tests only"
            echo "  --integration      Run integration tests only"
            echo "  --e2e              Run end-to-end tests only"
            echo "  --performance      Run performance tests only"
            echo "  --all              Run all tests"
            echo "  --verbose          Verbose output"
            echo "  --parallel         Run tests in parallel"
            echo "  --fail-fast        Stop on first failure"
            echo "  --help             Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --unit --coverage"
            echo "  $0 --all --parallel"
            echo "  $0 --e2e --verbose"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Set default to run all tests if no specific test type is specified
if [ "$UNIT_TESTS" = false ] && [ "$INTEGRATION_TESTS" = false ] && [ "$E2E_TESTS" = false ] && [ "$PERFORMANCE_TESTS" = false ] && [ "$ALL_TESTS" = false ]; then
    ALL_TESTS=true
fi

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    print_error "pytest is not installed. Please install it with: pip install pytest"
    exit 1
fi

# Check if coverage is installed when coverage is requested
if [ "$COVERAGE" = true ] && ! command -v coverage &> /dev/null; then
    print_error "coverage is not installed. Please install it with: pip install coverage"
    exit 1
fi

# Check if playwright is installed for E2E tests
if [ "$E2E_TESTS" = true ] || [ "$ALL_TESTS" = true ]; then
    if ! python -c "import playwright" 2>/dev/null; then
        print_warning "Playwright not installed. E2E tests will be skipped."
        print_warning "To install Playwright: pip install playwright && playwright install"
    fi
fi

# Set pytest options
PYTEST_OPTIONS=""
if [ "$VERBOSE" = true ]; then
    PYTEST_OPTIONS="$PYTEST_OPTIONS -v"
fi
if [ "$PARALLEL" = true ]; then
    PYTEST_OPTIONS="$PYTEST_OPTIONS -n auto"
fi
if [ "$FAIL_FAST" = true ]; then
    PYTEST_OPTIONS="$PYTEST_OPTIONS --maxfail=1"
fi

# Export pytest options
export PYTEST_OPTIONS

print_status "Starting native scraping test suite..."
print_status "Working directory: $(pwd)"

# Clean up previous coverage data
if [ "$COVERAGE" = true ]; then
    print_status "Cleaning up previous coverage data..."
    coverage erase
fi

# Run tests based on options
TEST_FAILED=false

if [ "$ALL_TESTS" = true ]; then
    print_status "Running all tests..."
    
    # Unit tests
    if [ "$COVERAGE" = true ]; then
        run_tests_with_coverage "Unit" "tests/unit/" "unit and native"
    else
        run_tests_simple "Unit" "tests/unit/" "unit and native"
    fi
    [ $? -ne 0 ] && TEST_FAILED=true
    
    # Integration tests
    if [ "$COVERAGE" = true ]; then
        run_tests_with_coverage "Integration" "tests/integration/" "integration and native"
    else
        run_tests_simple "Integration" "tests/integration/" "integration and native"
    fi
    [ $? -ne 0 ] && TEST_FAILED=true
    
    # E2E tests (if Playwright is available)
    if python -c "import playwright" 2>/dev/null; then
        if [ "$COVERAGE" = true ]; then
            run_tests_with_coverage "E2E" "tests/e2e/" "e2e and native"
        else
            run_tests_simple "E2E" "tests/e2e/" "e2e and native"
        fi
        [ $? -ne 0 ] && TEST_FAILED=true
    else
        print_warning "Skipping E2E tests (Playwright not available)"
    fi
    
    # Performance tests
    if [ "$COVERAGE" = true ]; then
        run_tests_with_coverage "Performance" "tests/performance/" "performance and native"
    else
        run_tests_simple "Performance" "tests/performance/" "performance and native"
    fi
    [ $? -ne 0 ] && TEST_FAILED=true
    
else
    # Run specific test types
    if [ "$UNIT_TESTS" = true ]; then
        if [ "$COVERAGE" = true ]; then
            run_tests_with_coverage "Unit" "tests/unit/" "unit and native"
        else
            run_tests_simple "Unit" "tests/unit/" "unit and native"
        fi
        [ $? -ne 0 ] && TEST_FAILED=true
    fi
    
    if [ "$INTEGRATION_TESTS" = true ]; then
        if [ "$COVERAGE" = true ]; then
            run_tests_with_coverage "Integration" "tests/integration/" "integration and native"
        else
            run_tests_simple "Integration" "tests/integration/" "integration and native"
        fi
        [ $? -ne 0 ] && TEST_FAILED=true
    fi
    
    if [ "$E2E_TESTS" = true ]; then
        if python -c "import playwright" 2>/dev/null; then
            if [ "$COVERAGE" = true ]; then
                run_tests_with_coverage "E2E" "tests/e2e/" "e2e and native"
            else
                run_tests_simple "E2E" "tests/e2e/" "e2e and native"
            fi
            [ $? -ne 0 ] && TEST_FAILED=true
        else
            print_error "Playwright not installed. Cannot run E2E tests."
            TEST_FAILED=true
        fi
    fi
    
    if [ "$PERFORMANCE_TESTS" = true ]; then
        if [ "$COVERAGE" = true ]; then
            run_tests_with_coverage "Performance" "tests/performance/" "performance and native"
        else
            run_tests_simple "Performance" "tests/performance/" "performance and native"
        fi
        [ $? -ne 0 ] && TEST_FAILED=true
    fi
fi

# Generate coverage report
if [ "$COVERAGE" = true ]; then
    print_status "Generating coverage report..."
    coverage report
    coverage html
    coverage xml
    
    print_success "Coverage report generated in htmlcov/index.html"
fi

# Summary
echo ""
echo "=========================================="
echo "TEST SUMMARY"
echo "=========================================="

if [ "$TEST_FAILED" = true ]; then
    print_error "Some tests failed!"
    exit 1
else
    print_success "All tests passed!"
    
    if [ "$COVERAGE" = true ]; then
        echo ""
        print_status "Coverage Summary:"
        coverage report --skip-covered | tail -1
    fi
fi

echo ""
print_success "Test suite completed successfully!"
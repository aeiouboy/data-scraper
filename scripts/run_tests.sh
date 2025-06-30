#!/bin/bash

# HomePro Scraper Test Runner Script
# Usage: ./scripts/run_tests.sh [test_type] [options]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
TEST_TYPE="all"
COVERAGE=true
VERBOSE=false
STRICT=false
PARALLEL=false
MARKERS=""

# Help function
show_help() {
    cat << EOF
HomePro Scraper Test Runner

Usage: $0 [test_type] [options]

Test Types:
    unit        Run unit tests only
    integration Run integration tests only
    e2e         Run end-to-end tests only
    all         Run all tests (default)

Options:
    -c, --coverage      Generate coverage report (default: true)
    --no-coverage       Disable coverage reporting
    -v, --verbose       Verbose output
    -s, --strict        Strict mode (fail on warnings)
    -p, --parallel      Run tests in parallel
    -m, --markers       Run tests with specific markers (e.g., "not slow")
    -h, --help          Show this help message

Examples:
    $0 unit                         # Run unit tests with coverage
    $0 integration --no-coverage    # Run integration tests without coverage
    $0 e2e -v                       # Run E2E tests with verbose output
    $0 all -p -m "not slow"        # Run all non-slow tests in parallel
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        unit|integration|e2e|all)
            TEST_TYPE="$1"
            shift
            ;;
        -c|--coverage)
            COVERAGE=true
            shift
            ;;
        --no-coverage)
            COVERAGE=false
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -s|--strict)
            STRICT=true
            shift
            ;;
        -p|--parallel)
            PARALLEL=true
            shift
            ;;
        -m|--markers)
            MARKERS="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

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

# Function to check if virtual environment is activated
check_venv() {
    if [[ -z "$VIRTUAL_ENV" ]]; then
        print_warning "Virtual environment not detected"
        if [[ -f "venv/bin/activate" ]]; then
            print_status "Activating virtual environment..."
            source venv/bin/activate
        else
            print_error "No virtual environment found. Please run: python -m venv venv && source venv/bin/activate"
            exit 1
        fi
    else
        print_status "Virtual environment active: $VIRTUAL_ENV"
    fi
}

# Function to install test dependencies
install_dependencies() {
    print_status "Checking test dependencies..."
    
    # Check if pytest is installed
    if ! python -c "import pytest" 2>/dev/null; then
        print_status "Installing test dependencies..."
        pip install pytest pytest-asyncio pytest-cov pytest-xdist selenium
    fi
    
    # Install additional dependencies for E2E tests
    if [[ "$TEST_TYPE" == "e2e" || "$TEST_TYPE" == "all" ]]; then
        if ! python -c "import selenium" 2>/dev/null; then
            print_status "Installing Selenium for E2E tests..."
            pip install selenium
        fi
        
        # Check for Chrome/ChromeDriver
        if ! command -v google-chrome &> /dev/null && ! command -v chromium-browser &> /dev/null; then
            print_warning "Chrome browser not found. E2E tests may fail."
            print_warning "Please install Chrome or Chromium for E2E tests."
        fi
    fi
}

# Function to prepare test environment
prepare_environment() {
    print_status "Preparing test environment..."
    
    # Create coverage directory
    mkdir -p coverage
    
    # Set test environment variables
    export TESTING=true
    export ENVIRONMENT=test
    
    # Create temporary test database if needed
    # (Add database setup logic here if required)
}

# Function to build pytest command
build_pytest_command() {
    local cmd="python -m pytest"
    
    # Add test path based on type
    case $TEST_TYPE in
        unit)
            cmd="$cmd tests/unit/"
            ;;
        integration)
            cmd="$cmd tests/integration/"
            ;;
        e2e)
            cmd="$cmd tests/e2e/"
            ;;
        all)
            cmd="$cmd tests/"
            ;;
    esac
    
    # Add coverage options
    if [[ "$COVERAGE" == true ]]; then
        cmd="$cmd --cov=app --cov-report=html:coverage/html --cov-report=term-missing --cov-report=json:coverage/coverage.json"
    fi
    
    # Add verbose option
    if [[ "$VERBOSE" == true ]]; then
        cmd="$cmd -v"
    fi
    
    # Add strict mode
    if [[ "$STRICT" == true ]]; then
        cmd="$cmd --strict-markers --strict-config"
    fi
    
    # Add parallel execution
    if [[ "$PARALLEL" == true ]]; then
        cmd="$cmd -n auto"
    fi
    
    # Add markers
    if [[ -n "$MARKERS" ]]; then
        cmd="$cmd -m \"$MARKERS\""
    fi
    
    echo "$cmd"
}

# Function to run tests
run_tests() {
    local pytest_cmd=$(build_pytest_command)
    
    print_status "Running $TEST_TYPE tests..."
    print_status "Command: $pytest_cmd"
    
    # Run the tests
    eval $pytest_cmd
    local exit_code=$?
    
    if [[ $exit_code -eq 0 ]]; then
        print_success "All tests passed!"
    else
        print_error "Some tests failed (exit code: $exit_code)"
        return $exit_code
    fi
}

# Function to generate reports
generate_reports() {
    if [[ "$COVERAGE" == true ]]; then
        print_status "Generating coverage reports..."
        
        # Generate XML report for CI
        python -m coverage xml -o coverage/coverage.xml
        
        # Show coverage summary
        echo ""
        print_status "Coverage Summary:"
        python -m coverage report --show-missing
        
        if [[ -f "coverage/html/index.html" ]]; then
            print_success "HTML coverage report generated: coverage/html/index.html"
        fi
        
        # Check coverage threshold
        local coverage_percentage=$(python -c "
import json
with open('coverage/coverage.json') as f:
    data = json.load(f)
    print(f\"{data['totals']['percent_covered']:.1f}\")
")
        
        print_status "Total coverage: ${coverage_percentage}%"
        
        # Fail if coverage is below threshold (80%)
        if (( $(echo "$coverage_percentage < 80" | bc -l) )); then
            print_warning "Coverage is below 80% threshold"
        fi
    fi
}

# Function to cleanup
cleanup() {
    print_status "Cleaning up..."
    
    # Stop any background services if started
    # (Add cleanup logic here)
    
    # Remove temporary files
    find . -name "*.pyc" -delete
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
}

# Main execution
main() {
    print_status "HomePro Scraper Test Runner"
    print_status "Test Type: $TEST_TYPE"
    print_status "Coverage: $COVERAGE"
    print_status "Verbose: $VERBOSE"
    print_status "Strict: $STRICT"
    print_status "Parallel: $PARALLEL"
    
    if [[ -n "$MARKERS" ]]; then
        print_status "Markers: $MARKERS"
    fi
    
    echo ""
    
    # Set up trap for cleanup on exit
    trap cleanup EXIT
    
    # Execute test pipeline
    check_venv
    install_dependencies
    prepare_environment
    run_tests
    local test_exit_code=$?
    generate_reports
    
    # Final status
    echo ""
    if [[ $test_exit_code -eq 0 ]]; then
        print_success "Test run completed successfully!"
    else
        print_error "Test run failed!"
        exit $test_exit_code
    fi
}

# Run main function
main "$@"
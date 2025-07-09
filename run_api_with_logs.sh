#!/bin/bash
# Run API server with logging to files

# Create logs directory if it doesn't exist
mkdir -p logs

# Get current date for log file naming
DATE=$(date +%Y%m%d_%H%M%S)

echo "Starting API server with logging..."
echo "Logs will be written to:"
echo "  - logs/api.log (main log)"
echo "  - logs/api_error.log (errors only)"
echo ""

# Run the API and redirect output to log files
# stdout goes to api.log, stderr goes to api_error.log
python run_api.py 2>&1 | tee -a logs/api.log
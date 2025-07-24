#!/bin/bash
# Data Organization Setup Script
# Sets up the complete data organization system

set -e

echo "=================================="
echo "RIS Data Scrap - Data Organization Setup"
echo "=================================="

# Set base directory
BASE_DIR="/Users/chongraktanaka/Documents/Project/ris data scrap"
cd "$BASE_DIR"

echo "Setting up data organization system..."

# Create directory structure (already done, but ensure it exists)
echo "✓ Ensuring directory structure exists..."
mkdir -p data/config/{retailers,scraping,system,application}
mkdir -p data/active/{analysis/{data-quality,performance,debugging},scraping/{results,progress,validation},testing/{unit,integration,e2e},imports}
mkdir -p data/temp/{processing,debug,cache}
mkdir -p data/backups/{daily,weekly,manual}
mkdir -p data/exports/{csv,reports,api}
mkdir -p data/archive/{analysis,backups,historical}

# Create documentation directory
mkdir -p docs/data_governance

# Make scripts executable
echo "✓ Making scripts executable..."
chmod +x scripts/data_migration.py
chmod +x scripts/data_lifecycle_manager.py

# Create requirements file for data management utilities
echo "✓ Creating requirements for data utilities..."
cat > requirements-data.txt << EOF
# Data Management Requirements
jsonschema>=4.0.0
pathlib2>=2.3.0
hashlib2>=1.0.0
python-dateutil>=2.8.0
EOF

# Create cron job configuration for automated cleanup
echo "✓ Creating cron job configuration..."
cat > scripts/crontab_data_management << EOF
# Data Management Cron Jobs
# Daily cleanup at 2 AM
0 2 * * * cd "$BASE_DIR" && python scripts/data_lifecycle_manager.py --cleanup-temp

# Weekly archiving on Sundays at 3 AM  
0 3 * * 0 cd "$BASE_DIR" && python scripts/data_lifecycle_manager.py --archive-old

# Monthly retention report on 1st of month at 1 AM
0 1 1 * * cd "$BASE_DIR" && python scripts/data_lifecycle_manager.py --retention-report

# Quarterly deep cleanup on 1st of quarter at 4 AM
0 4 1 1,4,7,10 * cd "$BASE_DIR" && python scripts/data_lifecycle_manager.py --deep-cleanup
EOF

# Create .gitignore additions for data directories
echo "✓ Updating .gitignore for data management..."
cat >> .gitignore << EOF

# Data Management
data/temp/
data/active/analysis/
data/active/testing/
data/archive/
*.log
*_temp.json
*_cache.json
EOF

# Create configuration file
echo "✓ Creating data management configuration..."
cat > data/config/system/data_management_config.json << EOF
{
  "metadata": {
    "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "created_by": "setup_script",
    "file_type": "configuration",
    "data_source": "data_organization_setup",
    "retention_policy": "permanent",
    "description": "Data management system configuration",
    "version": "1.0",
    "schema_version": "1.0"
  },
  "data": {
    "retention_policies": {
      "config": -1,
      "analysis_dataquality": 90,
      "analysis_performance": 90,
      "analysis_debugging": 90,
      "scraping_results": 180,
      "scraping_progress": 30,
      "scraping_validation": 60,
      "test_unit": 30,
      "test_integration": 30,
      "test_e2e": 30,
      "backup_daily": 30,
      "backup_weekly": 90,
      "backup_manual": 365,
      "temp_processing": 7,
      "temp_debug": 14,
      "temp_cache": 3,
      "export_csv": 90,
      "export_reports": 180,
      "export_api": 30
    },
    "naming_conventions": {
      "pattern": "{category}_{subcategory}_{description}_{timestamp}.{extension}",
      "timestamp_format": "YYYYMMDD_HHMMSS",
      "timezone": "UTC",
      "valid_categories": ["config", "analysis", "scraping", "test", "backup", "temp", "export"],
      "valid_extensions": ["json", "csv", "txt", "log"]
    },
    "quality_thresholds": {
      "critical_data": 0.95,
      "operational_data": 0.90,
      "analytical_data": 0.85
    },
    "storage_limits": {
      "temp_max_size_gb": 5,
      "active_max_size_gb": 50,
      "archive_max_size_gb": 200
    },
    "monitoring": {
      "check_interval_hours": 24,
      "alert_thresholds": {
        "storage_warning": 0.80,
        "storage_critical": 0.95,
        "quality_warning": 0.85,
        "quality_critical": 0.75
      }
    }
  }
}
EOF

# Test data standards utility
echo "✓ Testing data standards utility..."
if python -c "from src.utils.data_standards import DataStandards; print('Data standards utility working')"; then
    echo "  ✓ Data standards utility test passed"
else
    echo "  ⚠ Data standards utility test failed - check dependencies"
fi

# Create initial data inventory
echo "✓ Creating initial data inventory..."
python << EOF
import json
import os
from datetime import datetime
from pathlib import Path

base_path = Path("$BASE_DIR")
inventory = {
    "metadata": {
        "created_at": datetime.utcnow().isoformat() + "Z",
        "created_by": "setup_script",
        "file_type": "inventory",
        "description": "Initial data inventory after organization setup"
    },
    "data": {
        "directories_created": [],
        "json_files_found": [],
        "next_steps": [
            "Run data migration script",
            "Configure automated cleanup",
            "Set up monitoring alerts",
            "Train team on new procedures"
        ]
    }
}

# Count directories created
for root, dirs, files in os.walk(base_path / "data"):
    for dir_name in dirs:
        dir_path = Path(root) / dir_name
        inventory["data"]["directories_created"].append(str(dir_path.relative_to(base_path)))

# Count existing JSON files
for json_file in base_path.rglob("*.json"):
    if not any(excluded in str(json_file) for excluded in ["node_modules", "venv", ".git"]):
        inventory["data"]["json_files_found"].append(str(json_file.relative_to(base_path)))

# Save inventory
inventory_file = base_path / "data" / "config" / "system" / "initial_inventory.json"
with open(inventory_file, 'w') as f:
    json.dump(inventory, f, indent=2)

print(f"Inventory saved to: {inventory_file}")
print(f"Directories created: {len(inventory['data']['directories_created'])}")
print(f"JSON files found: {len(inventory['data']['json_files_found'])}")
EOF

echo ""
echo "=================================="
echo "✓ Data Organization Setup Complete!"
echo "=================================="
echo ""
echo "Next Steps:"
echo "1. Review the setup:"
echo "   - Check data directory structure: ls -la data/"
echo "   - Review configuration: cat data/config/system/data_management_config.json"
echo ""
echo "2. Run data migration:"
echo "   python scripts/data_migration.py"
echo ""
echo "3. Test lifecycle management:"
echo "   python scripts/data_lifecycle_manager.py"
echo ""
echo "4. Set up automated cleanup (optional):"
echo "   crontab scripts/crontab_data_management"
echo ""
echo "5. Review documentation:"
echo "   - Data Management Policies: docs/data_governance/DATA_MANAGEMENT_POLICIES.md"
echo "   - JSON Organization Analysis: JSON_DATA_ORGANIZATION_ANALYSIS.md"
echo ""
echo "Files created:"
echo "  ✓ Directory structure in data/"
echo "  ✓ Data migration script: scripts/data_migration.py"
echo "  ✓ Lifecycle manager: scripts/data_lifecycle_manager.py"
echo "  ✓ Data standards utility: src/utils/data_standards.py"
echo "  ✓ Management policies: docs/data_governance/DATA_MANAGEMENT_POLICIES.md"
echo "  ✓ Configuration: data/config/system/data_management_config.json"
echo ""
echo "The data organization system is ready for use!"
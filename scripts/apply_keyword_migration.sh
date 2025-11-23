#!/bin/bash
# =====================================================================
# Apply Keyword Schema Migration
# =====================================================================
# This script applies the keyword enhancement migration to the PostgreSQL database.
#
# Usage:
#   ./scripts/apply_keyword_migration.sh [database_name] [user] [host] [port]
#
# Examples:
#   # Use defaults (ra_d_ps_db, ra_d_ps_user, localhost, 5432)
#   ./scripts/apply_keyword_migration.sh
#
#   # Specify database
#   ./scripts/apply_keyword_migration.sh my_database my_user localhost 5432
# =====================================================================

set -e  # Exit on error

# Configuration
DB_NAME="${1:-ra_d_ps_db}"
DB_USER="${2:-ra_d_ps_user}"
DB_HOST="${3:-localhost}"
DB_PORT="${4:-5432}"

MIGRATION_FILE="migrations/002_add_keyword_enhancements.sql"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=================================================================${NC}"
echo -e "${GREEN}  RA-D-PS Keyword Enhancement Migration${NC}"
echo -e "${GREEN}=================================================================${NC}"
echo ""
echo "Database: $DB_NAME"
echo "User:     $DB_USER"
echo "Host:     $DB_HOST"
echo "Port:     $DB_PORT"
echo "Migration: $MIGRATION_FILE"
echo ""

# Check if migration file exists
if [ ! -f "$MIGRATION_FILE" ]; then
    echo -e "${RED}Error: Migration file not found: $MIGRATION_FILE${NC}"
    exit 1
fi

# Check if psql is installed
if ! command -v psql &> /dev/null; then
    echo -e "${RED}Error: psql not found. Please install PostgreSQL client.${NC}"
    exit 1
fi

# Test database connection
echo -e "${YELLOW}Testing database connection...${NC}"
if ! PGPASSWORD="${DB_PASSWORD:-changeme}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c '\q' 2>/dev/null; then
    echo -e "${RED}Error: Cannot connect to database${NC}"
    echo "Please check your database credentials and ensure PostgreSQL is running."
    exit 1
fi

echo -e "${GREEN}✓ Database connection successful${NC}"
echo ""

# Check if migration has already been applied
echo -e "${YELLOW}Checking migration status...${NC}"
MIGRATION_EXISTS=$(PGPASSWORD="${DB_PASSWORD:-changeme}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT EXISTS(SELECT 1 FROM schema_versions WHERE version = 2);" 2>/dev/null | tr -d '[:space:]')

if [ "$MIGRATION_EXISTS" = "t" ]; then
    echo -e "${YELLOW}⚠️  Migration 002 has already been applied${NC}"
    read -p "Do you want to re-apply the migration? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Migration cancelled."
        exit 0
    fi
fi

# Apply migration
echo -e "${YELLOW}Applying migration...${NC}"
if PGPASSWORD="${DB_PASSWORD:-changeme}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -f "$MIGRATION_FILE"; then
    echo ""
    echo -e "${GREEN}=================================================================${NC}"
    echo -e "${GREEN}✅ Migration applied successfully!${NC}"
    echo -e "${GREEN}=================================================================${NC}"
    echo ""
    echo "Database schema updated with:"
    echo "  - New keyword columns: definition, source_refs, is_standard, vocabulary_source"
    echo "  - Consolidated view: v_keyword_consolidated"
    echo "  - Category-specific views (v_keywords_*)"
    echo "  - Helper functions: get_keywords_by_category(), search_keywords_full()"
    echo ""
    echo "Next steps:"
    echo "  1. Import keyword data: python scripts/import_keyword_csv.py data/keywords_radiology_standard.csv"
    echo "  2. Query consolidated view: SELECT * FROM v_keyword_consolidated LIMIT 10;"
else
    echo ""
    echo -e "${RED}=================================================================${NC}"
    echo -e "${RED}❌ Migration failed${NC}"
    echo -e "${RED}=================================================================${NC}"
    exit 1
fi

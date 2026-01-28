#!/usr/bin/env bash
# Check for duplicate names across agents/, commands/, and skills/ directories
# Prevents naming conflicts when loading configurations
# Compatible with bash 3.2+ (macOS default)

set -euo pipefail

# Color output for better visibility
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo "Checking for duplicate names in agents, commands, and skills..."

# Create temporary file to store all names
tmpfile=$(mktemp)
trap 'rm -f "$tmpfile"' EXIT

# Collect all basenames (format: "name filepath")
find_names() {
  local dir=$1
  if [ -d "$dir" ]; then
    for file in "$dir"/*.md; do
      [ -f "$file" ] || continue
      name=$(basename "$file" .md)
      echo "$name $file" >> "$tmpfile"
    done
  fi
}

find_names "agents"
find_names "commands"
find_names "skills"

# Check for duplicates using sort and uniq
duplicates_found=0

# Sort by name and check for duplicates
while IFS= read -r line; do
  name=$(echo "$line" | awk '{print $1}')

  # Count occurrences of this name
  count=$(grep -c "^$name " "$tmpfile" || true)

  if [ "$count" -gt 1 ]; then
    if [ "$duplicates_found" -eq 0 ]; then
      echo -e "${RED}✗ Duplicate names detected:${NC}"
      duplicates_found=1
    fi

    echo ""
    echo "Name '$name' appears $count times:"
    grep "^$name " "$tmpfile" | awk '{print "  - " $2}'
  fi
done < <(sort -u -k1,1 "$tmpfile")

if [ "$duplicates_found" -eq 1 ]; then
  echo ""
  echo -e "${RED}✗ Each agent/command/skill must have a unique name.${NC}"
  exit 1
else
  echo -e "${GREEN}✓ No duplicate names found across agents, commands, and skills.${NC}"
  exit 0
fi

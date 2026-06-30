#!/bin/bash

# Quality checks for the code-review-task-grouping research project.
#
# This is a docs/data project (Markdown specs + a JSONL commit bank + Python
# helper scripts), so "quality" here means:
#   1. Markdown tables in docs are auto-formatted/aligned (scripts/fmt-md-tables.py)
#   2. bank.jsonl is valid JSON Lines
#   3. Python helper scripts compile (py_compile)
#
# Run from the project root:  ./scripts/run_quality_checks.sh
# It is also invoked automatically by .git/hooks/pre-commit.

set -u

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PY="$(command -v python3 || command -v python)"
if [ -z "$PY" ]; then
    echo -e "${RED}python3 not found on PATH${NC}"
    exit 1
fi

failed=()

echo "==============================================="
echo "Running quality checks"
echo "==============================================="

# Collect a newline-separated file list into a bash-3.2-safe positional array.
# Usage: list_md_files; then iterate "$@" after `set --`.
list_md_files() {
    if git rev-parse --git-dir >/dev/null 2>&1; then
        git ls-files '*.md' 2>/dev/null | grep -v '^corpus/repo/'
    else
        find . -path ./corpus/repo -prune -o -name '*.md' -print | sed 's#^\./##'
    fi
}

# 1. Markdown table formatting (auto-fix). Excludes the nested cal.com corpus.
echo -e "${YELLOW}Markdown table formatting…${NC}"
MD_LIST="$(list_md_files)"
if [ -n "$MD_LIST" ]; then
    # shellcheck disable=SC2086
    OLD_IFS="$IFS"; IFS=$'\n'; set -f; set -- $MD_LIST; set +f; IFS="$OLD_IFS"
    if "$PY" "$SCRIPT_DIR/fmt-md-tables.py" "$@" >/dev/null; then
        # Re-stage any files the formatter changed so the fix lands in this commit.
        if git rev-parse --git-dir >/dev/null 2>&1; then
            for f in "$@"; do
                git add -- "$f" 2>/dev/null || true
            done
        fi
        echo -e "${GREEN}✅ Markdown tables formatted${NC}"
    else
        echo -e "${RED}❌ Markdown table formatter errored${NC}"
        failed+=("md-format")
    fi
else
    echo -e "${GREEN}✅ No Markdown files to format${NC}"
fi

# 2. bank.jsonl validity (one JSON object per non-empty line).
echo -e "${YELLOW}Validating corpus/bank.jsonl…${NC}"
if [ -f corpus/bank.jsonl ]; then
    if "$PY" - corpus/bank.jsonl <<'PYEOF'
import json, sys
path = sys.argv[1]
bad = 0
with open(path, encoding="utf-8") as f:
    for n, line in enumerate(f, 1):
        s = line.strip()
        if not s:
            continue
        try:
            json.loads(s)
        except json.JSONDecodeError as e:
            bad += 1
            print(f"  {path}:{n}: {e}")
sys.exit(1 if bad else 0)
PYEOF
    then
        echo -e "${GREEN}✅ bank.jsonl is valid JSON Lines${NC}"
    else
        echo -e "${RED}❌ bank.jsonl has invalid lines${NC}"
        failed+=("bank.jsonl")
    fi
else
    echo -e "${GREEN}✅ No bank.jsonl yet (skipped)${NC}"
fi

# 3. Python helper scripts compile.
echo -e "${YELLOW}Compiling Python helper scripts…${NC}"
PY_LIST="$(find scripts -name '*.py' -print 2>/dev/null)"
if [ -n "$PY_LIST" ]; then
    OLD_IFS="$IFS"; IFS=$'\n'; set -f; set -- $PY_LIST; set +f; IFS="$OLD_IFS"
    if "$PY" -m py_compile "$@"; then
        echo -e "${GREEN}✅ Python scripts compile${NC}"
    else
        echo -e "${RED}❌ Python compile errors${NC}"
        failed+=("py-compile")
    fi
else
    echo -e "${GREEN}✅ No Python scripts to compile${NC}"
fi

echo "==============================================="
if [ "${#failed[@]}" -eq 0 ]; then
    echo -e "${GREEN}🎉 All quality checks PASSED${NC}"
    exit 0
else
    echo -e "${RED}💥 Failed checks:${NC}"
    for c in "${failed[@]}"; do
        echo -e "${RED}  - $c${NC}"
    done
    exit 1
fi

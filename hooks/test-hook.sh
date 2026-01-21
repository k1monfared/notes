#!/bin/bash
# Test script for the pre-commit movie enrichment hook
# Validates all components required for the hook to function properly

# Don't use set -e as we handle errors manually

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
HOOK_FILE="$SCRIPT_DIR/pre-commit"
GIT_HOOK_LINK="$REPO_ROOT/.git/hooks/pre-commit"
ENRICH_SCRIPT="/home/k1/public/imdb_helper/scripts/enrich_new_movies.py"
MOVIES_FILE="$REPO_ROOT/movies"

passed=0
failed=0
warnings=0

pass() {
    echo -e "${GREEN}[PASS]${NC} $1"
    passed=$((passed + 1))
}

fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    failed=$((failed + 1))
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    warnings=$((warnings + 1))
}

info() {
    echo -e "      $1"
}

echo "========================================"
echo "Pre-commit Hook Test Suite"
echo "========================================"
echo

# --- Hook File Checks ---
echo "--- Hook File Checks ---"

if [[ -f "$HOOK_FILE" ]]; then
    pass "Hook file exists at hooks/pre-commit"
else
    fail "Hook file missing at hooks/pre-commit"
fi

if [[ -x "$HOOK_FILE" ]]; then
    pass "Hook file is executable"
else
    fail "Hook file is not executable"
    info "Fix: chmod +x $HOOK_FILE"
fi

if bash -n "$HOOK_FILE" 2>/dev/null; then
    pass "Hook script has valid bash syntax"
else
    fail "Hook script has syntax errors"
    info "Run: bash -n $HOOK_FILE"
fi

echo

# --- Git Integration Checks ---
echo "--- Git Integration Checks ---"

if [[ -L "$GIT_HOOK_LINK" ]]; then
    pass "Git hook symlink exists"

    link_target=$(readlink "$GIT_HOOK_LINK")
    if [[ "$link_target" == "../../hooks/pre-commit" ]]; then
        pass "Symlink points to correct location"
    else
        fail "Symlink points to wrong location: $link_target"
        info "Expected: ../../hooks/pre-commit"
    fi
else
    fail "Git hook symlink missing at .git/hooks/pre-commit"
    info "Fix: ln -sf ../../hooks/pre-commit $GIT_HOOK_LINK"
fi

echo

# --- Enrich Script Checks ---
echo "--- Enrich Script Checks ---"

if [[ -f "$ENRICH_SCRIPT" ]]; then
    pass "Enrich script exists"
else
    fail "Enrich script missing at $ENRICH_SCRIPT"
fi

if [[ -r "$ENRICH_SCRIPT" ]]; then
    pass "Enrich script is readable"
else
    fail "Enrich script is not readable"
fi

# Check Python syntax
if python3 -m py_compile "$ENRICH_SCRIPT" 2>/dev/null; then
    pass "Enrich script has valid Python syntax"
else
    fail "Enrich script has Python syntax errors"
fi

echo

# --- Python Dependencies Checks ---
echo "--- Python Dependencies Checks ---"

if command -v python3 &>/dev/null; then
    pass "Python3 is available"
    info "Version: $(python3 --version 2>&1)"
else
    fail "Python3 is not available"
fi

# Check if the enrich_movies module exists (same dir as enrich script)
enrich_module="$(dirname "$ENRICH_SCRIPT")/enrich_movies.py"
if [[ -f "$enrich_module" ]]; then
    pass "enrich_movies.py module exists"
else
    fail "enrich_movies.py module missing at $enrich_module"
fi

# Check if enrich_movies.py has valid Python syntax
if python3 -m py_compile "$enrich_module" 2>/dev/null; then
    pass "enrich_movies.py has valid Python syntax"
else
    fail "enrich_movies.py has Python syntax errors"
fi

echo

# --- Movies File Checks ---
echo "--- Movies File Checks ---"

if [[ -f "$MOVIES_FILE" ]]; then
    pass "Movies file exists"
else
    fail "Movies file missing at $MOVIES_FILE"
fi

if [[ -r "$MOVIES_FILE" ]] && [[ -w "$MOVIES_FILE" ]]; then
    pass "Movies file is readable and writable"
else
    warn "Movies file may not have correct permissions"
fi

echo

# --- Dry Run Test ---
echo "--- Dry Run Test ---"

# Test the enrich script with --dry-run and --verbose (no actual changes)
dry_run_output=$(python3 "$ENRICH_SCRIPT" -f "$MOVIES_FILE" --dry-run --verbose 2>&1)
dry_run_exit=$?

if [[ $dry_run_exit -eq 0 ]]; then
    pass "Enrich script dry-run executes successfully"
    if [[ -n "$dry_run_output" ]]; then
        info "Output: $dry_run_output"
    fi
else
    fail "Enrich script dry-run failed with exit code $dry_run_exit"
    info "Output: $dry_run_output"
fi

echo

# --- Summary ---
echo "========================================"
echo "Summary"
echo "========================================"
echo -e "Passed:   ${GREEN}$passed${NC}"
echo -e "Failed:   ${RED}$failed${NC}"
echo -e "Warnings: ${YELLOW}$warnings${NC}"
echo

if [[ $failed -eq 0 ]]; then
    echo -e "${GREEN}All critical checks passed!${NC}"
    exit 0
else
    echo -e "${RED}Some checks failed. Please fix the issues above.${NC}"
    exit 1
fi

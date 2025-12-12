#!/bin/bash
# Quick linting check script for SquatchCut

echo "Running ruff linting checks..."

# Check and fix common issues
ruff check --fix freecad/SquatchCut/ tests/

# Show remaining issues
echo ""
echo "Remaining linting issues:"
ruff check freecad/SquatchCut/ tests/

exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo "✅ All linting checks passed!"
else
    echo "❌ Linting issues found. Please fix before committing."
fi

exit $exit_code

#!/usr/bin/env bash
# Non-blocking 30-second gate for regression-commit lookup after root cause confirmation.
# - No Git repo / commits -> DECISION=NO_GIT_HISTORY
# - Interactive TTY       -> 30s countdown prompt ([Y/n]); 'n'/'no' skips, Enter/'y'/timeout searches
# - Non-interactive/pipe  -> immediately returns DECISION=FIND_REGRESSION_COMMIT without blocking

set -euo pipefail

TIMEOUT_SECS="${REGRESSION_PROMPT_TIMEOUT:-30}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1 || ! git rev-parse --verify HEAD >/dev/null 2>&1; then
  echo "DECISION=NO_GIT_HISTORY"
  exit 0
fi

if [ "${SKIP_REGRESSION_COMMIT:-0}" = "1" ]; then
  echo "DECISION=SKIP_REGRESSION_COMMIT (env override)"
  exit 0
fi

if [ -t 0 ] && [ -t 1 ] && [ "${AUTO_REGRESSION_COMMIT:-0}" != "1" ]; then
  printf '\n[Regression Commit] Root cause identified. Locate the introducing regression commit? [Y/n] (default Y in %ss): ' "$TIMEOUT_SECS"
  reply=""
  if read -r -t "$TIMEOUT_SECS" reply; then
    case "$reply" in
      [nN]|[nN][oO])
        echo "DECISION=SKIP_REGRESSION_COMMIT (user declined)"
        exit 0
        ;;
      *)
        echo "DECISION=FIND_REGRESSION_COMMIT (user accepted)"
        exit 0
        ;;
    esac
  else
    printf '\n'
    echo "DECISION=FIND_REGRESSION_COMMIT (timeout ${TIMEOUT_SECS}s default)"
    exit 0
  fi
fi

echo "DECISION=FIND_REGRESSION_COMMIT (autonomous/non-interactive default)"

#!/usr/bin/env bash
# Retired full-suite launcher: passed CPU checks are retained by user instruction.
set -euo pipefail
printf '%s\n' 'The completed CPU checks must not be rerun. Use the remaining-CPU repair queue only after explicit resume authorization.' >&2
exit 64

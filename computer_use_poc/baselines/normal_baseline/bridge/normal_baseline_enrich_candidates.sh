#!/bin/bash
# normal_baseline_enrich_candidates.sh
# Agent bridge wrapper: L3 candidates → enriched_candidates
#
# Usage:
#   bash normal_baseline_enrich_candidates.sh <baseline_dir> <input_candidates_json> <output_enriched_json>
#
# Exit codes:
#   0  bridge_success
#   1  bridge_failed (baseline_dir_missing / invalid_candidate_input / enricher_execution_failed)

set -euo pipefail

# ---- Args ----
BASELINE_DIR="${1:?Usage: $0 <baseline_dir> <input_candidates_json> <output_enriched_json>}"
INPUT_CANDIDATES="${2:?Usage: $0 <baseline_dir> <input_candidates_json> <output_enriched_json>}"
OUTPUT_ENRICHED="${3:?Usage: $0 <baseline_dir> <input_candidates_json> <output_enriched_json>}"

# ---- Resolve script dir ----
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENRICHER_PY="${SCRIPT_DIR}/../src/normal_baseline_enricher.py"

# ---- Pre-flight checks ----

# 1. baseline_dir must exist
if [ ! -d "$BASELINE_DIR" ]; then
  echo "bridge_failed: baseline_dir_missing"
  echo "  baseline_dir: $BASELINE_DIR"
  echo "  L4 fallback: use original L3 candidates with caveat (no normal background)"
  exit 1
fi

# 2. Check baseline_dir contains required files
for f in normal_low_entropy_profile.json normal_discrete_field_distribution.json high_cardinality_summary.json profiler_metadata.json; do
  if [ ! -f "$BASELINE_DIR/$f" ]; then
    echo "bridge_failed: baseline_dir_incomplete"
    echo "  missing: $BASELINE_DIR/$f"
    echo "  L4 fallback: use original L3 candidates with caveat"
    exit 1
  fi
done

# 3. input_candidates must exist
if [ ! -f "$INPUT_CANDIDATES" ]; then
  echo "bridge_failed: invalid_candidate_input"
  echo "  input file not found: $INPUT_CANDIDATES"
  echo "  L4 fallback: use original L3 candidates with caveat"
  exit 1
fi

# 4. Validate input JSON
if ! python3 -m json.tool "$INPUT_CANDIDATES" > /dev/null 2>&1; then
  echo "bridge_failed: invalid_candidate_input"
  echo "  input file is not valid JSON: $INPUT_CANDIDATES"
  echo "  L4 fallback: use original L3 candidates with caveat"
  exit 1
fi

# ---- Execute enricher ----
echo "bridge_starting"
echo "  baseline_dir: $BASELINE_DIR"
echo "  input_candidates: $INPUT_CANDIDATES"
echo "  output_enriched: $OUTPUT_ENRICHED"

if ! python3 "$ENRICHER_PY" \
  --baseline-dir "$BASELINE_DIR" \
  --input-candidates "$INPUT_CANDIDATES" \
  --output "$OUTPUT_ENRICHED"; then
  echo "bridge_failed: enricher_execution_failed"
  echo "  L4 fallback: use original L3 candidates with caveat"
  exit 1
fi

# ---- Post-flight validation ----

# Check output exists and is valid JSON
if [ ! -f "$OUTPUT_ENRICHED" ]; then
  echo "bridge_failed: enricher_execution_failed"
  echo "  output file not created: $OUTPUT_ENRICHED"
  exit 1
fi

if ! python3 -m json.tool "$OUTPUT_ENRICHED" > /dev/null 2>&1; then
  echo "bridge_failed: enricher_execution_failed"
  echo "  output file is not valid JSON: $OUTPUT_ENRICHED"
  exit 1
fi

# ---- Summary ----
CANDIDATE_COUNT=$(python3 -c "import json; print(len(json.load(open('$OUTPUT_ENRICHED'))['enriched_candidates']))" 2>/dev/null || echo "?")
HIT_COUNT=$(python3 -c "import json; m=json.load(open('$OUTPUT_ENRICHED'))['enrichment_metadata']; print(m['baseline_hit_count'])" 2>/dev/null || echo "?")
MISS_COUNT=$(python3 -c "import json; m=json.load(open('$OUTPUT_ENRICHED'))['enrichment_metadata']; print(m['baseline_miss_count'])" 2>/dev/null || echo "?")
HC_COUNT=$(python3 -c "import json; m=json.load(open('$OUTPUT_ENRICHED'))['enrichment_metadata']; print(m['high_cardinality_count'])" 2>/dev/null || echo "?")

echo ""
echo "bridge_success"
echo "  candidates: $CANDIDATE_COUNT"
echo "  baseline_hit: $HIT_COUNT"
echo "  baseline_miss: $MISS_COUNT"
echo "  high_cardinality: $HC_COUNT"
echo "  output: $OUTPUT_ENRICHED"
exit 0

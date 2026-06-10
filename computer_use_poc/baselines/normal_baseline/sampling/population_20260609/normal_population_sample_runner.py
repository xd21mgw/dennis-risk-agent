#!/usr/bin/env python3
"""
normal_population_sample_runner.py v0.1

Population baseline 抽样 runner：
1. 尝试通过 DataAgent/Hive 抽取正式样本（deterministic hash sample）
2. 如果无法访问真实平台，标记 dataagent_unavailable 并使用本地 Excel 样例作为 demo
3. 导出样本文件到指定目录
4. 运行 normal_baseline_profiler.py 生成正式 population baseline 统计结果

DataAgent 边界：只取数不分析

口径：population_baseline / 大盘背景 baseline
不是 LOGIN_AUE 精准 normal baseline
"""

import argparse
import json
import os
import sys
import subprocess

# Resolve paths relative to the normal_baseline root directory
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_NORMAL_BASELINE_ROOT = os.path.normpath(os.path.join(_SCRIPT_DIR, "..", ".."))

INPUT_EXCEL_DIR = os.path.join(_NORMAL_BASELINE_ROOT, "input_excels")
CONTRACT_PATH = os.path.join(_NORMAL_BASELINE_ROOT, "recon",
    "profiler_input_contract_20260609_v0_1.yaml")
BATCH_YAML_PATH = os.path.join(_NORMAL_BASELINE_ROOT, "sample_batches",
    "normal_population_batch_20260609_v0_1.yaml")
PROFILER_SCRIPT = os.path.join(_NORMAL_BASELINE_ROOT, "src", "normal_baseline_profiler.py")

SAMPLE_STATUS_FILE = "dataagent_sample_status.json"

# DataAgent/Hive unavailable by default in local development environment
DATAGENT_AVAILABLE = False  # Cannot access real platform from local env


def check_dataagent_availability():
    """Check if DataAgent/Hive is accessible."""
    # In local development environment, we cannot access real platform
    # This should be set to True when running in an environment with
    # DataAgent/Hive connectivity
    return DATAGENT_AVAILABLE


def extract_samples_via_dataagent(output_dir, batch_yaml_path):
    """Extract samples via DataAgent/Hive using deterministic hash sample.

    This function would connect to DataAgent/Hive and execute the SQL
    templates defined in the batch YAML. Since we cannot access real
    platforms in local development, this returns a status indicating
    dataagent_unavailable.
    """
    # This is a placeholder for the actual DataAgent execution
    # In production, this would:
    # 1. Read the batch YAML to get table names and conditions
    # 2. Execute the SQL templates via DataAgent/Hive
    # 3. Export the results to the output directory

    return {
        "dataagent_available": False,
        "reason": "Cannot access real DataAgent/Hive platform from local development environment",
        "action_required": "Run this script in an environment with DataAgent/Hive connectivity, "
                          "or use --fallback-excel to demo with local Excel samples",
        "sample_status": "dataagent_unavailable",
        "sources": {
            "infra_user_action_log": {
                "target_count": 3000,
                "actual_count": None,
                "status": "not_extracted",
            },
            "passport_action_log": {
                "target_count": 3000,
                "actual_count": None,
                "status": "not_extracted",
            },
            "weapon_android": {
                "target_count": 3000,
                "actual_count": None,
                "status": "not_extracted",
            },
            "weapon_ios": {
                "target_count": 3000,
                "actual_count": None,
                "status": "not_extracted",
            },
        },
    }


def extract_samples_via_excel_fallback(output_dir):
    """Use existing local Excel files as fallback demo samples.

    This is NOT the primary path for population baseline.
    It is only used when DataAgent is unavailable.
    The Excel samples have ~1000 rows per source, which is below
    the 3000 sample threshold for low_entropy_rule.
    """
    sample_status = {
        "dataagent_available": False,
        "fallback_method": "local_excel_demo",
        "fallback_note": "Using existing Excel samples (~1000 rows each) as demo. "
                        "Not meeting 3000 sample threshold for low_entropy_rule.",
        "sample_status": "fallback_excel_demo",
        "baseline_scope": "population_baseline",
        "not_login_aue_specific": True,
        "sources": {
            "infra_user_action_log": {
                "target_count": 3000,
                "actual_count": None,
                "status": "fallback_excel",
                "note": "Excel ~1000 rows, below 3000 threshold",
            },
            "passport_action_log": {
                "target_count": 3000,
                "actual_count": None,
                "status": "fallback_excel",
                "note": "Excel ~1000 rows, below 3000 threshold",
            },
            "weapon_android": {
                "target_count": 3000,
                "actual_count": None,
                "status": "fallback_excel",
                "note": "Excel ~1000 rows, below 3000 threshold",
            },
            "weapon_ios": {
                "target_count": 3000,
                "actual_count": None,
                "status": "fallback_excel",
                "note": "Excel ~1000 rows, below 3000 threshold",
            },
        },
    }

    # Write sample status
    status_path = os.path.join(output_dir, SAMPLE_STATUS_FILE)
    with open(status_path, "w") as f:
        json.dump(sample_status, f, ensure_ascii=False, indent=2)
    print(f"  Written sample status: {status_path}")

    return sample_status


def run_profiler(input_dir, contract_path, output_dir, topn_limit=20):
    """Run normal_baseline_profiler.py on the extracted samples."""
    cmd = [
        sys.executable, PROFILER_SCRIPT,
        "--input-dir", input_dir,
        "--contract", contract_path,
        "--output-dir", output_dir,
        "--topn-limit", str(topn_limit),
    ]

    print(f"\n  Running profiler: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"  Profiler FAILED!")
        print(f"  stdout: {result.stdout[:500]}")
        print(f"  stderr: {result.stderr[:500]}")
        return None

    print(f"  Profiler completed successfully")
    # Read metadata
    metadata_path = os.path.join(output_dir, "profiler_metadata.json")
    if os.path.exists(metadata_path):
        with open(metadata_path) as f:
            metadata = json.load(f)
        return metadata
    return None


def main():
    parser = argparse.ArgumentParser(
        description="normal_baseline population sample runner v0.1"
    )
    parser.add_argument("--output-dir", required=True,
                        help="Output directory for samples and profiler results")
    parser.add_argument("--fallback-excel", action="store_true",
                        help="Use local Excel samples as fallback demo "
                             "(when DataAgent is unavailable)")
    parser.add_argument("--topn-limit", type=int, default=20,
                        help="TOP-N limit for profiler (default: 20)")
    parser.add_argument("--batch-yaml", default=BATCH_YAML_PATH,
                        help="Path to population batch YAML")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    print(f"normal_baseline population sample runner v0.1")
    print(f"  output_dir: {args.output_dir}")
    print(f"  batch_yaml: {args.batch_yaml}")
    print(f"  fallback_excel: {args.fallback_excel}")

    # Step 1: Check DataAgent availability
    dataagent_available = check_dataagent_availability()
    print(f"\n  DataAgent available: {dataagent_available}")

    if dataagent_available:
        print(f"\n  Step 1: Extracting samples via DataAgent...")
        sample_status = extract_samples_via_dataagent(
            args.output_dir, args.batch_yaml
        )
    elif args.fallback_excel:
        print(f"\n  Step 1: DataAgent unavailable. Using local Excel fallback...")
        sample_status = extract_samples_via_excel_fallback(args.output_dir)
    else:
        print(f"\n  Step 1: DataAgent unavailable and --fallback-excel not specified.")
        print(f"  Cannot extract samples. Please:")
        print(f"    1. Run in an environment with DataAgent/Hive connectivity")
        print(f"    2. Or use --fallback-excel for local demo")
        # Write status
        status = {
            "dataagent_available": False,
            "fallback_excel": False,
            "sample_status": "unavailable",
            "action_required": "Use --fallback-excel or run in DataAgent environment",
        }
        status_path = os.path.join(args.output_dir, SAMPLE_STATUS_FILE)
        with open(status_path, "w") as f:
            json.dump(status, f, ensure_ascii=False, indent=2)
        sys.exit(1)

    # Step 2: Run profiler
    if sample_status.get("fallback_method") == "local_excel_demo":
        input_dir = INPUT_EXCEL_DIR
        contract_path = CONTRACT_PATH
    else:
        # In production, input_dir would point to the DataAgent export directory
        input_dir = args.output_dir
        contract_path = CONTRACT_PATH

    print(f"\n  Step 2: Running profiler...")
    print(f"    input_dir: {input_dir}")
    print(f"    contract_path: {contract_path}")

    metadata = run_profiler(input_dir, contract_path, args.output_dir, args.topn_limit)

    if metadata is None:
        print(f"\n  Profiler failed. Check output directory for errors.")
        sys.exit(1)

    # Step 3: Print summary
    print(f"\n  === Population Baseline Summary ===")
    print(f"  baseline_scope: {metadata.get('baseline_scope')}")
    print(f"  not_login_aue_specific: {metadata.get('not_login_aue_specific')}")
    print(f"  total_fields_discovered: {metadata.get('total_fields_discovered')}")
    print(f"  total_fields_profiled: {metadata.get('total_fields_profiled')}")

    # Low entropy summary
    low_entropy_status_dist = {}
    le_path = os.path.join(args.output_dir, "normal_low_entropy_profile.json")
    if os.path.exists(le_path):
        with open(le_path) as f:
            le_profiles = json.load(f)
        for e in le_profiles:
            s = e["normal_status"]
            low_entropy_status_dist[s] = low_entropy_status_dist.get(s, 0) + 1
    print(f"  low_entropy_status_distribution: {low_entropy_status_dist}")

    # Sample size check
    for sid, result in metadata.get("source_results", {}).items():
        rows = result.get("rows", 0)
        meets_threshold = rows >= 3000
        print(f"  {sid}: {rows} rows, meets_3000_threshold: {meets_threshold}")

    # Sample status summary
    print(f"\n  sample_status: {sample_status.get('sample_status')}")
    if sample_status.get("fallback_method"):
        print(f"  fallback_method: {sample_status.get('fallback_method')}")
        print(f"  NOTE: Current Excel samples (~1000 rows) are below 3000 threshold.")
        print(f"  Low_entropy_profile will show normal_unknown_small_sample for most fields.")
        print(f"  To get real population baseline, extract 3000+ rows via DataAgent/Hive.")

    print(f"\n  Output directory: {args.output_dir}")
    print(f"  Files:")
    for f in sorted(os.listdir(args.output_dir)):
        if f.endswith(".json"):
            print(f"    {f}")


if __name__ == "__main__":
    main()
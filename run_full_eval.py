"""
run_full_eval.py — Single-process, sequential generation + judging.
No concurrency, no race conditions on terra_generations.json.
"""
import json
import time
import sys
from eval_terra import run_generation_only, run_judging_only

GEN_FILE = "terra_generations.json"
JUDGE_FILE = "terra_eval_raw.json"
TARGET = 105

def check_count():
    try:
        with open(GEN_FILE, 'r', encoding='utf-8') as f:
            d = json.load(f)
        return len(d)
    except Exception:
        return 0

print("=" * 70)
print("=== TERRA FULL EVAL: GENERATION + JUDGING (single process) ===")
print("=" * 70)

# --- PHASE 1: Generation ---
while True:
    count = check_count()
    print(f"\n[GEN STATUS] {count}/{TARGET} records on disk.")
    if count >= TARGET:
        print("[GEN COMPLETE] 105 records confirmed.")
        break
    print("[GEN] Calling run_generation_only(resume=True)...")
    try:
        run_generation_only(resume=True)
    except Exception as e:
        print(f"[GEN ERROR] {e} — sleeping 5s then retrying...")
        time.sleep(5)

# Final count verification
final_count = check_count()
print(f"\n[VERIFY] terra_generations.json has {final_count} records.")
if final_count < TARGET:
    print(f"[STOP CONDITION] Expected {TARGET}, got {final_count}. Aborting.")
    sys.exit(1)

# --- PHASE 2: Judging ---
print("\n[JUDGING] Starting full judging pass (resume=False)...")
try:
    run_judging_only(resume=False)
except Exception as e:
    print(f"[JUDGE ERROR] {e}")
    sys.exit(1)

# --- PHASE 3: Audit ---
print("\n[AUDIT] Verifying judged record coverage...")
with open(GEN_FILE) as f:
    gens = json.load(f)
with open(JUDGE_FILE) as f:
    judged = json.load(f)

gen_keys = set((r['query_id'], r['pipeline']) for r in gens)
judged_keys = set((r['query_id'], r['pipeline']) for r in judged)
missing = gen_keys - judged_keys
null_f = [r for r in judged if r.get('faithfulness') is None]
null_r = [r for r in judged if r.get('relevance') is None]

print(f"  Generations: {len(gens)} | Judged: {len(judged)}")
print(f"  Missing from judged: {len(missing)}")
print(f"  Null faithfulness: {len(null_f)} | Null relevance: {len(null_r)}")

if missing:
    print(f"[AUDIT FAIL] Missing records: {missing}")
    sys.exit(1)
if null_f or null_r:
    print(f"[AUDIT WARN] Some scores are None — check judge errors.")
else:
    print("[AUDIT PASS] All 105 records judged with no null scores.")

print("\n[ALL PHASES COMPLETE] Run: python eval_terra.py --recompile to generate report.")

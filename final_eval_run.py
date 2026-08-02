"""
final_eval_run.py — One-shot, synchronous, no background tasks.
Generates → Judges → Audits → Writes report.
Uses a unique output filename to avoid conflicts.
"""
import json, os, sys, time, statistics, collections
import pandas as pd
from tabulate import tabulate

GEN_FILE = "terra_generations.json"
RAW_FILE = "terra_eval_raw_v19_final.json"   # unique name to avoid clobber
REPORT_FILE = "terra_evaluation_report.md"
TARGET = 105

# ── PHASE 1: Generation ─────────────────────────────────────────────────────
from eval_terra import run_generation_only, run_judging_only, CATEGORY_A, CATEGORY_B

def count_gens():
    try:
        with open(GEN_FILE, 'r', encoding='utf-8') as f:
            return len(json.load(f))
    except Exception:
        return 0

print("=" * 70)
print("=== FINAL EVAL RUN — SINGLE PROCESS, NO CONCURRENCY ===")
print("=" * 70)

while count_gens() < TARGET:
    n = count_gens()
    print(f"\n[GEN] {n}/{TARGET} on disk — running generation pass...")
    try:
        run_generation_only(resume=True)
    except Exception as e:
        print(f"[GEN ERROR] {e} — sleeping 5s...")
        time.sleep(5)

n = count_gens()
print(f"\n[GEN DONE] {n}/{TARGET} records confirmed.")
if n < TARGET:
    print(f"[STOP] Could not reach {TARGET}. Exiting.")
    sys.exit(1)

# ── PHASE 2: Judging → RAW_FILE ──────────────────────────────────────────────
print(f"\n[JUDGING] Writing to {RAW_FILE}...")
run_judging_only(resume=False, raw_output=RAW_FILE)

# ── PHASE 3: Audit ───────────────────────────────────────────────────────────
with open(GEN_FILE) as f:
    gens = json.load(f)
with open(RAW_FILE) as f:
    judged = json.load(f)

gen_keys = set((r['query_id'], r['pipeline']) for r in gens)
judged_keys = set((r['query_id'], r['pipeline']) for r in judged)
missing = gen_keys - judged_keys
null_f = [r for r in judged if r.get('faithfulness') is None]

print(f"\n[AUDIT] Gens={len(gens)} | Judged={len(judged)} | Missing={len(missing)} | NullF={len(null_f)}")
if missing:
    print(f"[AUDIT FAIL] Missing: {missing}")
    sys.exit(1)
print("[AUDIT PASS]")

# Copy to canonical name so --recompile works
import shutil
shutil.copy(RAW_FILE, "terra_eval_raw.json")
print(f"[COPY] {RAW_FILE} -> terra_eval_raw.json")

# ── PHASE 4: Report ──────────────────────────────────────────────────────────
df = pd.DataFrame(judged)
pipeline_summary = []
for pipeline in ["1_Direct_LLM", "2_Flat_RAG", "3_TERRA_GraphRAG"]:
    p_df = df[df["pipeline"] == pipeline]
    ab_df = p_df[p_df["category"].isin(["A_Factual", "B_Evolutionary"])]
    cd_df = p_df[p_df["category"].isin(["C_OutOfContext", "D_Adversarial"])]
    faith_vals = p_df["faithfulness"].dropna().tolist()
    rel_vals   = p_df["relevance"].dropna().tolist()
    rouge_vals = ab_df["rouge_l"].dropna().tolist()
    rejected   = cd_df["safety_rejected"].sum()
    total_cd   = len(cd_df)
    latency_vals = [r["timing"].get("total_ms", 0) for r in judged
                    if r["pipeline"] == pipeline and isinstance(r.get("timing"), dict) and r["timing"].get("total_ms", 0) > 0]
    pipeline_summary.append({
        "Pipeline": pipeline.replace("_", " "),
        "Faithfulness (mean)": f"{statistics.mean(faith_vals):.3f}" if faith_vals else "N/A",
        "Faithfulness (±SD)":  f"±{statistics.stdev(faith_vals):.3f}" if len(faith_vals) > 1 else "N/A",
        "Relevance (mean)":    f"{statistics.mean(rel_vals):.3f}" if rel_vals else "N/A",
        "Relevance (±SD)":     f"±{statistics.stdev(rel_vals):.3f}" if len(rel_vals) > 1 else "N/A",
        "ROUGE-L (mean)":      f"{statistics.mean(rouge_vals):.3f}" if rouge_vals else "N/A",
        "Safety Rejected":     f"{int(rejected)}/{total_cd}",
        "Latency (mean ms)":   f"{statistics.mean(latency_vals):.0f}" if latency_vals else "N/A",
    })
summary_df = pd.DataFrame(pipeline_summary)

cat_summary = []
for cat in ["A_Factual", "B_Evolutionary", "C_OutOfContext", "D_Adversarial"]:
    c_df = df[df["category"] == cat]
    for pipeline in ["1_Direct_LLM", "2_Flat_RAG", "3_TERRA_GraphRAG"]:
        pc_df = c_df[c_df["pipeline"] == pipeline]
        faith_vals = pc_df["faithfulness"].dropna().tolist()
        rouge_vals = pc_df["rouge_l"].dropna().tolist()
        rejected   = pc_df["safety_rejected"].sum()
        cat_summary.append({
            "Category": cat, "Pipeline": pipeline.replace("_", " "), "n": len(pc_df),
            "Faithfulness": f"{statistics.mean(faith_vals):.3f}" if faith_vals else "N/A",
            "ROUGE-L": f"{statistics.mean(rouge_vals):.3f}" if rouge_vals else "N/A",
            "Safety Rejections": int(rejected),
        })
cat_df = pd.DataFrame(cat_summary)

latency_rows = []
for pipeline in ["1_Direct_LLM", "2_Flat_RAG", "3_TERRA_GraphRAG"]:
    timings = [r["timing"] for r in judged if r["pipeline"] == pipeline and isinstance(r.get("timing"), dict)]
    if timings:
        def avg(vals): return statistics.mean(vals) if vals else 0
        def sd(vals): return statistics.stdev(vals) if len(vals) > 1 else 0
        r_vals  = [t.get("routing_ms", 0) for t in timings]
        ret_vals= [t.get("retrieval_ms", 0) for t in timings]
        g_vals  = [t.get("grading_ms", 0) for t in timings]
        gen_vals= [t.get("generation_ms", 0) for t in timings]
        tot_vals= [t.get("total_ms", 0) for t in timings]
        latency_rows.append({
            "Pipeline": pipeline.replace("_", " "),
            "Routing (ms)":    f"{avg(r_vals):.0f} ±{sd(r_vals):.0f}",
            "Retrieval (ms)":  f"{avg(ret_vals):.0f} ±{sd(ret_vals):.0f}",
            "Grading (ms)":    f"{avg(g_vals):.0f} ±{sd(g_vals):.0f}",
            "Generation (ms)": f"{avg(gen_vals):.0f} ±{sd(gen_vals):.0f}",
            "Total (ms)":      f"{avg(tot_vals):.0f} ±{sd(tot_vals):.0f}",
        })
latency_df = pd.DataFrame(latency_rows)

# Wilcoxon
wilcoxon_rows = []
try:
    from scipy.stats import wilcoxon
    ab_qids = {q["id"] for q in CATEGORY_A + CATEGORY_B}
    df_ab = df[df["query_id"].isin(ab_qids)]
    def get_scores(pipeline, metric):
        return df_ab[df_ab["pipeline"] == pipeline][metric].dropna().tolist()
    for metric, label in [("faithfulness", "Faithfulness"), ("rouge_l", "ROUGE-L")]:
        terra = get_scores("3_TERRA_GraphRAG", metric)
        flat  = get_scores("2_Flat_RAG", metric)
        direct= get_scores("1_Direct_LLM", metric)
        for cname, cscores in [("Flat RAG", flat), ("Direct LLM", direct)]:
            n = min(len(terra), len(cscores))
            if n >= 5:
                t2, c2 = terra[:n], cscores[:n]
                if sum(abs(a-b) for a,b in zip(t2, c2)) > 0:
                    stat, p = wilcoxon(t2, c2, alternative="two-sided")
                    wilcoxon_rows.append({"Metric": label, "Comparison": f"TERRA vs {cname}",
                                          "n": n, "Wilcoxon stat": f"{stat:.2f}",
                                          "p-value": f"{p:.4f}",
                                          "Significant (p<0.05)": "Yes" if p < 0.05 else "No"})
                    print(f"  {label}: TERRA vs {cname} — p={p:.4f}")
                else:
                    wilcoxon_rows.append({"Metric": label, "Comparison": f"TERRA vs {cname}",
                                          "n": n, "Wilcoxon stat": "N/A",
                                          "p-value": "N/A (identical)", "Significant (p<0.05)": "N/A"})
except Exception as e:
    print(f"[WILCOXON ERROR] {e}")
wilcoxon_df = pd.DataFrame(wilcoxon_rows) if wilcoxon_rows else pd.DataFrame()

print("\n=== OVERALL PIPELINE SUMMARY ===")
print(tabulate(summary_df, headers='keys', tablefmt='github', showindex=False))
print("\n=== PER-CATEGORY BREAKDOWN ===")
print(tabulate(cat_df, headers='keys', tablefmt='github', showindex=False))
print("\n=== LATENCY BREAKDOWN ===")
print(tabulate(latency_df, headers='keys', tablefmt='github', showindex=False))

with open(REPORT_FILE, "w", encoding="utf-8") as f:
    # Compute model provenance from actual per-record data (v22 Step 22.2 fix)
    from collections import Counter
    judge_counts = Counter(r.get("judge_model_used") for r in judged if r.get("judge_model_used"))
    gen_counts   = Counter(r.get("generation_model_used") for r in judged if r.get("generation_model_used"))
    judge_str = ", ".join(f"{m} ({c})" for m, c in judge_counts.most_common())
    gen_str   = ", ".join(f"{m} ({c})" for m, c in gen_counts.most_common())

    f.write("# TERRA GraphRAG -- Comparative Evaluation Report (v3)\n\n")
    f.write("Benchmark: 35 queries across 4 categories (A=Factual, B=Evolutionary, "
            "C=OutOfContext, D=Adversarial), 3 pipelines. "
            "Metrics: Faithfulness, Relevance (LLM-as-critic judge on 1-5 scale), "
            "ROUGE-L (LLM-independent, A+B only), Safety Rejection Rate (C+D), "
            "and per-stage latency.\n\n")
    f.write(f"**Judge model(s) used**: {judge_str}. "
            f"**Generation model(s) used**: {gen_str}. "
            f"**Total records**: {len(judged)} (35 queries x 3 pipelines).\n\n")
    f.write("## Overall Pipeline Summary\n\n")
    f.write(tabulate(summary_df, headers='keys', tablefmt='github', showindex=False))
    f.write("\n\n## Per-Category Breakdown\n\n")
    f.write(tabulate(cat_df, headers='keys', tablefmt='github', showindex=False))
    f.write("\n\n## Latency Breakdown (mean +-SD, milliseconds)\n\n")
    f.write(tabulate(latency_df, headers='keys', tablefmt='github', showindex=False))
    f.write("\n\n")
    if not wilcoxon_df.empty:
        f.write("## Statistical Significance (Wilcoxon Signed-Rank, Categories A+B)\n\n")
        f.write(tabulate(wilcoxon_df, headers='keys', tablefmt='github', showindex=False))
        f.write("\n\n")
    f.write("## Notes on Evaluation Methodology\n\n")
    f.write("- **LLM Judge**: Uses a sceptical critic persona "
            "on a 1-5 scale (5=best) to reduce self-consistency bias.\n")
    f.write("- **ROUGE-L**: LLM-independent metric computed against human-written reference "
            "answers for Categories A (Factual) and B (Evolutionary).\n")
    f.write("- **Safety Rejection**: Categories C (Out-of-Context, 10 queries) and "
            "D (Adversarial, 5 queries). D queries use real in-domain case names "
            "but ask unrelated questions.\n")
    f.write("- **Faithfulness scale**: 1 = completely hallucinated, 5 = fully grounded in context.\n")
    f.write(f"- **Generation model(s)**: {gen_str}. "
            "None entries = safety-refused responses with no generation call.\n")

print(f"\n[REPORT] Saved to {REPORT_FILE}")
print("\n=== ALL DONE ===")

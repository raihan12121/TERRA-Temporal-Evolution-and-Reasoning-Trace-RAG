"""
Step 23.9 — Run B03, B07, B08, B09 (actual v19 B-rejections) through the real
terra_inference_engine using real imports. Report context size, whether it includes
real case text, entailment result, and final answer vs. refusal.
"""
import os, sys, importlib
os.environ['PYTHONUTF8'] = '1'
from dotenv import load_dotenv
load_dotenv()

# Force fresh reload so v23 fixes are live
import ask_terra
importlib.reload(ask_terra)
from ask_terra import terra_inference_engine, extract_graph_context, smart_grader, collection, eeg

# The 4 queries that were safety-rejected in v19
QUERIES = {
    "B03": "How did graduate school desegregation cases influence the Brown ruling?",
    "B07": "How did Cooper v. Aaron reinforce Brown v. Board of Education?",
    "B08": "What role did Sweatt v. Painter play in limiting the separate but equal doctrine?",
    "B09": "How did the Slaughterhouse Cases and Civil Rights Cases together shape the limits of the Fourteenth Amendment?",
}

print("=" * 70)
print("Step 23.9 — B03/B07/B08/B09 validation against v23 fixes")
print("=" * 70)

for qid, query in QUERIES.items():
    print(f"\n{'='*60}")
    print(f"[{qid}] {query[:80]}...")
    print(f"{'='*60}")

    # Step A: manually run retrieval + extract_graph_context so we can inspect
    results = collection.query(query_texts=[query], n_results=2)
    metadatas = results['metadatas'][0]
    traces    = results['documents'][0]
    print(f"  Retrieved case IDs: {[m.get('case_id') for m in metadatas]}")

    ctx = extract_graph_context(metadatas, max_depth=2)
    traces_ctx = "\n".join([f"- {t}" for t in traces])
    full_ctx = f"{ctx}\n{traces_ctx}"

    has_text = '[Case Summary/Text]:' in ctx
    print(f"  Context size (chars): {len(full_ctx)}")
    print(f"  Context includes real node text: {has_text}")
    if has_text:
        # Show first snippet of text found
        idx = ctx.find('[Case Summary/Text]:')
        print(f"  Sample text: {ctx[idx:idx+200]}")

    # Step B: call smart_grader directly to see entailment result
    print(f"\n  [Smart Grader check on live context...]")
    entails = smart_grader(query, full_ctx)
    print(f"  smart_grader returned: {entails}")

    # Step C: run full terra_inference_engine
    print(f"\n  [Running full terra_inference_engine...]")
    ans, ctx_out, timing = terra_inference_engine(query, return_timing=True)
    gen_model = timing.get('_generation_model_used', 'N/A')
    is_refusal = 'cannot' in ans.lower()[:100] or 'outside' in ans.lower()[:100] or "don't have" in ans.lower()[:100]
    print(f"  gen_model: {gen_model}")
    print(f"  Answer (first 200 chars): {ans[:200]}")
    print(f"  Safety refusal: {is_refusal}")

print("\n=== Step 23.9 COMPLETE ===")

import os
import sys
import json
import time
import networkx as nx
import chromadb
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("PHASE 2 — FULL SYSTEM RECHECK")
print("=" * 60)

from ask_terra import (
    terra_inference_engine, collection, eeg,
    openai_client, generate_content_with_retry_openai
)
from eval_terra import (
    direct_llm_inference, flat_rag_inference, judge_answer, judge_client
)

# Step 19.1 — Consolidated Cross-Pipeline Test
query_19_1 = "How did the Supreme Court's stance on racial segregation evolve from Plessy to Brown?"
print(f"\n--- STEP 19.1: Cross-Pipeline Test on Query: '{query_19_1}' ---")

pipelines = [
    ("1_Direct_LLM", direct_llm_inference),
    ("2_Flat_RAG", flat_rag_inference),
    ("3_TERRA_GraphRAG", lambda q: terra_inference_engine(q, return_timing=True))
]

p1_results = {}

for pname, pfn in pipelines:
    print(f"\n[Running Pipeline]: {pname}")
    t0 = time.time()
    res = pfn(query_19_1)
    if len(res) == 3:
        ans, ctx, timing = res
    else:
        ans, ctx = res
        timing = {}
        
    is_direct = (pname == "1_Direct_LLM") or not ctx.strip()
    judge_res = judge_answer(query_19_1, ctx, ans, is_direct_llm=is_direct)
    
    p1_results[pname] = {
        "gen_model": timing.get("_generation_model_used"),
        "ctx_size": len(ctx),
        "judge_model": judge_res.get("_judge_model_used"),
        "judge_faithfulness": judge_res.get("faithfulness_score"),
        "judge_relevance": judge_res.get("relevance_score"),
        "retry_sleep_ms_gen": timing.get("_retry_sleep_ms"),
        "total_ms": timing.get("total_ms")
    }
    
    print(f"  Generation Model Used: {timing.get('_generation_model_used')}")
    print(f"  Context Size: {len(ctx)} chars")
    print(f"  Judge Model Used: {judge_res.get('_judge_model_used')}")
    print(f"  Faithfulness: {judge_res.get('faithfulness_score')} | Relevance: {judge_res.get('relevance_score')}")
    print(f"  Retry Sleep MS (Gen): {timing.get('_retry_sleep_ms')}")

# Step 19.2 — Corpus Integrity Spot-Check
print("\n--- STEP 19.2: Corpus Integrity Spot-Check ---")
node_count = eeg.number_of_nodes()
edge_count = eeg.number_of_edges()

# Check nodes truncated at 500 chars
truncated_500_count = sum(
    1 for n in eeg.nodes
    if len(eeg.nodes[n].get("text", "")) == 500
)

chroma_doc_count = collection.count()

print(f"  terra_eeg_index.json Node Count: {node_count}")
print(f"  terra_eeg_index.json Edge Count: {edge_count}")
print(f"  Nodes truncated at exactly 500 chars: {truncated_500_count}")
print(f"  ChromaDB thinking_traces Document Count: {chroma_doc_count}")

print("\n" + "=" * 60)
print("PHASE 2 TEST COMPLETE")
print("=" * 60)

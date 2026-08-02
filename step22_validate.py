"""
Step 22.8 — Single-query, all-pipeline validation.
Uses B01 (HARD-routing, multi-hop evolutionary) as the test query.
Confirms: generation stays Groq-only, judge stays Gemini-only,
no cross-provider contamination.
"""
import os, json, time
os.environ['PYTHONUTF8'] = '1'
from dotenv import load_dotenv
load_dotenv()

from ask_terra import (
    terra_inference_engine, collection,
    generate_content_with_retry_openai, openai_client
)
from eval_terra import (
    direct_llm_inference, flat_rag_inference,
    judge_answer, compute_rouge_l, REFERENCE_ANSWERS, CATEGORY_B
)

QUERY = "How did the Supreme Court's stance on racial segregation change from Plessy v. Ferguson to Brown v. Board of Education?"
QID = "B01"
reference = REFERENCE_ANSWERS.get(QID)

print("=" * 70)
print(f"Step 22.8 Validation Query: {QID}")
print(f"Query: {QUERY[:80]}...")
print("=" * 70)

results = {}

# Pipeline 1: Direct LLM
print("\n[Pipeline 1] Direct LLM...")
ans1, ctx1, tim1 = direct_llm_inference(QUERY)
gen_model_1 = tim1.get("_generation_model_used")
print(f"  gen_model_used: {gen_model_1}")
print(f"  answer[:120]: {ans1[:120]}")
results["1_Direct_LLM"] = {"ans": ans1, "ctx": ctx1, "timing": tim1, "gen_model": gen_model_1}

# Pipeline 2: Flat RAG
print("\n[Pipeline 2] Flat RAG...")
ans2, ctx2, tim2 = flat_rag_inference(QUERY)
gen_model_2 = tim2.get("_generation_model_used")
print(f"  gen_model_used: {gen_model_2}")
print(f"  answer[:120]: {ans2[:120]}")
results["2_Flat_RAG"] = {"ans": ans2, "ctx": ctx2, "timing": tim2, "gen_model": gen_model_2}

# Pipeline 3: TERRA GraphRAG
print("\n[Pipeline 3] TERRA GraphRAG...")
ans3, ctx3, tim3 = terra_inference_engine(QUERY, return_timing=True)
gen_model_3 = tim3.get("_generation_model_used")
print(f"  gen_model_used: {gen_model_3}")
print(f"  answer[:120]: {ans3[:120]}")
print(f"  context snippet[:300]: {ctx3[:300]}")
results["3_TERRA_GraphRAG"] = {"ans": ans3, "ctx": ctx3, "timing": tim3, "gen_model": gen_model_3}

# Judge all three
print("\n[Judging all 3 pipelines...]")
for pipe_name, data in results.items():
    is_direct = (pipe_name == "1_Direct_LLM") or not data["ctx"].strip()
    scores = judge_answer(QUERY, data["ctx"], data["ans"], is_direct_llm=is_direct)
    judge_model = scores.get("_judge_model_used")
    rouge = compute_rouge_l(data["ans"], reference)
    print(f"\n  {pipe_name}:")
    print(f"    judge_model: {judge_model}")
    print(f"    faithfulness: {scores.get('faithfulness_score')}")
    print(f"    relevance: {scores.get('relevance_score')}")
    print(f"    rouge_l: {rouge}")
    # Check contamination
    gen_m = data["gen_model"] or ""
    if any(x in gen_m for x in ["gemma", "gemini"]):
        print(f"    !! CONTAMINATION ALERT: generation used Gemini-family model: {gen_m}")
    else:
        print(f"    gen_model check: OK (Groq or None/safety-refused)")
    if judge_model and any(x in str(judge_model) for x in ["llama", "groq"]):
        print(f"    !! CONTAMINATION ALERT: judge used Groq-family model: {judge_model}")
    else:
        print(f"    judge_model check: OK (Gemini-family or None)")
    time.sleep(1)

print("\n=== Step 22.8 COMPLETE ===")

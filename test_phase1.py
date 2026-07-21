import os
import sys
import json
import time
from dotenv import load_dotenv

load_dotenv()

print("=" * 60)
print("PHASE 1 RE-VALIDATION")
print("=" * 60)

# Item 1: Key Presence Confirmation
print("\n--- ITEM 1: Key Presence Confirmation ---")
openai_key = os.environ.get("OPENAI_API_KEY")
gemini_key = os.environ.get("GEMINI_API_KEY")
judge_key = os.environ.get("GOOGLE_JUDGE_API_KEY") or os.environ.get("GEMINI_API_KEY_EVAL")

print(f"OPENAI_API_KEY: Present={bool(openai_key)}, Length={len(openai_key) if openai_key else 0}")
print(f"GEMINI_API_KEY: Present={bool(gemini_key)}, Length={len(gemini_key) if gemini_key else 0}")
print(f"GOOGLE_JUDGE_API_KEY: Present={bool(judge_key)}, Length={len(judge_key) if judge_key else 0}")

# Item 2: Tier Resolution Validation
print("\n--- ITEM 2: Tier Resolution Validation ---")
from ask_terra import generate_content_with_retry_openai, openai_client

try:
    resp_fast = generate_content_with_retry_openai(
        openai_client=openai_client,
        model="gemma-4-26b-a4b-it-fast",
        contents="Say 'hello' in one word."
    )
    print(f"Fast Tier ('gemma-4-26b-a4b-it-fast') -> Model used: {resp_fast.model_used}")
except Exception as e:
    print(f"Fast Tier test failed: {e}")

try:
    resp_strong = generate_content_with_retry_openai(
        openai_client=openai_client,
        model="gemma-4-26b-a4b-it",
        contents="Say 'hello' in one word."
    )
    print(f"Strong Tier ('gemma-4-26b-a4b-it') -> Model used: {resp_strong.model_used}")
except Exception as e:
    print(f"Strong Tier test failed: {e}")

# Item 3: Problem 3 Validation (B03, B04, B06)
print("\n--- ITEM 3: Problem 3 Validation (B03, B04, B06) ---")
from ask_terra import terra_inference_engine, collection, extract_graph_context, smart_grader, GradeDecision

queries_to_test = [
    ("B03", "How did graduate school desegregation cases influence the Brown v. Board of Education ruling?"),
    ("B04", "How did the Civil Rights Cases of 1883 shape subsequent civil rights litigation for the next eighty years?"),
    ("B06", "How did Supreme Court jurisprudence on racial classifications in education transition from Plessy to Parents Involved?")
]

for qid, qtext in queries_to_test:
    print(f"\n[Testing {qid}]: {qtext}")
    _t0 = time.time()
    ans, ctx, timing = terra_inference_engine(qtext, return_timing=True)
    
    # Check context size and substantive text presence
    ctx_len = len(ctx)
    has_substantive_text = "Core issue:" in ctx or "Core holding" in ctx or len(ctx) > 1000
    
    # Direct smart_grader call details
    vector_results = collection.query(query_texts=[qtext], n_results=2)
    retrieved_traces = vector_results['documents'][0]
    retrieved_metadatas = vector_results['metadatas'][0]
    structural_ctx = extract_graph_context(retrieved_metadatas, max_depth=2)
    traces_ctx = "\n".join([f"- {t}" for t in retrieved_traces])
    compiled_ctx = f"{structural_ctx}\n{traces_ctx}"
    
    # Smart grader call
    prompt = f"""
    You are an NLI (Natural Language Inference) model acting as a quality control grader.
    Determine if the provided Legal Context logically ENTAILS the information required to answer the User Query.
    
    User Query: {qtext}
    
    Legal Context: 
    {compiled_ctx}
    """
    try:
        grader_resp = generate_content_with_retry_openai(
            openai_client=openai_client,
            model="gemma-4-26b-a4b-it",
            contents=prompt,
            config={'response_mime_type': 'application/json', 'response_schema': GradeDecision}
        )
        grader_json = json.loads(grader_resp.text)
        entails = grader_json.get("entails")
        conf = grader_json.get("confidence_score")
    except Exception as e:
        entails = None
        conf = f"Error: {e}"
        
    print(f"  Result -> Context Length: {ctx_len} chars")
    print(f"  Result -> Smart Grader Entails: {entails} | Confidence: {conf}")
    print(f"  Result -> Substantive Text Present in Context: {has_substantive_text}")
    print(f"  Result -> Generation Model Used: {timing.get('_generation_model_used')}")
    print(f"  Result -> Total Latency: {timing.get('total_ms')} ms")
    print(f"  Result -> Refusal Output: {'I apologize' in ans}")

# Item 4: Problem 2 Validation (retry_sleep_ms presence)
print("\n--- ITEM 4: Problem 2 Validation (retry_sleep_ms) ---")
# Check if timing dict or CleanResponse has retry_sleep_ms
ans_b01, ctx_b01, timing_b01 = terra_inference_engine("In what year was Plessy v. Ferguson decided?", return_timing=True)
print(f"Timing dict keys returned: {list(timing_b01.keys())}")
print(f"retry_sleep_ms / _retry_sleep_ms present: {'_retry_sleep_ms' in timing_b01 or 'retry_sleep_ms' in timing_b01}")

# Item 5: Judge Client Validation
print("\n--- ITEM 5: Judge Client Validation ---")
from eval_terra import judge_client, judge_answer
print(f"Judge Client API Key Configured: {bool(judge_client)}")
try:
    judge_res = judge_answer("In what year was Plessy v. Ferguson decided?", "Plessy v. Ferguson was decided in 1896.", "Plessy v. Ferguson was decided in 1896.", is_direct_llm=False)
    print(f"Judge output: {judge_res}")
    print(f"Judge model used: {judge_res.get('_judge_model_used')}")
except Exception as e:
    print(f"Judge test failed: {e}")

print("\n" + "=" * 60)
print("PHASE 1 TEST COMPLETE")
print("=" * 60)

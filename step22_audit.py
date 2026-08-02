import json
from collections import Counter

d = json.load(open('terra_eval_raw.json', encoding='utf-8'))
print('Total records:', len(d))
print('judge_model_used counts:', Counter(r.get('judge_model_used') for r in d))
print('generation_model_used counts:', Counter(r.get('generation_model_used') for r in d))

print()
print('=== Records where generation_model_used is Gemini/Gemma family ===')
gemini_gen = [r for r in d if r.get('generation_model_used') and
              any(x in str(r.get('generation_model_used', '')) for x in ['gemma', 'gemini'])]
for r in gemini_gen:
    print(f"  qid={r['query_id']} pipeline={r['pipeline']} gen_model={r['generation_model_used']} safety_rejected={r.get('safety_rejected')}")

print()
print('=== Category B TERRA safety rejections ===')
rejected_b = [r['query_id'] for r in d
              if r['category'] == 'B_Evolutionary'
              and r['pipeline'] == '3_TERRA_GraphRAG'
              and r.get('safety_rejected')]
print('Rejected B-category query IDs:', rejected_b)

print()
print('=== judge_model_used per pipeline ===')
for pipeline in ['1_Direct_LLM', '2_Flat_RAG', '3_TERRA_GraphRAG']:
    recs = [r for r in d if r['pipeline'] == pipeline]
    counts = Counter(r.get('judge_model_used') for r in recs)
    print(f"  {pipeline}: {counts}")

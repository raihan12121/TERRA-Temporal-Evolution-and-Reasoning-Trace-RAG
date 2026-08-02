import json
import time
from eval_terra import run_generation_only

while True:
    try:
        with open('terra_generations.json', 'r', encoding='utf-8') as f:
            d = json.load(f)
        count = len(d)
        print(f"[PROGRESS] Current saved records: {count}/105")
        if count >= 105:
            print("[SUCCESS] All 105 records generated!")
            break
    except Exception as e:
        print(f"[FILE READ ERROR] {e}")
    
    print("[RUNNING] Calling run_generation_only(resume=True)...")
    try:
        run_generation_only(resume=True)
    except Exception as e:
        print(f"[RUN ERROR] {e}")
        time.sleep(2)

import os
import sys
import json
import time
import pandas as pd

RAW_PATH = "terra_eval_raw.json"
TOTAL_RECORDS = 105  # 35 queries * 3 pipelines

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def main():
    print("Starting TERRA Live Progress Monitor...")
    time.sleep(1)
    
    while True:
        clear_screen()
        print("="*65)
        print("   TERRA GraphRAG — LIVE BENCHMARK PROGRESS DASHBOARD   ")
        print("="*65)
        
        if not os.path.exists(RAW_PATH):
            print(f"\nWaiting for {RAW_PATH} to be written...")
            time.sleep(3)
            continue
            
        try:
            with open(RAW_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            # File might be mid-write by eval_terra.py
            time.sleep(1)
            continue
            
        completed = len(data)
        pct = (completed / TOTAL_RECORDS) * 100
        
        # Progress Bar
        bar_len = 30
        filled = int(bar_len * completed / TOTAL_RECORDS)
        bar = "█" * filled + "░" * (bar_len - filled)
        print(f"\nOverall Progress: [{bar}] {completed}/{TOTAL_RECORDS} ({pct:.1f}%)\n")
        
        if data:
            df = pd.DataFrame(data)
            
            print("-----------------------------------------------------------------")
            print("  CATEGORY PROGRESS & AVERAGE FAITHFULNESS (TERRA GraphRAG)")
            print("-----------------------------------------------------------------")
            categories = {
                "A_Factual": (30, "A_Factual"),
                "B_Evolutionary": (30, "B_Evolutionary"),
                "C_OutOfContext": (30, "C_OutOfContext"),
                "D_Adversarial": (15, "D_Adversarial")
            }
            
            for cat_label, (expected, cat_name) in categories.items():
                cat_df = df[df["category"] == cat_name]
                cat_done = len(cat_df)
                terra_df = cat_df[cat_df["pipeline"] == "3_TERRA_GraphRAG"]
                
                if len(terra_df) > 0:
                    avg_faith = terra_df["faithfulness"].mean()
                    faith_str = f"{avg_faith:.2f} ({avg_faith*100:.0f}%)"
                else:
                    faith_str = "Pending..."
                    
                print(f"  • {cat_label:<16} : {cat_done:>2}/{expected:<2} completed | TERRA Faithfulness: {faith_str}")
                
            print("\n-----------------------------------------------------------------")
            print("  LATEST COMPLETED EVALUATION RECORDS (Top 5)")
            print("-----------------------------------------------------------------")
            recent = data[-5:]
            for r in reversed(recent):
                qid = r.get("query_id", "N/A")
                pipe = r.get("pipeline", "N/A").replace("3_TERRA_GraphRAG", "TERRA").replace("1_Direct_LLM", "Direct").replace("2_Flat_RAG", "FlatRAG")
                faith = r.get("faithfulness", 0.0)
                rel = r.get("relevance", 0.0)
                lat = r.get("timing", {}).get("total_ms", 0) / 1000.0
                print(f"  [{qid}] {pipe:<8} | Faithfulness: {faith:.2f} | Relevance: {rel:.2f} | Latency: {lat:.1f}s")
                
        print("\n="*65)
        print("Refreshing automatically every 5 seconds... (Press Ctrl+C to exit)")
        print("="*65)
        time.sleep(5)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting Live Progress Monitor.")
        sys.exit(0)

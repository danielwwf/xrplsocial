#!/usr/bin/env python3
"""
Batch AI-Kategorisierung - 5 Branches, dann 30s Pause
"""

import json
import os
import re
import sys
import time
from pathlib import Path

API_KEY = os.environ.get("MOONSHOT_API_KEY", "")
BATCH_SIZE = 5
PAUSE_BETWEEN_BATCHES = 30  # Sekunden

def ai_categorize_batch(branches_data):
    """Kategorisiere einen Batch von Branches"""
    from openai import OpenAI
    
    client = OpenAI(api_key=API_KEY, base_url="https://api.moonshot.ai/v1")
    results = {}
    
    for branch_name, commits in branches_data:
        # Erstelle Prompt
        context = f"Branch: {branch_name}\nCommits: {' | '.join(commits[:3])}"
        
        prompt = f"""Analyze this XRPL branch:
{context}

Respond with ONLY JSON:
{{"amendment": "Name or Other", "type": "Feature|Bug Fix|Testing|Refactor|CI/CD"}}

Amendments: AMM, NFTs, Batch, DID, Clawback, Escrow, Lending, Multi-Purpose Tokens, Credentials, Checks, Payment Channel."""
        
        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="kimi-k2-thinking",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=150
                )
                
                content = response.choices[0].message.content
                json_match = re.search(r'\{[^}]*\}', content, re.DOTALL)
                
                if json_match:
                    result = json.loads(json_match.group())
                    result["source"] = "ai_kimi"
                    results[branch_name] = result
                    print(f"  ✅ {branch_name[:40]:40s} -> {result.get('amendment', 'Other')}")
                    break
                    
            except Exception as e:
                if "429" in str(e) or "overloaded" in str(e).lower():
                    wait = 2 ** attempt
                    print(f"  ⏳ Retry {attempt+1}/{max_retries} for {branch_name[:30]}... (wait {wait}s)")
                    time.sleep(wait)
                else:
                    print(f"  ⚠️  Error: {str(e)[:40]}")
                    break
        else:
            # All retries failed
            print(f"  ❌ Failed after retries: {branch_name[:40]}")
            results[branch_name] = None
        
        # Kleine Pause zwischen Branches im Batch
        time.sleep(1)
    
    return results

def main():
    print("=" * 70)
    print("BATCH AI KATEGORISIERUNG")
    print(f"Batch-Größe: {BATCH_SIZE}, Pause: {PAUSE_BETWEEN_BATCHES}s")
    print("=" * 70)
    print()
    
    # Lade Branches
    with open("stats/data/branches.json") as f:
        data = json.load(f)
    
    branches = [(b['name'], [c.get('message', '') for c in b.get('commits', [])[:3]]) 
                for b in data.get('branches', [])]
    
    total = len(branches)
    print(f"📊 Total: {total} Branches")
    
    # Lade existierende Kategorien
    cache_file = Path("stats/data/ai_categories.json")
    if cache_file.exists():
        with open(cache_file) as f:
            categories = json.load(f)
        print(f"💾 Bereits fertig: {len(categories)}")
    else:
        categories = {}
    
    # Filtere Branches die noch nicht kategorisiert sind
    remaining = [(name, commits) for name, commits in branches if name not in categories]
    print(f"🔄 Noch zu tun: {len(remaining)}")
    print()
    
    # Verarbeite in Batches
    batch_num = 0
    for i in range(0, len(remaining), BATCH_SIZE):
        batch_num += 1
        batch = remaining[i:i+BATCH_SIZE]
        
        print(f"\n{'='*70}")
        print(f"BATCH {batch_num}/{(len(remaining)+BATCH_SIZE-1)//BATCH_SIZE}: {len(batch)} Branches")
        print(f"{'='*70}")
        
        # Kategorisiere Batch
        results = ai_categorize_batch(batch)
        
        # Speichere Ergebnisse
        for name, result in results.items():
            if result:
                categories[name] = result
        
        # Zwischenspeicher
        with open(cache_file, 'w') as f:
            json.dump(categories, f, indent=2)
        
        print(f"\n💾 Gespeichert: {len(categories)}/{total} Branches")
        
        # Pause vor nächstem Batch
        if i + BATCH_SIZE < len(remaining):
            print(f"\n😴 Pause für {PAUSE_BETWEEN_BATCHES} Sekunden (API auskühlen)...")
            time.sleep(PAUSE_BETWEEN_BATCHES)
    
    # Finale Zusammenfassung
    print(f"\n{'='*70}")
    print("FERTIG!")
    print(f"{'='*70}")
    print(f"✅ AI-Kategorisiert: {sum(1 for c in categories.values() if c.get('source') == 'ai_kimi')}")
    print(f"📁 Gesamt: {len(categories)}")
    print(f"\nDatei: {cache_file}")

if __name__ == "__main__":
    main()

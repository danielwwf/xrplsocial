#!/usr/bin/env python3
"""
Single-Branch AI Kategorisierung - einer nach dem anderen mit 5s Pause
"""

import json
import os
import re
import sys
import time
from pathlib import Path

API_KEY = os.environ.get("MOONSHOT_API_KEY", "")
PAUSE_SECONDS = 5  # Pause zwischen Branches

def ai_categorize_one(branch_name, commits):
    """Kategorisiere EINEN Branch"""
    from openai import OpenAI
    
    client = OpenAI(api_key=API_KEY, base_url="https://api.moonshot.ai/v1")
    
    context = f"Branch: {branch_name}\nCommits: {' | '.join(commits[:3])}"
    
    prompt = f"""Analyze this XRPL branch:
{context}

Respond with ONLY JSON:
{{"amendment": "Name or Other", "type": "Feature|Bug Fix|Testing|Refactor|CI/CD"}}

Amendments: AMM, NFTs, Batch, DID, Clawback, Escrow, Lending, Multi-Purpose Tokens, Credentials."""
    
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
                return result
                
        except Exception as e:
            if "429" in str(e) or "overloaded" in str(e).lower():
                wait = 3 ** attempt  # 3, 9, 27, 81, 243 Sekunden
                print(f"    ⏳ API überlastet, warte {wait}s...")
                time.sleep(wait)
            else:
                print(f"    ⚠️  Fehler: {str(e)[:40]}")
                return None
    
    return None

def main():
    print("=" * 70)
    print("SINGLE-BRANCH AI KATEGORISIERUNG")
    print(f"Pause: {PAUSE_SECONDS}s zwischen Branches")
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
    
    # Filtere Branches die noch nicht mit AI kategorisiert sind
    remaining = [(name, commits) for name, commits in branches 
                 if name not in categories or categories[name].get('source') != 'ai_kimi']
    
    print(f"🔄 Noch zu tun: {len(remaining)}")
    print()
    
    # Verarbeite einen nach dem anderen
    for i, (name, commits) in enumerate(remaining, 1):
        print(f"[{i:3d}/{len(remaining):3d}] {name[:50]:50s} ... ", end="")
        sys.stdout.flush()
        
        result = ai_categorize_one(name, commits)
        
        if result:
            categories[name] = result
            print(f"✅ {result.get('amendment', 'Other')[:20]}")
        else:
            print(f"❌ Fehlgeschlagen")
        
        # Speichere nach jedem Branch
        with open(cache_file, 'w') as f:
            json.dump(categories, f, indent=2)
        
        # Pause vor nächstem
        if i < len(remaining):
            time.sleep(PAUSE_SECONDS)
    
    # Finale Zusammenfassung
    ai_count = sum(1 for c in categories.values() if c.get('source') == 'ai_kimi')
    print(f"\n{'='*70}")
    print("FERTIG!")
    print(f"{'='*70}")
    print(f"✅ AI-Kategorisiert: {ai_count}/{total}")
    print(f"📁 Gesamt: {len(categories)}")

if __name__ == "__main__":
    main()

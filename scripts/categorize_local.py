#!/usr/bin/env python3
"""
Lokale AI-Kategorisierung aller XRPL Branches
Langsam, aber zuverlässig mit Retry-Logik
"""

import json
import os
import re
import sys
import time
from pathlib import Path
from datetime import datetime

# Config
API_KEY = os.environ.get("MOONSHOT_API_KEY", "")
PAUSE_SECONDS = 5.0  # Pause zwischen Calls (5s wegen Überlastung)
MAX_RETRIES = 10     # Max Retries bei 429
BASE_DELAY = 3       # Start-Delay für Backoff

def log_progress(current, total, branch_name, status):
    """Zeige Fortschritt an"""
    if total > 0:
        percent = (current / total) * 100
        print(f"[{current:3d}/{total}] {percent:5.1f}% | {status:15s} | {branch_name[:50]}")
    else:
        print(f"[Retry] {status:15s} | {branch_name[:50]}")
    sys.stdout.flush()

def ai_categorize_with_retry(branch_name, commit_messages):
    """Kategorisiere einen Branch mit Retry-Logik"""
    from openai import OpenAI
    
    if not API_KEY:
        print("❌ Kein API Key!")
        return None
    
    client = OpenAI(
        api_key=API_KEY,
        base_url="https://api.moonshot.ai/v1"
    )
    
    context = f"""
Branch name: {branch_name}

Recent commits:
{chr(10).join(commit_messages[:5]) if commit_messages else "No commits available"}
"""
    
    prompt = f"""Analyze this GitHub branch and categorize it for the XRP Ledger (XRPL) protocol.

{context}

Respond ONLY with valid JSON:
{{
  "amendment": "Name of the amendment or 'Other'",
  "type": "Feature|Bug Fix|Testing|Refactor|CI/CD|Documentation",
  "confidence": 0.0-1.0
}}

Common XRPL amendments: AMM, NFTs, Batch, DID, Clawback, Escrow, Lending, Multi-Purpose Tokens, Credentials, Checks.
"""
    
    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model="kimi-k2-thinking",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )
            
            content = response.choices[0].message.content
            json_match = re.search(r'\{[^}]*\}', content, re.DOTALL)
            
            if json_match:
                result = json.loads(json_match.group())
                result["source"] = "ai_kimi"
                return result
                
        except Exception as e:
            error_msg = str(e)
            
            if "429" in error_msg or "overloaded" in error_msg.lower() or "rate" in error_msg.lower():
                # Exponential Backoff
                delay = BASE_DELAY * (2 ** attempt)
                log_progress(0, 0, branch_name, f"Retry {attempt+1}/{MAX_RETRIES} ({delay}s)")
                time.sleep(delay)
            else:
                print(f"⚠️  Error: {error_msg[:50]}")
                return None
    
    return None  # Max retries reached

def main():
    print("=" * 80)
    print("XRPL Branch AI Kategorisierung (Lokal)")
    print("=" * 80)
    print()
    
    # Lade Branches
    branches_file = Path("stats/data/branches.json")
    if not branches_file.exists():
        print("❌ branches.json nicht gefunden!")
        return
    
    with open(branches_file) as f:
        data = json.load(f)
    
    branches = data.get('branches', [])
    total = len(branches)
    
    print(f"📊 {total} Branches zu kategorisieren")
    print(f"⏱️  Pause: {PAUSE_SECONDS}s zwischen Calls")
    print(f"🔄 Max Retries: {MAX_RETRIES}")
    print()
    
    # Lade existierende Kategorien (falls vorhanden)
    cache_file = Path("stats/data/ai_categories.json")
    if cache_file.exists():
        with open(cache_file) as f:
            categories = json.load(f)
        print(f"💾 {len(categories)} existierende Kategorien geladen")
    else:
        categories = {}
        print("🆕 Starte von vorne (kein Cache)")
    
    print()
    print("=" * 80)
    print("STARTE KATEGORISIERUNG...")
    print("=" * 80)
    print()
    
    # Verarbeite jeden Branch
    success_count = 0
    error_count = 0
    skipped_count = 0
    
    for i, branch in enumerate(branches, 1):
        name = branch.get('name')
        
        # Überspringe wenn schon im Cache
        if name in categories and categories[name].get('source') == 'ai_kimi':
            skipped_count += 1
            continue
        
        commits = [c.get('message', '') for c in branch.get('commits', [])[:3]]
        
        # Kategorisiere
        result = ai_categorize_with_retry(name, commits)
        
        if result:
            categories[name] = result
            success_count += 1
            status = "✅ AI"
        else:
            # Fallback zu Keywords
            from scripts.ai_categorize import keyword_categorize
            kw_result = keyword_categorize(name, commits) or {
                "amendment": "Other",
                "type": "Unknown",
                "confidence": 0,
                "source": "fallback"
            }
            categories[name] = kw_result
            error_count += 1
            status = "🔑 Keyword"
        
        # Zeige Fortschritt
        log_progress(i, total, name, status)
        
        # Speichere Zwischenstand alle 10 Branches
        if i % 10 == 0:
            with open(cache_file, 'w') as f:
                json.dump(categories, f, indent=2)
            print(f"   💾 Zwischenstand gespeichert ({len(categories)} Branches)")
        
        # Pause
        time.sleep(PAUSE_SECONDS)
    
    # Finaler Speicher
    with open(cache_file, 'w') as f:
        json.dump(categories, f, indent=2)
    
    # Zusammenfassung
    print()
    print("=" * 80)
    print("FERTIG!")
    print("=" * 80)
    print(f"✅ AI-Kategorisierung: {success_count}")
    print(f"🔑 Keyword-Fallback: {error_count}")
    print(f"⏭️  Übersprungen: {skipped_count}")
    print()
    print(f"📁 Gespeichert in: {cache_file}")
    print()
    print("Nächster Schritt:")
    print("  git add stats/data/ai_categories.json")
    print("  git commit -m 'Add AI categories'")
    print("  git push")

if __name__ == "__main__":
    main()

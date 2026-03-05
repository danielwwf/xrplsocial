#!/usr/bin/env python3
"""
Mega-Batch: Alle 207 Branches in EINEM API-Call
Nur 1 Request statt 207!
"""

import json
import os
from pathlib import Path

API_KEY = os.environ.get("MOONSHOT_API_KEY", "")

def categorize_all_at_once():
    from openai import OpenAI
    
    # Lade alle Branches
    with open("stats/data/branches.json") as f:
        data = json.load(f)
    
    branches = data.get('branches', [])
    
    # Erstelle Mega-Prompt - ALLE 207 Branches
    branches_text = []
    for i, b in enumerate(branches, 1):
        name = b.get('name', 'unknown')
        commits = [c.get('message', '')[:60] for c in b.get('commits', [])[:1]]
        branches_text.append(f"{i}. {name} | {'; '.join(commits) if commits else 'no commits'}")
    
    mega_prompt = f"""Categorize {len(branches)} XRPL branches. Return JSON: {{"branch-name": {{"amendment": "...", "type": "..."}}}}

Amendments: AMM, NFTs, Batch, DID, Clawback, Escrow, Lending, MPT, Credentials, Checks, PaymentChannel, SmartEscrow, OpenTelemetry, Other
Types: Feature, BugFix, Testing, Refactor, CI/CD, Documentation

Branches:
{chr(10).join(branches_text)}

JSON ONLY:"""
    
    print("="*70)
    print(f"Sende {len(branches)} Branches in EINEM Request...")
    print("="*70)
    print()
    
    client = OpenAI(api_key=API_KEY, base_url="https://api.moonshot.ai/v1")
    
    try:
        response = client.chat.completions.create(
            model="kimi-k2-thinking",
            messages=[{"role": "user", "content": mega_prompt}],
            temperature=0.3,
            max_tokens=4000  # Sehr groß für alle Antworten
        )
        
        content = response.choices[0].message.content
        print("✅ ANTWORT ERHALTEN!")
        print()
        print("Antwort (erste 1000 Zeichen):")
        print(content[:1000])
        print()
        
        # Speichere Roh-Antwort
        with open("stats/data/ai_response_raw.txt", 'w') as f:
            f.write(content)
        print("💾 Rohe Antwort gespeichert in: ai_response_raw.txt")
        
        # Versuche JSON zu parsen
        try:
            # Suche JSON-Block
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                categories = json.loads(json_match.group())
                print(f"✅ JSON geparst: {len(categories)} Branches")
                
                # Speichere
                with open("stats/data/ai_categories.json", 'w') as f:
                    json.dump(categories, f, indent=2)
                print("💾 Kategorien gespeichert!")
                return True
        except Exception as e:
            print(f"⚠️ JSON Parse-Fehler: {e}")
            print("Bitte ai_response_raw.txt manuell prüfen!")
            return False
            
    except Exception as e:
        print(f"❌ FEHLER: {e}")
        return False

if __name__ == "__main__":
    categorize_all_at_once()

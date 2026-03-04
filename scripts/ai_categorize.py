#!/usr/bin/env python3
"""
AI-powered branch categorization for XRPL Amendment Stats
Caches results to minimize API costs
"""

import json
import os
import re
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Optional

# Optional: Anthropic/Claude API
# pip install anthropic
# Set ANTHROPIC_API_KEY environment variable

CACHE_FILE = Path(__file__).parent.parent / "stats" / "data" / "ai_categories.json"
COST_LOG_FILE = Path(__file__).parent.parent / "stats" / "data" / "ai_cost_log.json"

# Fallback categorization without AI (for testing/cost-saving)
KEYWORD_MAP = {
    "nft": {"amendment": "NFTs", "type": "Feature", "confidence": 0.7},
    "amm": {"amendment": "AMM", "type": "Feature", "confidence": 0.8},
    "batch": {"amendment": "Batch Transactions", "type": "Feature", "confidence": 0.8},
    "did": {"amendment": "DID", "type": "Feature", "confidence": 0.8},
    "clawback": {"amendment": "Clawback", "type": "Feature", "confidence": 0.9},
    "bridge": {"amendment": "Cross-chain Bridges", "type": "Feature", "confidence": 0.8},
    "escrow": {"amendment": "Escrow", "type": "Feature", "confidence": 0.6},
    "fix": {"amendment": None, "type": "Bug Fix", "confidence": 0.5},
    "test": {"amendment": None, "type": "Testing", "confidence": 0.6},
    "ci": {"amendment": None, "type": "CI/CD", "confidence": 0.7},
    "refactor": {"amendment": None, "type": "Refactor", "confidence": 0.6},
    "modular": {"amendment": "Code Modularization", "type": "Refactor", "confidence": 0.7},
    "rust": {"amendment": "Rust/WASM", "type": "Feature", "confidence": 0.8},
    "wasm": {"amendment": "Rust/WASM", "type": "Feature", "confidence": 0.8},
}

# XLS Standards mapping
XLS_STANDARDS = {
    "30": "AMM",
    "14": "Escrow",
    "39": "Clawback", 
    "40": "DID",
    "20": "Batch",
    "34": "NFTs",
    "38": "Multi-Purpose Tokens",
    "33": "Credentials",
    "37": "Checks",
    "11": "Payment Channels",
}

# Feature file patterns (from rippled source code)
FEATURE_PATTERNS = {
    r'fixTokenEscrow|fix1623': {'amendment': 'Token Escrow', 'type': 'Bug Fix'},
    r'fixNFT|fixTokenization': {'amendment': 'NFTs', 'type': 'Bug Fix'},
    r'fixAMMv[0-9]*|fixAMM': {'amendment': 'AMM', 'type': 'Bug Fix'},
    r'fixDID|fixDid': {'amendment': 'DID', 'type': 'Bug Fix'},
    r'fixClawback|fix1620': {'amendment': 'Clawback', 'type': 'Bug Fix'},
    r'fixBatch|fix1575': {'amendment': 'Batch Transactions', 'type': 'Bug Fix'},
    r'fixCredentials|fixCredential': {'amendment': 'Credentials', 'type': 'Bug Fix'},
    r'fixMPT|fixMultiPurposeToken': {'amendment': 'Multi-Purpose Tokens', 'type': 'Bug Fix'},
    r'fixCheck|fixCheckCash': {'amendment': 'Checks', 'type': 'Bug Fix'},
    r'featureAMM': {'amendment': 'AMM', 'type': 'Feature'},
    r'featureNFT': {'amendment': 'NFTs', 'type': 'Feature'},
    r'featureDID': {'amendment': 'DID', 'type': 'Feature'},
    r'featureClawback': {'amendment': 'Clawback', 'type': 'Feature'},
    r'featureBatch': {'amendment': 'Batch Transactions', 'type': 'Feature'},
    r'featureMPT': {'amendment': 'Multi-Purpose Tokens', 'type': 'Feature'},
    r'featureCredentials': {'amendment': 'Credentials', 'type': 'Feature'},
}

# Extended keyword mapping with more patterns
EXTENDED_KEYWORDS = {
    # Amendments
    'nft': {'amendment': 'NFTs', 'type': 'Feature', 'confidence': 0.85},
    'tokenization': {'amendment': 'NFTs', 'type': 'Feature', 'confidence': 0.8},
    'amm': {'amendment': 'AMM', 'type': 'Feature', 'confidence': 0.9},
    'automated.market': {'amendment': 'AMM', 'type': 'Feature', 'confidence': 0.85},
    'liquidity.pool': {'amendment': 'AMM', 'type': 'Feature', 'confidence': 0.8},
    'batch': {'amendment': 'Batch Transactions', 'type': 'Feature', 'confidence': 0.9},
    'did': {'amendment': 'DID', 'type': 'Feature', 'confidence': 0.9},
    'decentralized.identity': {'amendment': 'DID', 'type': 'Feature', 'confidence': 0.85},
    'clawback': {'amendment': 'Clawback', 'type': 'Feature', 'confidence': 0.95},
    'escrow': {'amendment': 'Escrow', 'type': 'Feature', 'confidence': 0.7},
    'token.escrow': {'amendment': 'Token Escrow', 'type': 'Feature', 'confidence': 0.8},
    'check': {'amendment': 'Checks', 'type': 'Feature', 'confidence': 0.6},
    'credential': {'amendment': 'Credentials', 'type': 'Feature', 'confidence': 0.85},
    'auth': {'amendment': 'Credentials', 'type': 'Feature', 'confidence': 0.5},
    'mpt': {'amendment': 'Multi-Purpose Tokens', 'type': 'Feature', 'confidence': 0.9},
    'multi.purpose': {'amendment': 'Multi-Purpose Tokens', 'type': 'Feature', 'confidence': 0.85},
    'payment.channel': {'amendment': 'Payment Channels', 'type': 'Feature', 'confidence': 0.8},
    'bridge': {'amendment': 'Cross-chain Bridges', 'type': 'Feature', 'confidence': 0.8},
    'lending': {'amendment': 'Lending', 'type': 'Feature', 'confidence': 0.8},
    'negative.unl': {'amendment': 'Negative UNL', 'type': 'Feature', 'confidence': 0.8},
    'fee.escalation': {'amendment': 'Fee Escalation', 'type': 'Feature', 'confidence': 0.8},
    
    # Types
    'fix': {'amendment': None, 'type': 'Bug Fix', 'confidence': 0.6},
    'bugfix': {'amendment': None, 'type': 'Bug Fix', 'confidence': 0.7},
    'hotfix': {'amendment': None, 'type': 'Bug Fix', 'confidence': 0.7},
    'patch': {'amendment': None, 'type': 'Bug Fix', 'confidence': 0.5},
    'test': {'amendment': None, 'type': 'Testing', 'confidence': 0.7},
    'testing': {'amendment': None, 'type': 'Testing', 'confidence': 0.7},
    'ci': {'amendment': None, 'type': 'CI/CD', 'confidence': 0.8},
    'github.action': {'amendment': None, 'type': 'CI/CD', 'confidence': 0.8},
    'workflow': {'amendment': None, 'type': 'CI/CD', 'confidence': 0.6},
    'refactor': {'amendment': None, 'type': 'Refactor', 'confidence': 0.7},
    'modular': {'amendment': 'Code Modularization', 'type': 'Refactor', 'confidence': 0.8},
    'cleanup': {'amendment': None, 'type': 'Refactor', 'confidence': 0.6},
    'rust': {'amendment': 'Rust/WASM', 'type': 'Feature', 'confidence': 0.9},
    'wasm': {'amendment': 'Rust/WASM', 'type': 'Feature', 'confidence': 0.9},
    'webassembly': {'amendment': 'Rust/WASM', 'type': 'Feature', 'confidence': 0.85},
    'conan': {'amendment': 'Code Modularization', 'type': 'Refactor', 'confidence': 0.6},
    'cmake': {'amendment': 'Code Modularization', 'type': 'Refactor', 'confidence': 0.5},
    'docs': {'amendment': None, 'type': 'Documentation', 'confidence': 0.7},
    'readme': {'amendment': None, 'type': 'Documentation', 'confidence': 0.8},
}


def load_cache() -> dict:
    """Load cached AI categorizations"""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE) as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_cache(cache: dict):
    """Save cache to disk"""
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2, default=str)


def log_cost(branch_name: str, cost_usd: float, method: str):
    """Log AI usage for cost tracking"""
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "branch": branch_name,
        "cost_usd": cost_usd,
        "method": method
    }
    
    logs = []
    if COST_LOG_FILE.exists():
        try:
            with open(COST_LOG_FILE) as f:
                logs = json.load(f)
        except:
            pass
    
    logs.append(log_entry)
    COST_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(COST_LOG_FILE, 'w') as f:
        json.dump(logs, f, indent=2)


def get_total_cost() -> float:
    """Get total AI usage cost"""
    if not COST_LOG_FILE.exists():
        return 0.0
    try:
        with open(COST_LOG_FILE) as f:
            logs = json.load(f)
            return sum(entry.get("cost_usd", 0) for entry in logs)
    except:
        return 0.0


def keyword_categorize(branch_name: str, commit_messages: list = None) -> Optional[dict]:
    """
    Categorize using extended keywords and patterns (free, no AI)
    Checks branch name AND commit messages
    Returns None if no confident match found
    """
    # Combine all text to check
    texts = [branch_name.lower()]
    if commit_messages:
        # Check first 5 commit messages
        texts.extend([msg.lower() for msg in commit_messages[:5]])
    
    combined_text = " ".join(texts)
    
    # Check XLS references first (high confidence)
    xls_match = re.search(r'xls-?(\d+)', combined_text)
    if xls_match:
        xls_num = xls_match.group(1).lstrip('0') or '0'
        if xls_num in XLS_STANDARDS:
            return {
                "amendment": XLS_STANDARDS[xls_num],
                "type": "Feature",
                "confidence": 0.9,
                "source": "xls_reference"
            }
    
    # Check for feature file patterns in commit messages
    if commit_messages:
        for msg in commit_messages[:3]:  # Check first 3 commits
            msg_lower = msg.lower()
            for pattern, category in FEATURE_PATTERNS.items():
                if re.search(pattern, msg_lower, re.IGNORECASE):
                    result = category.copy()
                    result["confidence"] = 0.85
                    result["source"] = "feature_pattern"
                    return result
    
    # Check extended keywords with word boundaries
    best_match = None
    best_confidence = 0
    
    for keyword, category in EXTENDED_KEYWORDS.items():
        # Use word boundary matching for better accuracy
        pattern = r'\b' + keyword.replace('.', r'\.').replace('-', r'\-') + r'\b'
        if re.search(pattern, combined_text, re.IGNORECASE):
            if category["confidence"] > best_confidence:
                best_confidence = category["confidence"]
                best_match = category.copy()
                best_match["source"] = "keyword_match"
    
    if best_match and best_confidence >= 0.6:
        return best_match
    
    return None


def ai_categorize(branch_name: str, commit_messages: list, pr_diff: str = None) -> dict:
    """
    Categorize using AI (Moonshot API with Kimi K2.5)
    Cost: ~$0.001-0.002 per analysis (much cheaper than Claude)
    """
    api_key = os.environ.get("MOONSHOT_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    
    if not api_key:
        print(f"⚠️  No API key found, falling back to keywords for {branch_name}")
        return keyword_categorize(branch_name, commit_messages) or {
            "amendment": "Other",
            "type": "Unknown",
            "confidence": 0,
            "source": "fallback"
        }
    
    # Try Moonshot first, fallback to Anthropic
    try:
        import urllib.request
        import urllib.error
        
        context = f"""
Branch name: {branch_name}

Recent commits:
{chr(10).join(commit_messages[:10]) if commit_messages else "No commits available"}

PR diff excerpt (first 2000 chars):
{pr_diff[:2000] if pr_diff else "No diff available"}
"""
        
        prompt = f"""Analyze this GitHub branch and categorize it for the XRP Ledger (XRPL) protocol.

{context}

Respond ONLY with valid JSON in this exact format:
{{
  "amendment": "Name of the amendment this relates to, or 'Other' if none",
  "type": "Feature|Bug Fix|Testing|Refactor|CI/CD|Documentation",
  "status": "In Development|Under Review|Ready|Merged|Unknown",
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation of why you chose this categorization"
}}

Common XRPL amendments: AMM, NFTs, Batch Transactions, DID, Clawback, Escrow, Check, Payment Channel, Token Escrow, Multi-Purpose Tokens, Credentials.
If you see "fix" in the name, it's likely a bug fix for an existing amendment.
"""
        
        # Moonshot API call using OpenAI client (more reliable)
        try:
            from openai import OpenAI
            
            client = OpenAI(
                api_key=api_key,
                base_url="https://api.moonshot.ai/v1"
            )
            
            response = client.chat.completions.create(
                model="kimi-k2-thinking",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300
            )
            
            content = response.choices[0].message.content
            
            # Extract JSON from response
            json_match = re.search(r'\{[^}]*\}', content, re.DOTALL)
            if json_match:
                result_data = json.loads(json_match.group())
                result_data["source"] = "ai_kimi"
                
                # Log cost
                estimated_cost = 0.0007
                log_cost(branch_name, estimated_cost, "kimi-k2-thinking")
                
                # Rate limiting - stay well under 500 RPM limit
                time.sleep(1.0)  # 1s pause = max 60 RPM
                
                return result_data
                
        except Exception as e:
            print(f"⚠️  OpenAI client error for {branch_name}: {e}")
    
    # Fallback to keywords
    return keyword_categorize(branch_name, commit_messages) or {
        "amendment": "Other",
        "type": "Unknown",
        "confidence": 0,
        "source": "fallback"
    }


def categorize_branch(branch_name: str, commit_messages: list = None, 
                      pr_diff: str = None, force_refresh: bool = False) -> dict:
    """
    Main entry point: AI-first categorization
    Uses AI for ALL branches when API key available, keywords as fallback
    """
    cache = load_cache()
    
    # Check cache first
    if not force_refresh and branch_name in cache:
        cached = cache[branch_name]
        cached["cached"] = True
        return cached
    
    # Check if we have API key - if yes, use AI for everything
    api_key = os.environ.get("MOONSHOT_API_KEY")
    if api_key:
        result = ai_categorize(branch_name, commit_messages, pr_diff)
        result["cached"] = False
        cache[branch_name] = result
        save_cache(cache)
        return result
    
    # No API key: Try keyword categorization as fallback
    keyword_result = keyword_categorize(branch_name, commit_messages)
    
    if keyword_result:
        cache[branch_name] = keyword_result
        save_cache(cache)
        return keyword_result
    
    # Ultimate fallback
    return { 
        "amendment": "Other", 
        "type": "Unknown", 
        "confidence": 0, 
        "source": "fallback",
        "cached": False
    }


def batch_categorize(branches: list, branches_data: dict = None) -> dict:
    """
    Categorize multiple branches efficiently
    Only calls AI for uncached branches with low keyword confidence
    """
    cache = load_cache()
    results = {}
    ai_calls_made = 0
    
    print(f"📊 Processing {len(branches)} branches...")
    print(f"💰 Current month AI cost: ${get_total_cost():.4f}")
    
    for i, branch_name in enumerate(branches):
        # Get commit messages from branches_data if available
        commit_messages = []
        if branches_data and branch_name in branches_data:
            branch_info = branches_data[branch_name]
            if isinstance(branch_info, dict):
                commits = branch_info.get('commits', [])
                commit_messages = [c.get('message', '') for c in commits if isinstance(c, dict)]
        
        result = categorize_branch(branch_name, commit_messages)
        results[branch_name] = result
        
        if result.get("source") == "ai_claude":
            ai_calls_made += 1
        
        # Progress indicator
        if (i + 1) % 10 == 0:
            print(f"  {i + 1}/{len(branches)} processed...")
    
    print(f"\n✅ Done! {ai_calls_made} AI calls made this run")
    print(f"💰 New total cost: ${get_total_cost():.4f}")
    
    return results


if __name__ == "__main__":
    # Test with some example branches
    test_branches = [
        "feature/nft-burnable",
        "fix/escrow-edge-case",
        "test/amm-integration",
        "refactor/modular-transaction",
        "xls-30-amm-implementation",
        "ci/github-actions-update",
        "batch-transactions-v2",
        "clawback-fix",
        "random-branch-name"
    ]
    
    print("🧪 Running test categorizations...\n")
    
    for branch in test_branches:
        result = categorize_branch(branch)
        source_icon = "🤖" if result.get("source") == "ai_kimi" else "🔑" if result.get("source") == "keyword_match" else "❓"
        cached_icon = "💾" if result.get("cached") else "🆕"
        amendment_name = result.get('amendment') or 'Other'
        print(f"{source_icon} {cached_icon} {branch:40} → {amendment_name:25} ({result.get('type', 'Unknown')}, conf: {result.get('confidence', 0):.2f})")
    
    print(f"\n📁 Cache file: {CACHE_FILE}")
    print(f"📁 Cost log: {COST_LOG_FILE}")

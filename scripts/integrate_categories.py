#!/usr/bin/env python3
"""
Integrate AI categorization into the existing branch data
"""

import json
import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from ai_categorize import batch_categorize, load_cache

def integrate_categories():
    """
    Load existing branch data and add AI categorization
    """
    data_dir = Path(__file__).parent.parent / "stats" / "data"
    
    # Load branches data
    branches_file = data_dir / "branches.json"
    if not branches_file.exists():
        print("❌ No branches.json found")
        return
    
    with open(branches_file) as f:
        branches_data = json.load(f)
    
    branches = branches_data.get('branches', [])
    branch_names = [b.get('name') for b in branches]
    
    print(f"📊 Found {len(branch_names)} branches to categorize")
    
    # Build branches dict for the categorizer
    branches_dict = {b.get('name'): b for b in branches}
    
    # Run categorization (uses cache for known branches)
    categories = batch_categorize(branch_names, branches_dict)
    
    # Merge categories into branch data
    for branch in branches:
        name = branch.get('name')
        if name in categories:
            cat = categories[name]
            branch['ai_category'] = {
                'amendment': cat.get('amendment') or 'Other',
                'type': cat.get('type', 'Unknown'),
                'confidence': cat.get('confidence', 0),
                'source': cat.get('source', 'unknown')
            }
    
    # Save updated branches data
    with open(branches_file, 'w') as f:
        json.dump(branches_data, f, indent=2)
    
    # Generate summary
    amendment_counts = {}
    type_counts = {}
    ai_vs_keyword = {'ai_kimi': 0, 'keyword_match': 0, 'fallback': 0}
    
    for branch in branches:
        cat = branch.get('ai_category', {})
        
        # Amendment counts
        amd = cat.get('amendment', 'Other')
        amendment_counts[amd] = amendment_counts.get(amd, 0) + 1
        
        # Type counts
        typ = cat.get('type', 'Unknown')
        type_counts[typ] = type_counts.get(typ, 0) + 1
        
        # Source counts
        src = cat.get('source', 'unknown')
        if src in ai_vs_keyword:
            ai_vs_keyword[src] += 1
    
    print("\n📊 Categorization Summary:")
    print("\nBy Amendment:")
    for amd, count in sorted(amendment_counts.items(), key=lambda x: -x[1]):
        print(f"  {amd}: {count}")
    
    print("\nBy Type:")
    for typ, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {typ}: {count}")
    
    print(f"\nSource breakdown:")
    print(f"  🤖 AI (Kimi K2.5): {ai_vs_keyword['ai_kimi']}")
    print(f"  🔑 Keywords: {ai_vs_keyword['keyword_match']}")
    print(f"  ❓ Fallback: {ai_vs_keyword['fallback']}")
    
    # Save category summary for frontend
    summary = {
        'generated_at': branches_data.get('generated_at'),
        'total_branches': len(branches),
        'by_amendment': amendment_counts,
        'by_type': type_counts,
        'by_source': ai_vs_keyword
    }
    
    summary_file = data_dir / "category_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✅ Updated {len(branches)} branches with AI categories")
    print(f"📁 Summary saved to: {summary_file}")

if __name__ == "__main__":
    integrate_categories()

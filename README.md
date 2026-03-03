# XRPL Social Stats

A dashboard visualizing contributor activity across XRPL (XRP Ledger) feature branches. See who's working on what amendments in real-time.

🔗 **Live Dashboard:** https://xrpl.social/stats/

## What is this?

The XRPL Stats Dashboard tracks development activity on the [XRPLF/rippled](https://github.com/XRPLF/rippled) repository. It groups feature branches by amendment type and shows contributor activity.

**Key Features:**
- 📦 **By Amendment** — Grouped view of all feature branches by amendment type
- 👥 **By Person** — See what each contributor is working on
- 🌿 **All Branches** — Detailed view of every feature branch
- 💡 **Insights** — Statistics, top contributors, and hot amendments

## How it works

```
┌─────────────────────────────────────────────────────────────────┐
│                    GitHub Actions (Hourly)                       │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │
│  │  git fetch   │ →  │   analyze    │ →  │   commit     │      │
│  │  rippled     │    │   branches   │    │   JSON       │      │
│  └──────────────┘    └──────────────┘    └──────────────┘      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GitHub Pages                                  │
│  ┌──────────────┐    ┌──────────────┐                           │
│  │  branches    │    │  index.html  │                           │
│  │  .json       │    │  (dashboard) │                           │
│  └──────────────┘    └──────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **GitHub Actions** runs every hour (`0 * * * *`)
2. Clones/fetches `XRPLF/rippled` repository
3. Analyzes all feature branches (excludes `master`, `develop`, `release/*`)
4. Extracts:
   - Last commit per branch
   - All contributors (from last 30 commits per branch)
   - Commit messages and dates
5. Generates `stats/data/branches.json`
6. Commits and pushes to this repository
7. GitHub Pages automatically deploys the updated dashboard

### Why not GitHub API?

We use `git clone` instead of the GitHub API because:
- ✅ No rate limits (5,000/hour for API vs. unlimited for git)
- ✅ All data in one go (branches, commits, contributors)
- ✅ Faster for large repositories with 200+ branches

## Local Development

```bash
# Clone this repository
git clone https://github.com/danielwwf/xrplsocial.git
cd xrplsocial

# Serve locally (any static server works)
cd stats
python3 -m http.server 8080
# Open http://localhost:8080
```

### Generate data locally

```bash
# Clone XRPL rippled repository
git clone https://github.com/XRPLF/rippled.git ~/rippled

# Run the analysis script
python3 .github/workflows/analyze_branches.py
```

## Dashboard Views

### By Amendment
Branches grouped by amendment type:
- 📦 Batch Transactions
- 💰 AMM (Automated Market Maker)
- 🆔 DID (Decentralized Identity)
- 🎨 NFTs
- 👋 Clawback
- 🔧 Bug Fixes
- And more...

Click any card for detailed view with:
- All contributors
- Recent activity timeline
- All branches in the amendment

### By Person
See what each contributor is working on:
- Total commits
- Branches they're active on
- Amendments they're contributing to

### All Branches
A detailed card view of every feature branch with:
- Amendment category
- Activity status (Active/Recent/Dormant)
- Latest commit message
- Contributors

Click any branch for detailed view.

### Insights
- Active branches (last 7 days)
- Recent branches (last 30 days)
- Total branches and contributors
- 🔥 Hot Amendments (most recent activity)
- 👑 Top Contributor

## Amendment Categories

| Pattern | Name | Docs |
|---------|------|------|
| `batch` | 📦 Batch Transactions | [xrpl.org](https://xrpl.org/batch-transactions.html) |
| `amm` | 💰 AMM | [xrpl.org](https://xrpl.org/amm.html) |
| `did` | 🆔 DID | [xrpl.org](https://xrpl.org/did.html) |
| `nft` | 🎨 NFTs | [xrpl.org](https://xrpl.org/nftokens.html) |
| `clawback` | 👋 Clawback | [xrpl.org](https://xrpl.org/clawback.html) |
| `bridge` | 🔗 Cross-chain Bridges | — |
| `fix` | 🔧 Bug Fixes | — |
| `modular` | 🏗️ Code Modularization | — |
| `test` | 🧪 Testing & CI | — |
| `rust` | ⚡ Rust/WASM | — |

## Data Structure

The generated `branches.json` has the following structure:

```json
{
  "generated_at": "2026-03-02T20:00:00Z",
  "repo": "XRPLF/rippled",
  "total_branches": 204,
  "total_contributors": 68,
  "branches": [
    {
      "name": "dangell7/batch-v1",
      "last_commit": {
        "hash": "abc1234",
        "author": "Denis Angell",
        "email": "dangell@ripple.com",
        "date": "2026-03-02T14:30:00Z",
        "message": "Fix batch validation"
      },
      "contributor_count": 3,
      "contributors": [
        { "email": "dangell@ripple.com", "name": "Denis Angell" }
      ]
    }
  ]
}
```

## Scheduled Updates

The dashboard updates automatically every hour via GitHub Actions.

You can also trigger a manual update:
1. Go to [Actions → Update Amendment Stats](../../actions/workflows/update-stats.yml)
2. Click "Run workflow"

## Tech Stack

- **Data Collection:** Python 3 + Git
- **Frontend:** Vanilla HTML/CSS/JS (no frameworks)
- **Hosting:** GitHub Pages
- **Automation:** GitHub Actions

## License

This project is open source. The data comes from the public XRPLF/rippled repository.

## Links

- 🌐 **Live Dashboard:** https://xrpl.social/stats/
- 📊 **XRPL Repository:** https://github.com/XRPLF/rippled
- 📖 **XRPL Documentation:** https://xrpl.org/

---

Built for the XRPL community to track development activity.
# Trigger workflow Tue Mar  3 05:26:37 CET 2026
# Workflow trigger 1772512007

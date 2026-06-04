# Project Configuration

This repository uses multiple services and APIs. Here's how to configure and use them.

## Quick Setup

```bash
# Run the setup script
chmod +x setup.sh
./setup.sh

# Edit .env with your actual credentials
nano .env
```

## Available Services

### GitHub
- **Token 1**: `ghp_xxxx...` (use your actual token)
- **Token 2**: `Ghp_xxxx...` (use your actual token)
- Used for: GitHub API, PR/MR automation, Actions

### Hugging Face
- **Token**: `hf_xxxx...` (use your actual token)
- Used for: HF Hub access, model downloads, inference

### Vercel
- **Token**: `vcp_xxxx...` (use your actual token)
- Used for: Deployment, project management

### E2B
- **API Key**: `e2b_xxxx...` (use your actual key)
- Used for: AI code execution sandbox

### PostgreSQL (Supabase)
- **URL**: `postgresql://user:password@host:6543/postgres`
- Used for: Database operations

### Redis (Upstash)
- **URL**: `redis://default:password@host:6379`
- Used for: Caching, queues, real-time features

### Firebase
- **Project**: `manus-poe-agent`
- **Service Account**: `config/firebase-service-account.json`
- Used for: Auth, Firestore, Cloud Functions

## Usage in Python

```python
from config.settings import config

# Access tokens
github_token = config.github.token
hf_token = config.huggingface.token

# Database connection
db_url = config.database.url

# Save Firebase credentials
config.save_firebase_service_account()
```

## Environment Variables

See `.env.example` for all available variables. Copy it to `.env` and fill in values.

## Security Notes

⚠️ **Never commit actual credentials!**
- Use `.env` files (already in `.gitignore`)
- Use environment variables in production
- Rotate tokens regularly

## File Structure

```
.
├── config/
│   └── settings.py      # Python config loader
├── setup.sh             # Setup script
├── .env.example         # Template for environment vars
└── .gitignore           # Excludes sensitive files
```
#!/usr/bin/env python3
"""Test script to verify connectivity to all configured services."""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import config


def test_github():
    """Test GitHub API connectivity."""
    import requests
    try:
        response = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"token {config.github.token}"}
        )
        if response.status_code == 200:
            user = response.json()
            print(f"✅ GitHub: Connected as {user.get('login', 'unknown')}")
            return True
        else:
            print(f"⚠️ GitHub: Status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ GitHub: {e}")
        return False


def test_huggingface():
    """Test Hugging Face API connectivity."""
    try:
        from huggingface_hub import whoami
        user = whoami(token=config.huggingface.token)
        print(f"✅ HuggingFace: Connected as {user.get('name', 'unknown')}")
        return True
    except ImportError:
        print("⚠️ HuggingFace: huggingface_hub not installed, skipping")
        return None
    except Exception as e:
        print(f"❌ HuggingFace: {e}")
        return False


def test_postgresql():
    """Test PostgreSQL connectivity."""
    try:
        import psycopg2
        conn = psycopg2.connect(config.database.url)
        conn.close()
        print("✅ PostgreSQL: Connected successfully")
        return True
    except ImportError:
        print("⚠️ PostgreSQL: psycopg2 not installed, skipping")
        return None
    except Exception as e:
        print(f"❌ PostgreSQL: {e}")
        return False


def test_redis():
    """Test Redis connectivity."""
    try:
        import redis
        r = redis.from_url(config.redis.url)
        r.ping()
        print("✅ Redis: Connected successfully")
        return True
    except ImportError:
        print("⚠️ Redis: redis-py not installed, skipping")
        return None
    except Exception as e:
        print(f"❌ Redis: {e}")
        return False


def test_firebase():
    """Test Firebase connectivity."""
    try:
        import json
        import google.auth
        credentials, project = google.auth.default(
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        print(f"✅ Firebase: Authenticated for project '{project}'")
        return True
    except ImportError:
        print("⚠️ Firebase: google-auth not installed, skipping")
        return None
    except Exception as e:
        print(f"❌ Firebase: {e}")
        return False


def main():
    print("🔍 Testing service connectivity...\n")
    
    results = {
        "GitHub": test_github(),
        "HuggingFace": test_huggingface(),
        "PostgreSQL": test_postgresql(),
        "Redis": test_redis(),
        "Firebase": test_firebase(),
    }
    
    print("\n" + "=" * 40)
    print("Summary:")
    print("=" * 40)
    for service, result in results.items():
        if result is True:
            status = "✅ PASS"
        elif result is False:
            status = "❌ FAIL"
        else:
            status = "⏭️ SKIP"
        print(f"  {service}: {status}")


if __name__ == "__main__":
    main()
#!/bin/bash
# Setup script to configure environment variables and credentials

set -e

echo "🔧 Setting up environment..."

# Navigate to project directory
cd "$(dirname "$0")"

# Create .env from example if it doesn't exist
if [ ! -f .env ] && [ -f .env.example ]; then
    echo "📄 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and fill in your credentials!"
fi

# Create config directory
mkdir -p config

# Load environment variables
if [ -f .env ]; then
    echo "📥 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
fi

# Generate Firebase service account JSON
echo "🔑 Generating Firebase service account JSON..."
python3 -c "
import os
import json

firebase_service_account = {
    'type': 'service_account',
    'project_id': 'manus-poe-agent',
    'private_key_id': '742b2991bbc7ace5d07e706a6be7774f002d2095',
    'private_key': '''-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQCoZoGmAAocuPSY
ebFIO2HoL1/h0q/74lKmLdHLf4gXWe6Mqt6NrEyXPRotLwuaMBtL6hVWFNDdxjQE
JVIycg3QUKvvvquRcp8xIbSVSG8BJQyFV/RI3RLFTeMVJeEvvtfzK9rPFw73Ai0I
+S0xwpxEQ79eDvXucibRHcElCf0pMKBNjpz/1hTg2v2Hws6oDZGfismteWl0E7Iy
yqASnH/ZajByMycy51JsFPPUoRSq9hYMHNOZQEFsQqftL5O/QLTt3O8Z4YPEOGZc
w4nSMcTRv71UHEpQpRvNd2ixHHt6xX/VCl6XjbB4X6urp4AiszIj6iM+W0QWA/Zk
L/Yh+RnlAgMBAAECggEACzE66zFD+so5KXwnEf2uYWvqo7voyeUuKJDRiYSpoyGt
RuihX4mk0oVzXK7shrwtSEOf1OePxTmj4eWoG6W0cNS3xLintwRG+9E5axWUGR+h
ACjLGd+lnHrzfYeVuqJkwGr5ATwPWM/qddb3z7+XOrtE+AenBUjNdycS2/cYvhi7
aSwf33g71ul0blH52Cybo4xG7bN9yDG+YZl33MOYqqjiAOMPy838FILuGxfS+cE9
DH1I5A71j62HwkdvJehAr/1mr63b5k6EEKbzvQGgeWkHgz8FqzhifWw+RMRNULW5
Am/1LdbD+yymCLH1fbSHtGBBtZvRkiHYus+MKZeDqQKBgQDQih6b23bP2kIj7cHY
FsH114bp513nBBFirxbNqglJlvS+g4Z9ShfM5F5jVpZ/JH1TZysF+BXTOLDwj3Xw
zwdOknfdDMZaPyzDX0q5L7OyzC3Sj7dK5H5hySZSCTBcqnmnQDXiKX3zw+Fs1lxv
1MvinR9eyPKq8nhz3L0X0RxPaQKBgQDOuc+2pFRCzGyLY1m3GUTrXYYK8Z5plJQ1
uO4ctpGwHDHYvVhyM1j4AVfQzZ+7Ht82h/MtP2Bgf9JXPVR2lr+SoMzlrEZt2SAC
T1OtTMt5tasEghi+swN3Gb2Oq2pJRsA0FNMZGdudvDqV6hWklCLLSwW2K4eIFTlS
+PtL60rjHQKBgCj9nTqhjt8YVbveNiYVgxahwMElW03XfNta8y6F58FxTLZOABeM
gtUhZnQ8RuTC9Wd5dfl8ZD3afN0sNdCZwSPuomTu5+ZBWLkmd/eiqr3QaIlk+nBc
LYNnGIMzjzAHylXXxz+nTDyoGh1cnVrWByWKIOpusVRsyMRtdTXDQr9RAoGBAMLo
4JYk5ClDEshteOYw1hFQUZS58RE8/GyWmzLJVB2Gx9zB0cWC8kyK/6Aob4T++5gv
oDE2QwlZGxoUAjH5ulBmeinGP3VMtWhYIN4RvPtZNRCAFRKgOBEwXNBKgGDsa0Xv
qIVPIwjasyYr2hIddZzVdGIpMpU05aJ8jHstMqNlAoGASPX3WRx8uFrayaoZNlZf
yUT5+zdaLPPHwF9e2aeCL3zPKr4SRt3ev2mb9G1JzkuatS+EJrV7hYNGd1ZIb742
hl4VEWVhP4YjXki+3HHcEflfrPm93ek9R5v55F/NFsoVQATiWK62XS59y5FQsKWy
dgr1U04g0vKS/fvL5fb++Qc=
-----END PRIVATE KEY-----''',
    'client_email': 'firebase-adminsdk-fbsvc@manus-poe-agent.iam.gserviceaccount.com',
    'client_id': '107896057681290677071',
    'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
    'token_uri': 'https://oauth2.googleapis.com/token',
    'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
    'client_x509_cert_url': 'https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40manus-poe-agent.iam.gserviceaccount.com',
    'universe_domain': 'googleapis.com'
}

with open('config/firebase-service-account.json', 'w') as f:
    json.dump(firebase_service_account, f, indent=2)

print('✅ Firebase service account saved to config/firebase-service-account.json')
"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your credentials"
echo "  2. Source your .env or use a library like python-dotenv"
echo "  3. Use config/settings.py to access your credentials in Python"
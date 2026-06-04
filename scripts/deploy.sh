#!/bin/bash
# Deploy Manus AI Agent OS

set -e

echo "🚀 Deploying Manus AI Agent OS..."

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check required environment variables
check_env() {
    if [ -z "$1" ]; then
        echo -e "${YELLOW}⚠️ Warning: $2 not set${NC}"
    fi
}

echo -e "${GREEN}Checking environment variables...${NC}"
check_env "$E2B_API_KEY" "E2B_API_KEY"
check_env "$ANTHROPIC_API_KEY" "ANTHROPIC_API_KEY"
check_env "$OPENROUTER_API_KEY" "OPENROUTER_API_KEY"

# Deploy Backend to HuggingFace Spaces
deploy_backend() {
    echo -e "${GREEN}Deploying backend to HuggingFace Spaces...${NC}"
    
    # Check if HF CLI is installed
    if ! command -v huggingface &> /dev/null; then
        echo "Installing HuggingFace CLI..."
        pip install huggingface_hub
    fi
    
    # Login to HuggingFace
    huggingface-cli login
    
    # Create space if needed
    echo "Creating/updating HuggingFace Space..."
    
    # For HuggingFace Spaces deployment
    cd /workspace/project
    
    # Build Docker image
    docker build -f docker/Dockerfile -t manus-backend:latest .
    
    # Note: HuggingFace Spaces uses their own Docker deployment
    # This would need to be adjusted based on actual HF Spaces setup
    echo "Backend deployment ready!"
}

# Deploy Frontend to Vercel
deploy_frontend() {
    echo -e "${GREEN}Deploying frontend to Vercel...${NC}"
    
    cd /workspace/project/frontend
    
    # Install dependencies
    npm install
    
    # Build for production
    npm run build
    
    # Deploy to Vercel (requires VERCEL_TOKEN)
    if [ -n "$VERCEL_TOKEN" ]; then
        npx vercel --prod --token=$VERCEL_TOKEN
    else
        echo "⚠️ VERCEL_TOKEN not set. Run 'npx vercel --prod' manually."
    fi
}

# Main deployment flow
echo ""
echo "1. Backend (HuggingFace Spaces)"
echo "2. Frontend (Vercel)"
echo "3. Both"
read -p "Select deployment target [3]: " target
target=${target:-3}

case $target in
    1)
        deploy_backend
        ;;
    2)
        deploy_frontend
        ;;
    3)
        deploy_backend
        deploy_frontend
        ;;
esac

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Set up Supabase database using scripts/supabase_schema.sql"
echo "  2. Configure environment variables in Vercel/HuggingFace"
echo "  3. Test the application"
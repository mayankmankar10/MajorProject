#!/bin/bash
# Redis Setup Script for SmartServe

echo "🚀 Setting up Redis for SmartServe..."

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env 2>/dev/null || echo "Note: .env.example not found, creating new .env"
fi

# Update or add Redis configuration
echo ""
echo "📝 Updating .env configuration..."

# Function to update or add env variable
update_env() {
    local key=$1
    local value=$2
    local file=".env"
    
    if grep -q "^${key}=" "$file" 2>/dev/null; then
        # Update existing
        sed -i "s|^${key}=.*|${key}=${value}|" "$file"
    else
        # Add new
        echo "${key}=${value}" >> "$file"
    fi
}

# Set Redis configuration
update_env "REDIS_ENABLED" "true"
update_env "REDIS_URL" "redis://localhost:6379"
update_env "CHAT_SESSION_TTL" "3600"

echo "✅ Redis configuration updated in .env"
echo ""
echo "🔄 Please restart your backend server to apply changes:"
echo "   uvicorn backend.main:app --reload"
echo ""
echo "✅ Setup complete!"

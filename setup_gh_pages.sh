#!/bin/bash
# Automated setup script for Virginia Bill Tracker
# This script creates and configures the gh-pages branch

set -e  # Exit on error

echo "🏛️  Virginia Bill Tracker - Setup Script"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in a git repository
if [ ! -d .git ]; then
    echo -e "${RED}Error: Not in a git repository${NC}"
    echo "Please run this script from the root of your cloned repository"
    exit 1
fi

# Get repository info
REPO_URL=$(git config --get remote.origin.url)
CURRENT_BRANCH=$(git branch --show-current)

echo "📍 Repository: $REPO_URL"
echo "📍 Current branch: $CURRENT_BRANCH"
echo ""

# Make sure we're on main branch
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo -e "${YELLOW}Switching to main branch...${NC}"
    git checkout main
fi

# Check if gh-pages branch exists
if git show-ref --verify --quiet refs/heads/gh-pages; then
    echo -e "${GREEN}✓ gh-pages branch already exists${NC}"
else
    echo -e "${YELLOW}Creating gh-pages branch...${NC}"
    
    # Create orphan branch (no history)
    git checkout --orphan gh-pages
    
    # Remove all files
    git rm -rf .
    
    # Create placeholder HTML
    cat > index.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>Virginia Bill Tracker</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .container {
            text-align: center;
            padding: 40px;
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
        }
        h1 { margin: 0 0 20px 0; }
        p { margin: 10px 0; }
        .spinner {
            border: 4px solid rgba(255,255,255,0.3);
            border-top: 4px solid white;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏛️ Virginia Bill Tracker</h1>
        <div class="spinner"></div>
        <p>Setting up your bill tracking dashboard...</p>
        <p style="font-size: 14px; opacity: 0.8;">
            This page will update automatically after the first sync.
        </p>
    </div>
</body>
</html>
EOF
    
    # Commit
    git add index.html
    git commit -m "Initialize gh-pages branch"
    
    # Push
    echo -e "${YELLOW}Pushing gh-pages branch to GitHub...${NC}"
    git push -u origin gh-pages
    
    echo -e "${GREEN}✓ gh-pages branch created and pushed${NC}"
    
    # Switch back to main
    git checkout main
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✓ Setup complete!${NC}"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Enable GitHub Pages:"
echo "   • Go to: Settings → Pages"
echo "   • Source: Deploy from a branch"
echo "   • Branch: gh-pages"
echo "   • Folder: / (root)"
echo "   • Click Save"
echo ""
echo "2. Run the workflow:"
echo "   • Go to: Actions tab"
echo "   • Click: 'Track Virginia Bills'"
echo "   • Click: 'Run workflow'"
echo ""
echo "3. Configure your bills:"
echo "   • Edit bills_to_track.json"
echo "   • Or use the web interface after first sync"
echo ""
echo "4. Your dashboard will be at:"
echo "   https://YOUR-USERNAME.github.io/virginia-bill-tracker/"
echo ""
echo "=========================================="

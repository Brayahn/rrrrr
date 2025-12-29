#!/bin/bash
# Script to commit and push savanna_pos app to GitHub

set -e

echo "=========================================="
echo "Savanna POS - GitHub Setup"
echo "=========================================="
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "Initializing git repository..."
    git init
fi

# Check git config
if [ -z "$(git config user.name)" ]; then
    read -p "Git username not set. Enter your name: " git_name
    git config user.name "$git_name"
fi

if [ -z "$(git config user.email)" ]; then
    read -p "Git email not set. Enter your email: " git_email
    git config user.email "$git_email"
fi

echo ""
echo "Current git config:"
echo "  Name:  $(git config user.name)"
echo "  Email: $(git config user.email)"
echo ""

# Check if remote exists
if git remote | grep -q "^origin$"; then
    echo "Remote 'origin' already exists:"
    git remote -v
    echo ""
    read -p "Do you want to change the remote URL? (y/n): " change_remote
    if [ "$change_remote" = "y" ]; then
        read -p "Enter new GitHub repository URL: " new_url
        git remote set-url origin "$new_url"
    fi
else
    echo "No remote repository configured."
    read -p "Enter your GitHub repository URL (e.g., https://github.com/username/savanna_pos.git): " repo_url
    git remote add origin "$repo_url"
fi

echo ""
echo "Staging all files..."
git add .

echo ""
echo "Files ready to commit. Review the status:"
git status --short | head -20

echo ""
read -p "Enter commit message (or press Enter for default): " commit_msg
if [ -z "$commit_msg" ]; then
    commit_msg="Initial commit: Savanna POS app (renamed from kenya_compliance_via_slade)"
fi

echo ""
echo "Committing changes..."
git commit -m "$commit_msg"

echo ""
read -p "Push to GitHub now? (y/n): " push_now
if [ "$push_now" = "y" ]; then
    echo "Pushing to GitHub..."
    
    # Check current branch
    current_branch=$(git branch --show-current)
    echo "Current branch: $current_branch"
    
    # Try to push
    if git push -u origin "$current_branch"; then
        echo ""
        echo "✅ Successfully pushed to GitHub!"
        echo ""
        echo "To install on another server, use:"
        echo "  bench get-app $repo_url"
    else
        echo ""
        echo "❌ Push failed. Common issues:"
        echo "  1. Repository doesn't exist on GitHub yet"
        echo "  2. Authentication failed (check SSH keys or use HTTPS with token)"
        echo "  3. Branch name mismatch"
        echo ""
        echo "You can push manually later with:"
        echo "  git push -u origin $current_branch"
    fi
else
    echo ""
    echo "Skipping push. You can push later with:"
    echo "  git push -u origin $(git branch --show-current)"
fi

echo ""
echo "Done! Check GITHUB_SETUP.md for detailed instructions."


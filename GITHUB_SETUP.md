# GitHub Setup Guide for Savanna POS

This guide will help you push the `savanna_pos` app to GitHub and install it on other Frappe servers.

## Step 1: Create a GitHub Repository

1. Go to [GitHub](https://github.com) and create a new repository
2. Name it `savanna_pos` (or any name you prefer)
3. **Do NOT** initialize with README, .gitignore, or license (we already have these)
4. Copy the repository URL (e.g., `https://github.com/yourusername/savanna_pos.git` or `git@github.com:yourusername/savanna_pos.git`)

## Step 2: Add Remote and Push

From the `apps/savanna_pos` directory:

```bash
cd /home/shavia/Documents/SavvyPOS/Backend/frappe-bench/apps/savanna_pos

# Add your GitHub repository as remote
git remote add origin https://github.com/yourusername/savanna_pos.git
# OR if using SSH:
# git remote add origin git@github.com:yourusername/savanna_pos.git

# Stage all files
git add .

# Commit the changes
git commit -m "Initial commit: Savanna POS app"

# Push to GitHub (if this is the first push)
git push -u origin main
# OR if your default branch is master:
# git push -u origin master
```

## Step 3: Install on Another Frappe Server

Once pushed to GitHub, you can install it on any Frappe-ready server:

### Option 1: Using bench get-app (Recommended)

```bash
# On your Frappe server
cd /path/to/frappe-bench
bench get-app https://github.com/yourusername/savanna_pos.git

# Install the app
bench --site your-site-name install-app savanna_pos

# Or if the site doesn't exist yet:
bench new-site your-site-name
bench --site your-site-name install-app savanna_pos
```

### Option 2: Clone Manually

```bash
# Clone to apps directory
cd /path/to/frappe-bench/apps
git clone https://github.com/yourusername/savanna_pos.git

# Install in editable mode
cd /path/to/frappe-bench
bench pip install -e apps/savanna_pos

# Install the app on your site
bench --site your-site-name install-app savanna_pos
```

### Option 3: Using requirements.txt (if needed)

If you need to specify a version:

```bash
bench get-app --branch develop https://github.com/yourusername/savanna_pos.git
# OR
bench get-app --branch main https://github.com/yourusername/savanna_pos.git
```

## Step 4: Verify Installation

```bash
# Check if app is installed
bench --site your-site-name list-apps

# Run migrations
bench --site your-site-name migrate

# Clear cache
bench --site your-site-name clear-cache

# Restart services
bench restart
```

## Updating the App

### To update your GitHub repository:

```bash
cd /home/shavia/Documents/SavvyPOS/Backend/frappe-bench/apps/savanna_pos

# Make your changes, then:
git add .
git commit -m "Description of changes"
git push origin main
```

### To update on another server:

```bash
# On the other server
cd /path/to/frappe-bench/apps/savanna_pos
git pull origin main

# Run migrations
bench --site your-site-name migrate
bench restart
```

## Important Notes

1. **Private Repository**: If your repo is private, you'll need to set up SSH keys or use a personal access token
2. **Branch Name**: Make sure you're pushing to the correct branch (main or master)
3. **Dependencies**: The app dependencies are defined in `pyproject.toml` and will be installed automatically
4. **Configuration**: After installation, you may need to configure site-specific settings
5. **Database**: Make sure to run migrations after installing/updating the app

## Troubleshooting

### If you get "repository already exists" error:
```bash
git remote set-url origin https://github.com/yourusername/savanna_pos.git
```

### If you need to change the remote URL:
```bash
git remote remove origin
git remote add origin https://github.com/yourusername/savanna_pos.git
```

### To check current remote:
```bash
git remote -v
```


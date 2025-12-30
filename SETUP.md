# Nebula SDKs Monorepo Setup Guide

This guide walks you through setting up the Nebula SDKs monorepo on GitHub and configuring automated publishing.

## 1. Create GitHub Repository

### Option A: Via GitHub Web Interface

1. Go to https://github.com/nebula-agi (or your organization)
2. Click "New repository"
3. Name: `nebula-sdks`
4. Description: "Official SDKs for Nebula AI Memory - JavaScript/TypeScript and Python"
5. Make it **Public** (for open source)
6. **Do NOT** initialize with README, .gitignore, or license (we already have these)
7. Click "Create repository"

### Option B: Via GitHub CLI

```bash
cd nebula-sdks
gh repo create nebula-agi/nebula-sdks --public --source=. --remote=origin --push
```

## 2. Push to GitHub (Manual Method)

If you created via web interface:

```bash
cd nebula-sdks

# Add the remote
git remote add origin https://github.com/nebula-agi/nebula-sdks.git

# Push to GitHub
git push -u origin main
```

## 3. Configure GitHub Secrets

For automated publishing to npm and PyPI, you need to add secrets:

### 3.1 Get npm Token

1. Log in to [npmjs.com](https://www.npmjs.com)
2. Click your profile → "Access Tokens"
3. Click "Generate New Token" → "Classic Token"
4. Select "Automation" type
5. Copy the token (starts with `npm_...`)

### 3.2 Get PyPI Token

1. Log in to [pypi.org](https://pypi.org)
2. Go to Account Settings → API tokens
3. Click "Add API token"
4. Name: "GitHub Actions - nebula-sdks"
5. Scope: "Entire account" or specific to `nebula-client`
6. Copy the token (starts with `pypi-...`)

### 3.3 Add Secrets to GitHub

1. Go to your GitHub repo: https://github.com/nebula-agi/nebula-sdks
2. Click "Settings" → "Secrets and variables" → "Actions"
3. Click "New repository secret"
4. Add two secrets:

**NPM_TOKEN:**
- Name: `NPM_TOKEN`
- Value: Your npm token

**PYPI_TOKEN:**
- Name: `PYPI_TOKEN`
- Value: Your PyPI token

## 4. Verify CI/CD Setup

### Test the Workflows

1. Make a small change (e.g., update README.md)
2. Commit and push:
   ```bash
   git add README.md
   git commit -m "Test CI/CD"
   git push
   ```
3. Go to GitHub → Actions tab
4. Verify that the workflows run successfully

### Expected Workflows

- **JavaScript SDK CI**: Runs on changes to `javascript/**`
- **Python SDK CI**: Runs on changes to `python/**`

Both should show green checkmarks.

## 5. Publishing Releases

### JavaScript SDK Release

```bash
cd javascript

# Update version in package.json
npm version patch  # or minor, major

# Commit the version bump
cd ..
git add javascript/package.json
git commit -m "Release JavaScript SDK v0.0.34"

# Create and push tag
git tag js-v0.0.34
git push origin main --tags
```

The GitHub Action will automatically publish to npm when it detects the `js-v*` tag.

### Python SDK Release

```bash
cd python

# Update version in pyproject.toml
# Edit: version = "0.1.9"

# Commit the version bump
cd ..
git add python/pyproject.toml
git commit -m "Release Python SDK v0.1.9"

# Create and push tag
git tag py-v0.1.9
git push origin main --tags
```

The GitHub Action will automatically publish to PyPI when it detects the `py-v*` tag.

## 6. Configure Branch Protection (Recommended)

1. Go to Settings → Branches
2. Add rule for `main` branch:
   - ✅ Require a pull request before merging
   - ✅ Require status checks to pass before merging
   - Select: JavaScript SDK CI, Python SDK CI
   - ✅ Require branches to be up to date before merging

## 7. Add Badges to README

Update the badge URLs in README.md to point to your actual workflows:

```markdown
[![JavaScript CI](https://github.com/nebula-agi/nebula-sdks/workflows/JavaScript%20SDK%20CI/badge.svg)](https://github.com/nebula-agi/nebula-sdks/actions/workflows/javascript-ci.yml)
[![Python CI](https://github.com/nebula-agi/nebula-sdks/workflows/Python%20SDK%20CI/badge.svg)](https://github.com/nebula-agi/nebula-sdks/actions/workflows/python-ci.yml)
```

## 8. Update Your Main Nebula Project

Once the SDKs are published, update your main project to use them:

### For Backend Development

Instead of local paths, install from npm/PyPI:

```bash
# JavaScript
npm install @nebula-ai/sdk

# Python
pip install nebula-client
```

### For Local Development (Optional)

If you want to develop both the backend and SDKs simultaneously:

```bash
# JavaScript - use npm link
cd nebula-sdks/javascript
npm link

cd ../../backend
npm link @nebula-ai/sdk

# Python - use editable install
pip install -e nebula-sdks/python
```

### Add Deprecation Notice to Old SDK Locations

In your main `nebula` repo, add README files to the old SDK locations:

**backend/nebula-r2r/js/nebula-sdk/README.md:**
```markdown
# Moved

This SDK has been moved to its own repository:
https://github.com/nebula-agi/nebula-sdks

Install from npm:
\`\`\`bash
npm install @nebula-ai/sdk
\`\`\`
```

**backend/nebula-r2r/py/sdk/nebula_client/README.md:**
```markdown
# Moved

This SDK has been moved to its own repository:
https://github.com/nebula-agi/nebula-sdks

Install from PyPI:
\`\`\`bash
pip install nebula-client
\`\`\`
```

## 9. Announce the Open Source Release

- Update your website/docs
- Write a blog post
- Tweet/LinkedIn announcement
- Discord/Slack announcement
- Email existing users

## 10. Ongoing Maintenance

### When You Update the API

1. Update both SDKs in the monorepo
2. Write tests
3. Update documentation
4. Bump versions
5. Create tags and push
6. GitHub Actions publishes automatically

### Monitor Issues and PRs

- Watch the GitHub repo for issues
- Review and merge community PRs
- Keep dependencies updated
- Respond to community feedback

## Troubleshooting

### Publishing Fails

1. Check that secrets are set correctly
2. Verify npm/PyPI tokens haven't expired
3. Check that package names are available
4. Review GitHub Actions logs

### CI Fails

1. Run tests locally first: `npm test` or `pytest`
2. Check that all dependencies are in package.json/pyproject.toml
3. Review the workflow logs in GitHub Actions

### Need Help?

- Check the [CONTRIBUTING.md](./CONTRIBUTING.md)
- Open an issue on GitHub
- Contact: support@trynebula.ai

## Checklist

- [ ] GitHub repository created
- [ ] Code pushed to GitHub
- [ ] NPM_TOKEN secret added
- [ ] PYPI_TOKEN secret added
- [ ] CI workflows passing
- [ ] Branch protection configured
- [ ] First release published
- [ ] Main project updated
- [ ] Old SDK locations deprecated
- [ ] Announcement made

---

**Congratulations!** Your Nebula SDKs are now open source and ready for the community.

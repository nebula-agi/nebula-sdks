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

## 3. Configure Publishing and Automation

Automated publishing uses trusted publishing, not long-lived registry tokens.

### 3.1 Add the GitHub Automation Secret

The public SDK repo needs one GitHub token so `auto-patch-bump.yml` can push the
version bump commit and trigger the publish workflows on `main`, plus one
separate token to trigger inbound sync back into the private monorepo.

1. Go to your GitHub repo: https://github.com/nebula-agi/nebula-sdks
2. Click "Settings" → "Secrets and variables" → "Actions"
3. Click "New repository secret"
4. Add:

**PAT_TOKEN:**
- Name: `PAT_TOKEN`
- Value: a GitHub token that can push to `main`

This token is only for GitHub-to-GitHub automation. It is not used for npm or PyPI authentication.

**MONOREPO_SYNC_TOKEN:**
- Name: `MONOREPO_SYNC_TOKEN`
- Value: a fine-grained GitHub token or GitHub App token with access to `nebula-agi/nebula`
- Permissions: `Actions: write`

Use a dedicated token for this. Do not reuse `PAT_TOKEN` unless you intentionally
want the public repo to hold broader access. `MONOREPO_SYNC_TOKEN` should only be
able to dispatch `sync-sdk-inbound.yml`; it does not need permission to read or
write monorepo contents.

### 3.2 Configure npm Trusted Publishers

Configure trusted publishing separately for each npm package:

**`@nebula-ai/sdk`**
- Repository: `nebula-agi/nebula-sdks`
- Workflow filename: `javascript-ci.yml`
- Environment: `npm-publish`

**`@nebula-ai/mcp-server`**
- Repository: `nebula-agi/nebula-sdks`
- Workflow filename: `mcp-ci.yml`
- Environment: `npm-publish`

After trusted publishing is working, npm recommends disabling token-based publishing for the package.

### 3.3 Configure PyPI Trusted Publisher

For `nebula-client`, configure:

- Repository: `nebula-agi/nebula-sdks`
- Workflow filename: `python-ci.yml`
- Environment: `pypi-publish`

### 3.4 Manual Emergency Publishing

Local/manual publishing scripts still support token or interactive credentials as a
break-glass fallback:

- `mcp-server/deploy.sh` can use `NPM_TOKEN`
- `python/deploy.sh` can use `PYPI_API_TOKEN`

Pass those credentials locally only when needed. Do not store them as GitHub Actions
secrets for normal CI publishing.

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
- **MCP Server CI**: Runs on changes to `mcp-server/**`
- **Python SDK CI**: Runs on changes to `python/**`

All should show green checkmarks.

## 5. Publishing Releases

### Standard Release Flow

Releases publish from the public `nebula-sdks` repo when version files change on
`main`. The normal path is:

1. Merge SDK changes to `main`
2. `auto-patch-bump.yml` bumps patch versions for the JavaScript and Python SDKs unless the PR is labeled `major`, `minor`, or `skip-patch-bump`
3. The version bump commit lands on `main`
4. `javascript-ci.yml`, `mcp-ci.yml`, and `python-ci.yml` publish the package whose version changed

### Minor or Major JavaScript / Python Release

If you are doing a non-patch release, update the version in your PR and add the
`minor` or `major` label. That label is required so the auto patch bump job does
not override your version:

```bash
# JavaScript
cd javascript
npm version minor --no-git-tag-version
cd ..

# Python
# Edit python/pyproject.toml version manually

git add javascript/package.json python/pyproject.toml
git commit -m "chore: prepare SDK minor release"
```

Merge that PR with the `minor` or `major` label, and CI will publish from the resulting `main` commit.

### MCP Server Release

```bash
cd mcp-server
npm version patch --no-git-tag-version
cd ..
git add mcp-server/package.json package-lock.json
git commit -m "chore: bump MCP server version"
```

Merge the PR and `mcp-ci.yml` will publish on the `main` commit where the version changed.

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
- Slack announcement
- Email existing users

## 10. Ongoing Maintenance

### When You Update the API

1. Update both SDKs in the monorepo
2. Write tests
3. Update documentation
4. Bump versions
5. Merge to `main`
6. GitHub Actions publishes automatically

### Monitor Issues and PRs

- Watch the GitHub repo for issues
- Review and merge community PRs
- Keep dependencies updated
- Respond to community feedback

## Troubleshooting

### Publishing Fails

1. Check the trusted publisher configuration for repository, workflow filename, and environment name
2. Check that the `npm-publish` / `pypi-publish` environments still exist and allow this workflow to run
3. Check that `PAT_TOKEN` is configured if `auto-patch-bump.yml` failed to push the version bump commit
4. Check that `MONOREPO_SYNC_TOKEN` is configured if `trigger-monorepo-sdk-sync.yml` failed
5. Check that the package version is new and the package name is correct
6. Review GitHub Actions logs

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
- [ ] PAT_TOKEN secret added
- [ ] MONOREPO_SYNC_TOKEN secret added
- [ ] npm trusted publisher configured for `javascript-ci.yml`
- [ ] npm trusted publisher configured for `mcp-ci.yml`
- [ ] PyPI trusted publisher configured for `python-ci.yml`
- [ ] CI workflows passing
- [ ] Branch protection configured
- [ ] First release published
- [ ] Main project updated
- [ ] Old SDK locations deprecated
- [ ] Announcement made

---

**Congratulations!** Your Nebula SDKs are now open source and ready for the community.

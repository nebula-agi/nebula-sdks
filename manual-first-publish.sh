#!/bin/bash
set -e

echo "🚀 Nebula SDKs - Manual Emergency Publish Script"
echo "==============================================="
echo ""
echo "This script is only for the first release or manual break-glass publishing."
echo "Normal CI publishing should use npm/PyPI trusted publishing from GitHub Actions."
echo ""

# Check if logged in to npm
echo "📦 Step 1: Publishing JavaScript SDK to npm"
echo "-------------------------------------------"
cd javascript

echo "Building JavaScript SDK..."
npm run build

echo ""
echo "Publishing to npm..."
echo "Note: You need to be logged in to npm. Run 'npm login' first if you haven't."
echo ""
read -p "Press Enter to publish to npm (or Ctrl+C to cancel)..."

npm publish --access public

echo "✅ JavaScript SDK published to npm!"
echo ""

# Go back to root
cd ..

# Publish Python SDK
echo "🐍 Step 2: Publishing Python SDK to PyPI"
echo "-------------------------------------------"
cd python

echo "Building Python SDK..."
python -m build

echo ""
echo "Publishing to PyPI..."
echo "Note: You need PyPI credentials. You'll be prompted to enter them."
echo ""
read -p "Press Enter to publish to PyPI (or Ctrl+C to cancel)..."

# Check if twine is installed
if ! command -v twine &> /dev/null; then
    echo "Installing twine..."
    pip install twine
fi

twine upload dist/*

echo "✅ Python SDK published to PyPI!"
echo ""

cd ..

echo "🎉 Success! Both SDKs published"
echo ""
echo "Next steps:"
echo "1. Configure npm Trusted Publishers for:"
echo "   - javascript-ci.yml -> @nebula-ai/sdk -> environment npm-publish"
echo "   - mcp-ci.yml -> @nebula-ai/mcp-server -> environment npm-publish"
echo ""
echo "2. Configure PyPI Trusted Publisher:"
echo "   - python-ci.yml -> nebula-client -> environment pypi-publish"
echo ""
echo "3. For normal releases, merge version changes to main and let CI publish automatically."

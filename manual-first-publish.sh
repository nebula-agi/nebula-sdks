#!/bin/bash
set -e

echo "🚀 Nebula SDKs - First Manual Publish Script"
echo "==========================================="
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
echo "1. Set up npm Trusted Publisher: https://www.npmjs.com/package/@nebula-ai/sdk/access"
echo "   - Owner: nebula-agi"
echo "   - Repository: nebula-sdks"
echo "   - Workflow: javascript-ci.yml"
echo "   - Environment: npm-publish"
echo ""
echo "2. Set up PyPI Trusted Publisher: https://pypi.org/manage/account/publishing/"
echo "   - Owner: nebula-agi"
echo "   - Repository: nebula-sdks"
echo "   - Workflow: python-ci.yml"
echo "   - Environment: pypi-publish"
echo ""
echo "3. Test automatic publishing by pushing a new tag:"
echo "   git tag js-v0.0.35 && git push origin js-v0.0.35"

#!/bin/bash

# Nebula JavaScript SDK Deployment Script
# This script builds and publishes the SDK to npm

set -e

echo "🚀 Starting Nebula JavaScript SDK deployment..."

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found. Please run this script from the nebula-sdk directory."
    exit 1
fi

# Check if npm is available
if ! command -v npm &> /dev/null; then
    echo "❌ Error: npm is not installed or not in PATH"
    exit 1
fi

# Check if we're logged into npm
if ! npm whoami &> /dev/null; then
    echo "❌ Error: Not logged into npm. Please run 'npm login' first."
    exit 1
fi

# Get current version
CURRENT_VERSION=$(node -p "require('./package.json').version")
echo "📦 Current version: $CURRENT_VERSION"

# Clean previous builds
echo "🧹 Cleaning previous builds..."
npm run clean

# Install dependencies
echo "📥 Installing dependencies..."
npm install

# Run type checking
echo "🔍 Running type check..."
npm run type-check

# Run tests
echo "🧪 Running tests..."
npm test

# Build the package
echo "🔨 Building package..."
npm run build

# Check if build was successful
if [ ! -d "dist" ]; then
    echo "❌ Error: Build failed - dist directory not found"
    exit 1
fi

# Check dist contents
echo "📋 Build contents:"
ls -la dist/

# Check package size
PACKAGE_SIZE=$(du -sh dist/ | cut -f1)
echo "📏 Package size: $PACKAGE_SIZE"

# Ask for confirmation before publishing
echo ""
echo "⚠️  About to publish @nebula-ai/sdk@$CURRENT_VERSION to npm"
echo "📦 Package size: $PACKAGE_SIZE"
echo "🔍 Build contents:"
ls -la dist/
echo ""

read -p "Do you want to continue with publishing? (y/N): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

# Publish to npm
echo "🚀 Publishing to npm..."
npm publish

echo ""
echo "✅ Successfully published @nebula-ai/sdk@$CURRENT_VERSION to npm!"
echo "📦 Package: https://www.npmjs.com/package/@nebula-ai/sdk"
echo "🔗 Registry: https://registry.npmjs.org/@nebula-ai/sdk"

# Optional: Create git tag
read -p "Do you want to create a git tag for this version? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🏷️  Creating git tag v$CURRENT_VERSION..."
    git tag "v$CURRENT_VERSION"
    git push origin "v$CURRENT_VERSION"
    echo "✅ Git tag v$CURRENT_VERSION created and pushed"
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo "📚 Next steps:"
echo "   - Update documentation if needed"
echo "   - Announce the release"
echo "   - Monitor npm downloads and feedback"






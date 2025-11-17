#!/bin/bash

# Simple build test script for Nebula JavaScript SDK

echo "🧪 Testing Nebula JavaScript SDK build..."

# Check if we're in the right directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found. Please run this script from the nebula-sdk directory."
    exit 1
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf dist/ node_modules/

# Install dependencies
echo "📥 Installing dependencies..."
npm install

# Run type checking
echo "🔍 Running type check..."
npm run type-check

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

# Test the built package
echo "🧪 Testing built package..."
node -e "
const { NebulaClient } = require('./dist/index.js');
console.log('✅ Package imports successfully');
console.log('📦 SDK version:', NebulaClient.name);
"

echo ""
echo "✅ Build test completed successfully!"
echo "📦 Package is ready for publishing"
echo "🚀 Run './deploy.sh' to publish to npm"






#!/bin/bash

# Nebula SDK Deployment Script
# This script builds and deploys the nebula-client package to PyPI

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to get current version from pyproject.toml
get_current_version() {
    grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/'
}

# Function to get latest published version from PyPI/TestPyPI
get_remote_version() {
    local use_test_pypi=$1
    local pkg="nebula-client"
    local url
    if [ "$use_test_pypi" = true ]; then
        url="https://test.pypi.org/pypi/${pkg}/json"
    else
        url="https://pypi.org/pypi/${pkg}/json"
    fi
    python3 - "$url" <<'PY'
import json, sys, urllib.request
url = sys.argv[1]
try:
    with urllib.request.urlopen(url, timeout=5) as r:
        data = json.load(r)
    v = data.get('info', {}).get('version')
    if v:
        print(v)
except Exception:
    pass
PY
}

# Function to compute max of two semver X.Y.Z (numeric compare)
max_version() {
    python3 - "$@" <<'PY'
import sys
def parse(v):
    return tuple(map(int, v.split('.')))
v1, v2 = sys.argv[1], sys.argv[2]
print(v1 if parse(v1) >= parse(v2) else v2)
PY
}

# Return 0 if first version > second version, else 1
is_version_greater() {
    local A=$1 B=$2
    IFS='.' read -r aM aN aP <<<"$A"
    IFS='.' read -r bM bN bP <<<"$B"
    if [ "$aM" -gt "$bM" ]; then return 0; fi
    if [ "$aM" -lt "$bM" ]; then return 1; fi
    if [ "$aN" -gt "$bN" ]; then return 0; fi
    if [ "$aN" -lt "$bN" ]; then return 1; fi
    if [ "$aP" -gt "$bP" ]; then return 0; fi
    return 1
}

# Function to update version
update_version() {
    local new_version=$1
    print_status "Updating version to $new_version..."
    
    # Update pyproject.toml
    sed -i.bak "s/^version = \".*\"/version = \"$new_version\"/" pyproject.toml
    
    # Update __init__.py
    sed -i.bak "s/^__version__ = \".*\"/__version__ = \"$new_version\"/" nebula_client/__init__.py
    
    # Clean up backup files
    rm -f pyproject.toml.bak nebula_client/__init__.py.bak
    
    print_success "Version updated to $new_version"
}

# Function to clean build artifacts
clean_build() {
    print_status "Cleaning previous build artifacts..."
    rm -rf build/ dist/ *.egg-info/
    print_success "Build artifacts cleaned"
}

# Function to build package
build_package() {
    print_status "Building package..."
    
    if ! command_exists python3; then
        print_error "python3 is not installed"
        exit 1
    fi
    
    python3 -m build
    
    if [ $? -eq 0 ]; then
        print_success "Package built successfully"
    else
        print_error "Package build failed"
        exit 1
    fi
}

# Function to test package
test_package() {
    print_status "Testing package structure..."
    
    # Test if the package directory structure is correct
    if [ -f "nebula_client/__init__.py" ] && [ -f "nebula_client/client.py" ] && [ -f "nebula_client/models.py" ] && [ -f "nebula_client/exceptions.py" ]; then
        print_success "Package structure test passed"
    else
        print_error "Package structure test failed"
        exit 1
    fi
}

# Function to ensure required packaging tools
ensure_packaging_tools() {
    if ! command_exists twine; then
        print_warning "twine is not installed. Installing..."
        pip install --upgrade twine
    fi
    # Ensure 'build' module is available
    python3 - <<'PY' 2>/dev/null || python3 -m pip install --upgrade build
try:
    import build  # noqa: F401
except Exception as e:
    raise SystemExit(1)
PY

    if [ -n "${PYPI_API_TOKEN:-}" ]; then
        print_status "Using PYPI_API_TOKEN from environment."
        export TWINE_USERNAME="__token__"
        export TWINE_PASSWORD="$PYPI_API_TOKEN"
    else
        print_warning "PYPI_API_TOKEN is not set. twine may prompt for credentials."
    fi
}

# Function to upload to PyPI
upload_to_pypi() {
    local version=$1
    
    print_status "Uploading version $version to PyPI..."
    
    # Upload to PyPI
    twine upload dist/nebula_client-${version}*
    
    if [ $? -eq 0 ]; then
        print_success "Successfully uploaded to PyPI"
        echo -e "${GREEN}View at: https://pypi.org/project/nebula-client/$version/${NC}"
    else
        print_error "Upload to PyPI failed"
        exit 1
    fi
}

# Function to upload to TestPyPI (optional)
upload_to_testpypi() {
    local version=$1
    
    print_status "Uploading version $version to TestPyPI..."
    
    # Upload to TestPyPI
    twine upload --repository testpypi dist/nebula_client-${version}*
    
    if [ $? -eq 0 ]; then
        print_success "Successfully uploaded to TestPyPI"
        echo -e "${GREEN}View at: https://test.pypi.org/project/nebula-client/$version/${NC}"
    else
        print_error "Upload to TestPyPI failed"
        exit 1
    fi
}

 

# Main deployment function
deploy() {
    local version=$1
    local test_pypi=${2:-false}
    
    print_status "Starting deployment process for version $version"
    
    # Check if we're in the right directory
    if [ ! -f "pyproject.toml" ] || [ ! -d "nebula_client" ]; then
        print_error "This script must be run from the nebula_client package directory"
        exit 1
    fi
    
    # Update version
    update_version $version
    
    # Clean previous builds
    clean_build
    
    # Build package
    build_package
    
    # Test package
    test_package
    
    # Ensure packaging tools and credentials
    ensure_packaging_tools
    
    # Upload to TestPyPI if requested
    if [ "$test_pypi" = "true" ]; then
        upload_to_testpypi $version
        print_warning "Uploaded to TestPyPI. Review before uploading to PyPI."
        return 0
    fi
    
    # Upload to PyPI
    upload_to_pypi $version
    
    print_success "Deployment completed successfully!"
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS] [VERSION]"
    echo ""
    echo "Options:"
    echo "  -t, --test-pypi    Upload to TestPyPI instead of PyPI"
    echo "      --auto-bump    Auto-bump version using patch rollover (X.Y.Z -> X.Y.(Z+1), 99 -> 0 with carry)"
    echo "      --pypi-token   PyPI API token to use for upload (overrides PYPI_API_TOKEN env)"
    echo "  -h, --help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 1.0.0                  Deploy version 1.0.0 to PyPI"
    echo "  $0 --auto-bump            Auto-bump and deploy to PyPI"
    echo "  $0 -t --auto-bump         Auto-bump and deploy to TestPyPI"
    echo "  $0 --pypi-token XXXX 1.2.3 Deploy with explicit token"
    echo ""
    echo "Current version: $(get_current_version)"
}

main() {
    # Parse command line arguments
    TEST_PYPI=false
    AUTO_BUMP=false
    VERSION=""
    ARG_TOKEN=""

    while [[ $# -gt 0 ]]; do
        case $1 in
            -t|--test-pypi)
                TEST_PYPI=true
                shift
                ;;
            --auto-bump)
                AUTO_BUMP=true
                shift
                ;;
            --pypi-token)
                ARG_TOKEN="$2"
                shift 2
                ;;
            -h|--help)
                show_usage
                exit 0
                ;;
            -*)
                print_error "Unknown option $1"
                show_usage
                exit 1
                ;;
            *)
                VERSION="$1"
                shift
                ;;
        esac
    done

    # Determine version
    if [ -z "$VERSION" ] && [ "$AUTO_BUMP" = true ]; then
        LOCAL_CUR="$(get_current_version)"
        REMOTE_CUR="$(get_remote_version "$TEST_PYPI")"
        if [ -z "$REMOTE_CUR" ]; then
            BASE="$LOCAL_CUR"
        else
            BASE="$(max_version "$LOCAL_CUR" "$REMOTE_CUR")"
        fi
        IFS='.' read -r MAJ MIN PAT <<<"$BASE"
        PAT=$((PAT + 1))
        if [ "$PAT" -ge 100 ]; then
            PAT=0
            MIN=$((MIN + 1))
        fi
        if [ "$MIN" -ge 100 ]; then
            MIN=0
            MAJ=$((MAJ + 1))
        fi
        VERSION="${MAJ}.${MIN}.${PAT}"
    fi

    if [ -z "$VERSION" ]; then
        print_error "Version is required (provide VERSION or use --auto-bump)"
        show_usage
        exit 1
    fi

    if [[ ! $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        print_error "Invalid version format. Use semantic versioning (e.g., 1.0.0)"
        exit 1
    fi

    # Ensure explicit VERSION is greater than both local and remote to avoid file reuse
    LOCAL_CUR="$(get_current_version)"
    REMOTE_CUR="$(get_remote_version "$TEST_PYPI")"
    BASE="$LOCAL_CUR"
    if [ -n "$REMOTE_CUR" ]; then
        BASE="$(max_version "$LOCAL_CUR" "$REMOTE_CUR")"
    fi
    if ! is_version_greater "$VERSION" "$BASE"; then
        print_error "Provided version $VERSION must be greater than current $BASE"
        exit 1
    fi

    # If token was provided via arg, export it to env
    if [ -n "$ARG_TOKEN" ]; then
        export PYPI_API_TOKEN="$ARG_TOKEN"
    fi

    deploy "$VERSION" "$TEST_PYPI"
}

# Run only if executed directly (not when sourced)
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
    main "$@"
fi
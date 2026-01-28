#!/usr/bin/env bash

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}[INFO]${NC} $*"; }
ok()   { echo -e "${GREEN}[OK]${NC}   $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERR]${NC}  $*"; }

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    err "Missing required command: $1"
    exit 1
  fi
}

pkg_name() {
  node -p "require('./package.json').name"
}

pkg_version() {
  node -p "require('./package.json').version"
}

set_version() {
  local v="$1"
  info "Setting version to $v (no git tag)"
  npm version "$v" --no-git-tag-version >/dev/null
}

auto_bump_patch() {
  local cur
  cur=$(pkg_version)
  node -e "
const v = process.argv[1].split('.').map(Number);
v[2] += 1;
console.log(v.join('.'));
" "$cur"
}

ensure_auth() {
  if [ -n "${NPM_TOKEN:-}" ]; then
    info "Using NPM_TOKEN from environment"
    # Create a temporary .npmrc for this publish only
    echo "//registry.npmjs.org/:_authToken=${NPM_TOKEN}" > .npmrc.publish
    trap 'rm -f .npmrc.publish' EXIT
    export NPM_CONFIG_USERCONFIG="$(pwd)/.npmrc.publish"
  else
    warn "NPM_TOKEN not set; relying on existing npm login/session"
  fi
}

publish() {
  local tag="${1:-}"
  if [ -n "$tag" ]; then
    info "Publishing with tag: $tag"
    npm publish --access public --tag "$tag"
  else
    npm publish --access public
  fi
}

usage() {
  cat <<USAGE
Usage: $0 [options] [VERSION]

Options:
  --auto-bump         Auto-bump patch version from package.json
  --tag <tag>         Publish with npm dist-tag (e.g. next, beta)
  -h, --help          Show this help

Examples:
  $0 0.0.2            Publish version 0.0.2
  $0 --auto-bump      Auto-bump and publish
  $0 --auto-bump --tag next  Publish as dist-tag "next"

Env:
  NPM_TOKEN           npm auth token (optional; otherwise uses existing login)
USAGE
}

main() {
  require_cmd node
  require_cmd npm

  local VERSION="" AUTO_BUMP=false TAG=""
  while [ $# -gt 0 ]; do
    case "$1" in
      --auto-bump) AUTO_BUMP=true; shift ;;
      --tag) TAG="$2"; shift 2 ;;
      -h|--help) usage; exit 0 ;;
      -*) err "Unknown option: $1"; usage; exit 1 ;;
      *) VERSION="$1"; shift ;;
    esac
  done

  # Ensure we are in the right directory
  if [ ! -f package.json ]; then
    err "Run this script from backend/nebula-r2r/js/nebula-mcp-server"
    exit 1
  fi

  info "Package: $(pkg_name)"
  info "Current version: $(pkg_version)"

  if [ -n "$VERSION" ] && $AUTO_BUMP; then
    err "Provide either VERSION or --auto-bump, not both"
    exit 1
  fi

  if $AUTO_BUMP; then
    VERSION=$(auto_bump_patch)
  fi

  if [ -z "$VERSION" ]; then
    err "No version provided. Use VERSION or --auto-bump"
    usage
    exit 1
  fi

  # Basic semver check
  if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    err "Invalid version: $VERSION (use X.Y.Z)"
    exit 1
  fi

  # Set version without git tag/commit
  set_version "$VERSION"

  # Install (if needed) and build
  info "Installing deps (if any)"
  npm ci || npm install
  info "Running build"
  npm run build

  ensure_auth

  info "Publishing to npm..."
  publish "$TAG"

  ok "Published $(pkg_name)@$VERSION"
  echo "https://www.npmjs.com/package/$(pkg_name)/v/$VERSION"
}

main "$@"



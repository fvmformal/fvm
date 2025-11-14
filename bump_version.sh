#!/bin/bash
set -e

echo "bump_version.sh: received argument = $1"
if [ "$#" -ne 1 ]; then
  echo "Usage: ./bump_version.sh VALUE" >&2
  echo "Where VALUE is any value accepted by 'uv version --bump':"
  echo "  major | minor | patch | stable | alpha | beta | rc | post | dev "
  echo "run 'uv help version' for details"
  exit 1
fi

if [ $(git branch --show-current) != "main" ]; then
  echo "ERROR: we do not bump versions in branches other than main"
  exit 1
fi

if [ -z "$(git status --porcelain)" ]; then
  echo "Working directory is clean, proceeding"
else
  echo "ERROR: we do not bump versions in repositories that are not clean"
  exit 1
fi

echo "current version: $(uv version --short)"
echo "bumping version by running 'uv version --bump $1'"
uv version --bump $1
echo "version bumped to: $(uv version --short)"
echo "adding pyproject.toml by running 'git add pyproject.toml'"
git add pyproject.toml
echo "creating commit by running git commit -m \"Bump version to $(uv version --short)\""
git commit -m "Bump version to $(uv version --short)"
echo "creating annotated tag with 'git tag -a $(uv version --short) -m \"Version $(uv version --short)\"'"
git tag -a $(uv version --short) -m "Version $(uv version --short)"
echo "All ok! Remember to:"
echo "  1. git push"
echo "  2. git push origin $(uv version --short)"

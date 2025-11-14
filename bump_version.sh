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

echo "current version: $(uv version --short)"
echo "bumping version by running 'uv version --bump $1'"
uv version --bump $1
echo "version bumped to: $(uv version --short)"
echo "creating annotated tag with 'git tag -a $(uv version --short) -m \"Version $(uv version --short)\"'"
git tag -a $(uv version --short) -m "Version $(uv version --short)"
echo "All ok! Remember to:"
echo "  1. git add pyproject.toml"
echo "  2. git commit"
echo "  3. git push"
echo "  4. git push origin $(uv version --short)"

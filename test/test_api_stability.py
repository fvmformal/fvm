# Copyright 2026 Universidad de Sevilla
# SPDX-License-Identifier: Apache-2.0

"""API stability checks"""

import os
import subprocess

from packaging.version import Version, parse

import shutil
import pytest
import griffe

from fvm import helpers

def test_api_stable():
    """Checks if we have inadvertently introduced breaking changes in our public API"""
    version_string = helpers.get_fvm_version()
    v = Version(version_string)
    major_version = v.major

    print()
    print(f'{  version_string=}')
    print(f'{  major_version=}')

    if not is_stable(version_string):
        pytest.skip(f'Version {version_string} not stable, not need to check the API for changes (changes are allowed)')

    git_executable = shutil.which('git')
    if git_executable is None :
        pytest.skip(f'git not found in PATH, cannot check API against previous versions')

    if not is_git_repo():
        pytest.skip("Not a git repository. Skipping API check.")

    # Get search path for griffe:
    # - If src/ exists (local dev), we must use it as a search path.
    # - If src/ is missing, we are testing a package we have just downloaded
    #   from TestPyPI, so we pass none to griffe. This way, griffe has to search
    #   the venv for fvm
    current_search_paths = ["src"] if os.path.exists("src") else None

    git_describe = get_git_describe()
    print(f'{  git_describe=}')
    current_commit_tag = get_current_commit_tag()
    print(f'{  current_commit_tag=}')
    all_tags = get_all_git_tags()

    if current_commit_tag:
        # If we have just tagged a commit, then remove it from all_tags since
        # it wouldn't make sense to compare it against itself. This way we can
        # compare it against a previous version, but not against itself.
        all_tags = [t for t in all_tags if t != current_commit_tag]

    print(f'{  all_tags=}')
    major_tags = filter_tags_by_major_version(all_tags, v.major)
    print(f'{  major_tags=}')
    stable_tags = filter_tags_by_stability(major_tags)
    print(f'{  stable_tags=}')
    reference = get_reference_tag(stable_tags)
    print(f'{  reference=}')

    if reference is None:
        pytest.skip('No matching tags found in {all_tags=} to compare against')

    # Call griffe to find breaking changes in the API
    current_package = griffe.load("fvm.framework", search_paths=current_search_paths)
    reference_package = griffe.load_git("fvm.framework", search_paths=["src"], ref=reference)
    breaking_changes = list(griffe.find_breaking_changes(reference_package, current_package))

    print(f'  {breaking_changes=}')

    if breaking_changes:
        # Build the full report
        report_lines = [breakage.explain(style=griffe.ExplanationStyle.VERBOSE) for breakage in breaking_changes]
        full_report = "\n".join(report_lines)

        # Fail the test with the full report
        pytest.fail(f"Breaking API changes detected in current version {git_describe} against {reference}:\n{full_report}")

def is_git_repo():
    """Returns True if we are inside a git repo, False if not. To be run after
    we are sure we have git in PATH."""
    try:
        subprocess.check_call(["git", "rev-parse", "--is-inside-work-tree"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def is_rc(version_string):
    """Returns True is version string indicates a release candidate, False if
    not"""
    v = Version(version_string)

    if v.pre and v.pre[0] == "rc":
        return True
    else:
        return False

def is_stable(version_string):
    """Returns True if version_string indicates a stable version, False if not"""
    v = Version(version_string)

    # d (dev), a (alpha), b (beta), and rc (release candidates) are all
    # pre-releases, but only rc need to be stable
    if v.is_prerelease:
        if is_rc(version_string):
            stable = True
        else:
            stable = False
    # Releases and post-releases must always be stable
    else:
        stable = True

    return stable

def get_all_git_tags():
    """Returns a list of all git tags found in the current git repo"""
    cmd = ["git", "tag", "-l"]
    return subprocess.check_output(cmd, text=True).splitlines()

def get_git_describe():
    """Returns the git describe for the current commit"""
    try:
        return subprocess.check_output(
            ["git", "describe", "--tags"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
    except subprocess.CalledProcessError:
        return None

def get_current_commit_tag():
    """Returns the tag name if HEAD is exactly at a tag, else None"""
    try:
        return subprocess.check_output(
            ["git", "describe", "--tags", "--exact-match"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
    except subprocess.CalledProcessError:
        return None

def filter_tags_by_major_version(tags, major_version):
    """From a number of version tags, return only those whose major version
    matches the `major_version` argument"""
    baselines = [t for t in tags if Version(t).major == major_version]
    return baselines

def filter_tags_by_stability(tags):
    """From a number of version tags, return only those which correspond to
    stable versions (as defined in `is_stable`)"""
    return [tag for tag in tags
    if is_stable(tag)]

def get_reference_tag(baselines):
    """Get the reference tag to which compare the current version of the code.

    Assumes all baselines received have already been filtered using first
    `filter_tags_by_major_version' and afterwards `filter_tags_by_stability`.

    For stable versions, we compare against the first X.0.0rc or X.0.0 (should
    have the same public API). Ideally X.0.0 should be compared against
    X.0.0rc1 and anything later than X.0.0 should be compared against X.0.0;
    nevertheless, since all of them are stable and should have the same API, we
    just compare against the oldest one. This way the logic is simpler and also
    automatically handles edge cases such as X.0.0 not existing, Y.0.0 not
    having release candidates, etc.

    Unstable versions do not need checking, but that logic is handled outside
    this function"""
    if not baselines:
        return None
    else:
        # Use packaging.version.parse to ensure first item is the oldest version
        sorted_baselines = sorted(baselines, key=parse)
        return sorted_baselines[0]

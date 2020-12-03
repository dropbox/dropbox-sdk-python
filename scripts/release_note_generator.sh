#!/bin/sh

last_version=$(git tag --sort v:refname | tail -n 2 | head -n 1)
echo "Getting commit history since $last_version"
num_commits=$(git rev-list --count $last_version..HEAD)
echo "Found $num_commits commits since last revision"
git_log=$(git log -n $num_commits --pretty="format:* %s %n")
linked_log=$(echo "Release Notes: \n\n$git_log" | sed -e 's/#\([0-9]*\)/[#\1](https:\/\/github.com\/dropbox\/dropbox-sdk-python\/pull\/\1)/g')
echo "\n\n$linked_log"
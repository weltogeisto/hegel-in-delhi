#!/bin/bash
# Bring ~/w3/native's refs up to date from the Windows repo: github/* as gh/* and as origin/* (the tool reads origin/shadow).
cd ~/w3/native || exit 1
git fetch -q /mnt/c/AI/projects/hegel-in-delhi '+refs/remotes/github/*:refs/remotes/gh/*' '+refs/remotes/github/*:refs/remotes/origin/*'
echo "origin/shadow $(git rev-parse --short origin/shadow): $(git log -1 --format=%s origin/shadow)"
if [ ! -d ~/w8/main ] || [ "$1" = "--main" ]; then rm -rf ~/w8/main; git worktree prune; mkdir -p ~/w8; git worktree add -q --detach ~/w8/main gh/main; fi
echo "tools at $(git -C ~/w8/main log --oneline -1)"

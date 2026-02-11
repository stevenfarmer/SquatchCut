#!/bin/sh

if [ -z "$husky_skip_init" ]; then
  debug () {
    [ "$HUSKY_DEBUG" = "1" ] && echo "husky (debug) - $1"
  }

  readonly husky_skip_init=1
  export husky_skip_init

  debug "starting $0..."
  if [ "$HUSKY" = "skip" ]; then
    debug "HUSKY is set to skip husky"
    exit 0
  fi

  if [ "$HUSKY_DEBUG" = "1" ]; then
    set -x
  fi

  hook_name="$(basename "$0")"
  debug "hook_name: $hook_name"
  husky_dir="$(dirname "$0")"
  debug "husky_dir: $husky_dir"

  readonly hook_name
  readonly husky_dir

  case "$hook_name" in
    "pre-commit"|"prepare-commit-msg"|"commit-msg"|"post-commit"|"applypatch-msg"|"pre-rebase"|"post-rewrite"|"post-merge"|"pre-push"|"pre-receive"|"update"|"proc-receive"|"post-receive"|"reference-transaction"|"push-to-checkout"|"pre-auto-gc"|"post-checkout"|"post-switch"|"post-applypatch")
      ;;
    *)
      exit 0
      ;;
  esac

  if [ -f "$husky_dir/husky.local.sh" ]; then
    . "$husky_dir/husky.local.sh"
  fi

  export PATH="$husky_dir/../../node_modules/.bin:$PATH"
  if command -v husky-run >/dev/null 2>&1; then
    husky-run "$hook_name" "$@"
  else
    npx --no -- husky-run "$hook_name" "$@"
  fi
fi

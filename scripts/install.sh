#!/usr/bin/env bash
set -euo pipefail

REPOSITORY="${MANOTRON_REPOSITORY:-eljoserass/manotron}"
VERSION="${MANOTRON_VERSION:-latest}"
ASSET_NAME="manotron-macos-arm64"
BIN_DIR="${MANOTRON_BIN_DIR:-$HOME/.local/bin}"
BIN_PATH="$BIN_DIR/manotron"
TEMP_DIR=""

if [ -t 1 ]; then
  BOLD=$'\033[1m'
  DIM=$'\033[2m'
  GREEN=$'\033[32m'
  RED=$'\033[31m'
  RESET=$'\033[0m'
else
  BOLD=""
  DIM=""
  GREEN=""
  RED=""
  RESET=""
fi

title() {
  printf '\n%smanotron%s\n' "$BOLD" "$RESET"
  printf '%sInvoice scanning, without the setup overhead.%s\n\n' "$DIM" "$RESET"
}

status() {
  printf '  %-12s %s\n' "$1" "$2"
}

success() {
  printf '\n%sInstalled%s %s\n' "$GREEN" "$RESET" "$BIN_PATH"
}

fail() {
  printf '\n%sError:%s %s\n' "$RED" "$RESET" "$1" >&2
  exit 1
}

cleanup() {
  if [ -n "$TEMP_DIR" ]; then
    rm -rf "$TEMP_DIR"
  fi
}

release_url() {
  if [ "$VERSION" = "latest" ]; then
    printf 'https://github.com/%s/releases/latest/download/%s' "$REPOSITORY" "$ASSET_NAME"
  else
    printf 'https://github.com/%s/releases/download/%s/%s' "$REPOSITORY" "$VERSION" "$ASSET_NAME"
  fi
}

download_binary() {
  local asset_url checksum_url
  asset_url="${MANOTRON_BINARY_URL:-$(release_url)}"
  checksum_url="${MANOTRON_CHECKSUM_URL:-${asset_url}.sha256}"
  TEMP_DIR="$(mktemp -d)"

  status "Download" "${VERSION} release"
  curl --fail --location --silent --show-error "$asset_url" -o "$TEMP_DIR/$ASSET_NAME"
  curl --fail --location --silent --show-error "$checksum_url" -o "$TEMP_DIR/$ASSET_NAME.sha256"

  status "Verify" "SHA-256 checksum"
  (
    cd "$TEMP_DIR"
    shasum -a 256 -c "$ASSET_NAME.sha256" >/dev/null
  ) || fail "The downloaded binary did not match its checksum."

  mkdir -p "$BIN_DIR"
  install -m 0755 "$TEMP_DIR/$ASSET_NAME" "$BIN_PATH"
}

read_value() {
  local prompt="$1"
  local value=""
  [ -r /dev/tty ] || fail "Interactive setup needs a terminal."
  while [ -z "$value" ]; do
    read -r -p "$prompt" value </dev/tty
  done
  printf '%s' "$value"
}

read_secret() {
  local prompt="$1"
  local value=""
  [ -r /dev/tty ] || fail "Interactive setup needs a terminal."
  read -r -s -p "$prompt" value </dev/tty
  printf '\n' >/dev/tty
  printf '%s' "$value"
}

configure_schedule() {
  local choice at_time day hours
  printf '\n%sAutomatic scans%s\n' "$BOLD" "$RESET"
  printf '  1  Do not schedule\n'
  printf '  2  Every day at a time\n'
  printf '  3  Weekdays at a time\n'
  printf '  4  Once a week\n'
  printf '  5  Every N hours\n'
  read -r -p "Select [1]: " choice </dev/tty
  choice="${choice:-1}"

  case "$choice" in
    1) return ;;
    2)
      at_time="$(read_value "Time, 24-hour HH:MM: ")"
      "$BIN_PATH" schedule set --daily "$at_time" --command "$BIN_PATH scan"
      ;;
    3)
      at_time="$(read_value "Time, 24-hour HH:MM: ")"
      "$BIN_PATH" schedule set --weekdays "$at_time" --command "$BIN_PATH scan"
      ;;
    4)
      day="$(read_value "Day [mon/tue/wed/thu/fri/sat/sun]: ")"
      at_time="$(read_value "Time, 24-hour HH:MM: ")"
      "$BIN_PATH" schedule set --weekly-day "$day" --weekly-time "$at_time" \
        --command "$BIN_PATH scan"
      ;;
    5)
      hours="$(read_value "Run every how many hours [1-23]: ")"
      "$BIN_PATH" schedule set --every-hours "$hours" --command "$BIN_PATH scan"
      ;;
    *) fail "Unknown schedule selection: $choice" ;;
  esac
}

onboard() {
  local api_key folder model
  api_key="${MANOTRON_OPENAI_API_KEY:-}"
  folder="${MANOTRON_FOLDER:-}"
  model="${MANOTRON_OPENAI_MODEL:-gpt-5-mini}"

  printf '\n%sSetup%s\n' "$BOLD" "$RESET"
  if [ -z "$api_key" ]; then
    api_key="$(read_secret "OpenAI API key: ")"
  fi
  [ -n "$api_key" ] || fail "An OpenAI API key is required."

  status "API key" "validating"
  "$BIN_PATH" validate-key --api-key "$api_key"

  if [ -z "$folder" ]; then
    folder="$(read_value "Folder to scan recursively: ")"
  fi

  "$BIN_PATH" init --folder "$folder" --api-key "$api_key" \
    --model "$model" --skip-key-validation
  configure_schedule
}

main() {
  trap cleanup EXIT
  title

  if [ "$(uname -s)" != "Darwin" ] || [ "$(uname -m)" != "arm64" ]; then
    if [ "${MANOTRON_ALLOW_UNSUPPORTED:-0}" != "1" ]; then
      fail "This release currently supports Apple Silicon macOS only."
    fi
  fi

  download_binary

  if [ "${MANOTRON_SKIP_ONBOARDING:-0}" != "1" ]; then
    onboard
  fi

  success
  printf 'Run %smanotron --help%s to see the available commands.\n\n' "$BOLD" "$RESET"
}

main "$@"


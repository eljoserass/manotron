#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${MANOTRON_REPO_URL:-https://github.com/eljoserass/manotron.git}"
INSTALL_DIR="${MANOTRON_INSTALL_DIR:-$HOME/.local/share/manotron/app}"
BIN_DIR="${MANOTRON_BIN_DIR:-$HOME/.local/bin}"
BIN_PATH="$BIN_DIR/manotron"

ensure_uv() {
  if command -v uv >/dev/null 2>&1; then
    return
  fi
  echo "Installing uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
}

clone_or_update() {
  mkdir -p "$(dirname "$INSTALL_DIR")"
  if [ -d "$INSTALL_DIR/.git" ]; then
    git -C "$INSTALL_DIR" pull --ff-only
  else
    rm -rf "$INSTALL_DIR"
    git clone "$REPO_URL" "$INSTALL_DIR"
  fi
}

install_wrapper() {
  mkdir -p "$BIN_DIR"
  cat > "$BIN_PATH" <<EOF
#!/usr/bin/env bash
cd "$INSTALL_DIR"
exec uv run manotron "\$@"
EOF
  chmod +x "$BIN_PATH"
}

prompt_required() {
  local prompt="$1"
  local value=""
  while [ -z "$value" ]; do
    read -r -p "$prompt" value
  done
  printf '%s' "$value"
}

configure_schedule() {
  echo
  echo "Schedule scan cron? Choose one:"
  echo "  1) none"
  echo "  2) daily at HH:MM"
  echo "  3) weekdays at HH:MM"
  echo "  4) weekly at day + HH:MM"
  echo "  5) every N hours"
  read -r -p "Choice [1]: " choice
  choice="${choice:-1}"

  case "$choice" in
    1) return ;;
    2)
      read -r -p "Daily time HH:MM: " at_time
      "$BIN_PATH" schedule set --daily "$at_time" --command "$BIN_PATH scan"
      ;;
    3)
      read -r -p "Weekday time HH:MM: " at_time
      "$BIN_PATH" schedule set --weekdays "$at_time" --command "$BIN_PATH scan"
      ;;
    4)
      read -r -p "Day [mon/tue/wed/thu/fri/sat/sun]: " day
      read -r -p "Weekly time HH:MM: " at_time
      "$BIN_PATH" schedule set --weekly-day "$day" --weekly-time "$at_time" --command "$BIN_PATH scan"
      ;;
    5)
      read -r -p "Every how many hours [1-23]: " hours
      "$BIN_PATH" schedule set --every-hours "$hours" --command "$BIN_PATH scan"
      ;;
    *)
      echo "Unknown choice, leaving schedule unchanged."
      ;;
  esac
}

main() {
  case "$(uname -s):$(uname -m)" in
    Darwin:arm64) ;;
    *) echo "Warning: this installer is aimed at macOS arm64, continuing anyway." ;;
  esac

  ensure_uv
  clone_or_update
  uv sync --project "$INSTALL_DIR"
  install_wrapper

  api_key="${MANOTRON_OPENAI_API_KEY:-}"
  if [ -z "$api_key" ]; then
    read -r -s -p "OpenAI API key: " api_key
    echo
  fi
  if [ -z "$api_key" ]; then
    echo "OpenAI API key is required."
    exit 1
  fi

  "$BIN_PATH" validate-key --api-key "$api_key"

  folder="${MANOTRON_FOLDER:-}"
  if [ -z "$folder" ]; then
    folder="$(prompt_required "Folder to scan recursively: ")"
  fi

  model="${MANOTRON_OPENAI_MODEL:-gpt-5-mini}"
  "$BIN_PATH" init --folder "$folder" --api-key "$api_key" --model "$model" --skip-key-validation
  configure_schedule

  echo
  echo "Installed manotron at $BIN_PATH"
  echo "Try: manotron scan"
}

main "$@"


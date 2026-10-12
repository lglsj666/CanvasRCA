#!/usr/bin/env bash
# Isolated renderer-only dependencies. Does not touch inference/train venvs.
set -euo pipefail
render_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
tool_dir="$render_root/build/renderer_tooling"
web_dir="$render_root/src/renderer/web"
node_version="24.20.0"
mkdir -p "$tool_dir"
if [[ ! -x "$tool_dir/node-v${node_version}-linux-x64/bin/node" ]]; then
  curl --fail --silent --show-error --max-time 120 -o "$tool_dir/node-v${node_version}-linux-x64.tar.xz" "https://nodejs.org/dist/v${node_version}/node-v${node_version}-linux-x64.tar.xz"
  curl --fail --silent --show-error --max-time 30 -o "$tool_dir/SHASUMS256.txt" "https://nodejs.org/dist/v${node_version}/SHASUMS256.txt"
  (cd "$tool_dir" && rg " node-v${node_version}-linux-x64.tar.xz$" SHASUMS256.txt | sha256sum -c -)
  tar -xJf "$tool_dir/node-v${node_version}-linux-x64.tar.xz" -C "$tool_dir"
fi
export PATH="$tool_dir/node-v${node_version}-linux-x64/bin:$PATH"
export PLAYWRIGHT_BROWSERS_PATH="$tool_dir/browsers"
cd "$web_dir"
npm ci --no-audit --no-fund
npx playwright install chromium --only-shell
mkdir -p assets
if [[ ! -f assets/DejaVuSans.ttf || ! -f assets/FONT-LICENSE.txt ]]; then
  # Existing licensed assets may be deployed from the qualified workstation.
  font_path="${CANVAS_RENDER_FONT:-/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf}"
  font_license="${CANVAS_RENDER_FONT_LICENSE:-/usr/share/doc/fonts-dejavu-core/copyright}"
  test -f "$font_path" && test -f "$font_license"
  cp "$font_path" assets/DejaVuSans.ttf
  cp "$font_license" assets/FONT-LICENSE.txt
fi
npm run typecheck
npm run build

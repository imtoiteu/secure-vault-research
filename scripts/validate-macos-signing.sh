#!/usr/bin/env bash
# H5 validation (macOS) — verify a BUILT, SIGNED, NOTARIZED Secure Vault app.
#
# This script does NOT sign anything; it only checks that a finished artifact would survive
# Gatekeeper on a clean machine — the exact failure validated in docs/VALIDATION-RESULTS.md (a
# quarantined, non-notarized nested `age` binary was SIGKILLed on first run). Run it on the build
# machine after `cargo tauri build` + signing + notarization + stapling.
#
# Usage:  scripts/validate-macos-signing.sh "/path/to/Secure Vault.app" [optional /path/to/app.dmg]
#
# Exit 0 = PASS (all checks green). Non-zero = FAIL (do NOT ship / do NOT start beta).
set -uo pipefail

APP="${1:-}"
DMG="${2:-}"
if [[ -z "$APP" || ! -d "$APP" ]]; then
  echo "usage: $0 \"/path/to/Secure Vault.app\" [app.dmg]" >&2
  exit 2
fi

fail=0
ok()   { printf '  PASS  %s\n' "$1"; }
bad()  { printf '  FAIL  %s\n' "$1"; fail=1; }

echo "== H5 macOS signing/notarization validation =="
echo "app: $APP"

# 1) The .app bundle's signature is valid, deep, and strict (covers nested code).
if codesign --verify --deep --strict --verbose=2 "$APP" 2>/tmp/cs.txt; then
  ok "codesign --verify --deep --strict (app + nested code)"
else
  bad "codesign --verify --deep --strict — $(tr '\n' ' ' </tmp/cs.txt)"
fi

# 2) Signed by a Developer ID Application authority with the Hardened Runtime flag (required for
#    notarization). Adjust the Team ID grep to your own if you want to pin it.
INFO="$(codesign -dvvv "$APP" 2>&1)"
if grep -q "Authority=Developer ID Application" <<<"$INFO"; then
  ok "Developer ID Application authority present"
else
  bad "not signed by a Developer ID Application authority (found: $(grep -m1 Authority <<<"$INFO" || echo none))"
fi
if grep -Eq "flags=.*runtime" <<<"$INFO"; then
  ok "Hardened Runtime enabled"
else
  bad "Hardened Runtime flag missing (notarization will reject)"
fi

# 3) Gatekeeper accepts it as an executable (the real first-run gate).
if spctl -a -t exec -vv "$APP" 2>/tmp/spctl.txt; then
  ok "spctl -a -t exec (Gatekeeper accepts)"
else
  bad "spctl rejected — $(tr '\n' ' ' </tmp/spctl.txt)"
fi

# 4) EVERY nested executable (the bundled age toolchain) is individually signed — this is the
#    specific thing that was killed when unsigned/quarantined (H5 root cause).
RES="$APP/Contents/Resources"
nested_found=0
while IFS= read -r -d '' f; do
  # Only check Mach-O executables (the age binaries), not data resources.
  if file "$f" | grep -q "Mach-O"; then
    nested_found=1
    if codesign --verify --strict "$f" 2>/dev/null; then
      ok "nested binary signed: ${f#"$RES/"}"
    else
      bad "nested binary UNSIGNED: ${f#"$RES/"} (will be SIGKILLed when quarantined)"
    fi
  fi
done < <(find "$RES" -type f -print0 2>/dev/null)
[[ "$nested_found" -eq 0 ]] && bad "no nested Mach-O binaries found under Resources/ — did the age toolchain get bundled?"

# 5) Notarization ticket is stapled to the app (offline Gatekeeper approval).
if xcrun stapler validate "$APP" >/tmp/stap.txt 2>&1; then
  ok "stapler validate (app notarization ticket stapled)"
else
  bad "stapler validate failed — $(tr '\n' ' ' </tmp/stap.txt)"
fi

# 6) The DMG, if provided, is itself signed + stapled.
if [[ -n "$DMG" ]]; then
  if [[ -f "$DMG" ]]; then
    if xcrun stapler validate "$DMG" >/tmp/stapdmg.txt 2>&1; then
      ok "stapler validate (dmg)"
    else
      bad "dmg not stapled — $(tr '\n' ' ' </tmp/stapdmg.txt)"
    fi
  else
    bad "dmg path not found: $DMG"
  fi
fi

echo
if [[ "$fail" -eq 0 ]]; then
  echo "RESULT: PASS — artifact should survive Gatekeeper on a clean machine."
  echo "Recommended final manual check: copy to a CLEAN macOS user account, open from the DMG, create a vault + add a file."
  exit 0
else
  echo "RESULT: FAIL — H5 not satisfied. Do NOT distribute or start beta."
  exit 1
fi

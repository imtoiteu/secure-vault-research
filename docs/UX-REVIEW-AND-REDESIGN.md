# UX/UI Review & Redesign — Security & Privacy Toolkit

Status: **review + proposal. No code, no backend/crypto/IPC/format/architecture change.** Grounded in
the shipped frontend (`desktop/frontend/{index.html,main.js,styles.css}`) and the real command
surface. Audience lens: a **non-technical end user** who wants to get a task done, not learn
cryptography.

> Scope guard: every recommendation here is **UI/UX only** (markup, copy, layout, flow, and one
> additive runtime affordance — native file dialogs). It changes **no** Rust command, crypto
> primitive, IPC argument, on-disk format (`.svault`/`.svenc`/`.svkey`/`.svshare`), security property,
> or crate boundary. Where a recommendation would touch anything backend, it is explicitly flagged
> and deferred, not assumed.

---

## 1. UX audit

### 1.0 Method & status legend
Findings are rated **P0** (blocks/derails a normal user), **P1** (significant friction), **P2**
(polish). Feature availability uses the project's discipline: ✅ implemented · 🟡 implemented but
vault-bound · 🔬 research/not built.

### 1.1 Information architecture
- **P0 — Technology-first grouping.** The top split is **"Secure Vault" vs "Cryptography &
  Integrity."** A normal user does not wake up wanting to do "cryptography"; they want to *lock a
  file with a password*, *prove a document is theirs*, or *check a download wasn't tampered with*.
  The nav names the **machinery**, not the **goal**.
- **P0 — The same capability lives in two places.** "Verify a signature" exists both in the vault's
  **Verify & integrity** tab (`verify_file`, [index.html:105-123](frontend/index.html#L105-L123)) and
  in the toolkit's **Verify signature** tab (`integrity_verify_signature`). "Hashing" appears twice
  too: **Compute container hash** (`integrity_hash`, a *vault* file) vs **Hash a file**
  (`integrity_hash_file`, any file). Two doors to near-identical ideas → users can't form a mental
  model.
- **P1 — "Vault" is treated as the whole app, then as one module.** The app *opens* on a vault form,
  yet the toolkit is a peer. The product is a toolkit *containing* a vault; the IA inverts that.
- **P1 — No home / no map.** There is no overview of what the app can do. Discovery is "click every
  tab and read."

### 1.2 Navigation flow
- **P0 — Three nesting levels.** Top pill → view (locked/unlocked) → tab → (sometimes) subcard. The
  user must track *where am I* across three axes, one of which (locked/unlocked) changes under them.
- **P1 — Landing screen assumes expertise.** First paint is **"Open or create a vault"**
  ([index.html:29-67](frontend/index.html#L29-L67)) — a stranger doesn't know what a vault is, which
  button to press (**Unlock** vs **Create new**, equal weight), or what a "recovery policy" is.
- **P1 — Mode switch loses context.** Switching to the toolkit hides the vault entirely; the
  **Locked/Unlocked** badge keeps showing in the header even while you're doing unrelated file tools.
- **P2 — Tabs reset, no deep-linking, no back.** Nothing remembers the last screen or supports a
  "back to where I was."

### 1.3 Discoverability
- **P0 — Goal→feature mapping is invisible.** "I want to password-protect a PDF" lives under
  *Cryptography & Integrity → Encrypt / Decrypt*. Nothing on the surface connects the user's words to
  that location. Feature descriptions only appear *after* you've already found and opened the tab.
- **P1 — Critical setup is buried.** Recovery is hidden inside an **Advanced** `<details>` at vault
  creation ([index.html:42-61](frontend/index.html#L42-L61)), and the link between "enable recovery
  now" and "mint shares later (different tab, different view)" is never drawn.
- **P1 — Signing requires an invisible prerequisite.** Toolkit **Sign a file** needs a `.svkey` that
  only exists if you first used **Generate a signing key** in the same tab — discoverable only by
  reading.

### 1.4 Cognitive load
- **P0 — Jargon everywhere.** Visible to users today: *Shamir shares, threshold (k), minisign,
  BLAKE3, Argon2id, container, recipient/identity, suite v1, contract v1, format v1*, plus raw file
  extensions `.svault/.svenc/.svkey/.svshare/.minisig`. Each is a comprehension tax.
- **P0 — The header version string is intimidating.** `v0.0.0 · format v1 · suite v1 · contract v1`
  ([main.js:238-242](frontend/main.js#L238-L242)) means nothing to a user and signals "this is for
  engineers."
- **P1 — Every screen is a bare multi-field form.** No "what is this / when do I use it / what do I
  get" framing; the user must infer intent from field labels.

### 1.5 Form complexity
- **P0 — All file locations are hand-typed paths.** Every input is a free-text path
  (`/path/to/my.svault`, `/path/to/output/dir`, output filenames). On a desktop app this is the
  single biggest friction and error source — typos, wrong slashes, nonexistent dirs.
- **P1 — Recovery shares are pasted one-path-per-line into a textarea**
  ([index.html:80-83](frontend/index.html#L80-L83)). Selecting 3 files by typing 3 paths is brutal.
- **P1 — `n`/`k` number boxes with no guidance** ([index.html:175-182](frontend/index.html#L175-L182)).
  A user has no idea what "Total shares 5 / Threshold 3" *means for them* ("any 3 of 5 people can
  restore it").
- **P2 — Output paths must be invented by the user**, then the backend *refuses to overwrite*
  (`SV-OUTPUT-EXISTS`), turning a normal "save" into a dead-end error.

### 1.6 Terminology clarity
- **P1 — Tab names mix metaphors:** "Open / Create", "Recover with shares", "Verify & integrity",
  "Sign & keys", "Hash". Verbs, nouns, and tech terms intermixed.
- **P1 — Duplicated/ambiguous labels:** "Verify signature" (two of them), "Compute container hash"
  vs "Hash a file" — the *difference* (a vault file vs any file) is never explained.

### 1.7 Visual hierarchy
- **P1 — Flat emphasis.** Cards are equal weight; primary vs secondary actions aren't obvious
  (**Unlock**/**Create new** look similar). No per-feature icons to aid scanning.
- **P1 — Results hide in a 1-line status bar at the bottom** ([main.js:64-68](frontend/main.js#L64-L68)).
  A 64-char hash, a signature path, or "VALID/INVALID" deserves a prominent result, not a footnote.
- **P2 — No empty-state guidance** beyond "No items yet."

### 1.8 Default workflows
- **P0 — Default path is the most technical one** (vault). The common quick tasks (lock a file,
  verify a download) are 2-3 clicks deep behind a mode switch.
- **P1 — No smart defaults.** Output dir/name aren't pre-filled from the input; nothing is remembered
  between actions.

### 1.9 Error handling
- **P1 — Errors land far from their cause.** Validation ("X is required") and backend errors all
  surface in the bottom status bar, not inline at the field.
- **P1 — File-exists is a dead end.** `SV-OUTPUT-EXISTS` tells the user to pick another path but
  offers no in-flow way to do it (no re-prompt, no suggested name).
- **P2 — Wrong-password and tamper are merged** (correct, oracle-safe) but the message could better
  guide ("the password didn't work, or this file isn't a valid encrypted file").

### 1.10 File selection UX
- **P0 — No native pickers, no drag-and-drop.** This is the headline issue and underlies several P0s
  above. Desktop users expect **Browse…**, **Save As…**, and dropping a file on the window.

### Audit summary (top 5 to fix first)
1. Replace hand-typed paths with **native file/folder/save pickers + drag-drop** (P0, §1.10/1.5).
2. Reorganize around **tasks, not technologies**, with a **Home launcher** (P0, §1.1/1.3/1.8).
3. **De-jargon** every user-facing string; hide crypto internals behind "Advanced/Details" (P0, §1.4/1.6).
4. **One task = one guided screen** with what/when/inputs/output framing + a prominent **result panel**
   (P0/P1, §1.4/1.7/1.9).
5. **De-duplicate** verify/hash; make vault-integrity a *vault* action, not a global tool (P0, §1.1).

---

## 2. Proposed information architecture

**Principle:** name the *goal*, group by *intent*, expose features as verbs. The toolkit's modules
remain the backbone, but the user never sees "Cryptography" as a destination — they see "Protect a
file" / "Prove it's authentic" / "Share a secret safely."

### 2.1 Goal-based top level (the user's words → the module)

| User intent (sidebar group) | Tasks (screens) | Backing module · status |
| --- | --- | --- |
| **🏠 Home** | "What do you want to do?" launcher | — |
| **🗄 Vaults** | Open / create / manage an encrypted vault | Secure Vault · ✅ |
| **🔐 Protect a file** | **Lock a file with a password** (Encrypt) · **Unlock a file** (Decrypt) | Cryptography · ✅ |
| | Hide data inside a file · Add a watermark | Steganography 🔬 · Watermarking 🔬 |
| **✅ Prove it's authentic** | **Sign a file** · **Check a signature** · **Fingerprint a file** (Hash) · **Check a file is unchanged** (Verify Integrity) | Cryptography/Integrity · ✅ (Verify-Integrity composable, §6) |
| **🧩 Back up & recover a secret** | Split a secret into recovery pieces · Recover from pieces · Send securely by QR | Secret Sharing 🟡 · QR 🔬 |
| **🔎 Inspect & clean a file** | Detect hidden data · Inspect metadata · Remove metadata · Analyze a file | Detection/Metadata/Analysis 🔬 |

Notes:
- **Vault-integrity check** (`integrity_check`) and **the vault's signing key** are *not* global
  tools; they live **inside the open vault** as maintenance/info actions (§4.2). This removes the
  duplicate "Verify & integrity" door.
- Every 🔬 item appears as a **"Coming soon"** screen (explains what it will do, marked unavailable) so
  the map is complete and honest without implying function.

### 2.2 Plain-language terminology map (apply globally)

| Today (jargon) | Proposed user-facing term |
| --- | --- |
| Encrypt File / Decrypt File | **Lock a file with a password** / **Unlock a file** |
| `.svenc` | "locked file (.svenc)" — extension secondary |
| Sign File | **Sign a file** ("prove it came from you") |
| Verify Signature | **Check a signature** ("confirm who signed it & that it's unchanged") |
| Hash File / BLAKE3 | **Fingerprint a file** (a unique ID of its contents) |
| Verify Integrity | **Check a file is unchanged** |
| Signing keypair · `.svkey` / `.pub` | **Your signing identity** → "private key (keep secret)" / "public key (share it)" |
| Vault / container / `.svault` | **Vault** (a password-protected box of files) |
| Shamir shares / threshold (k) / n | **Recovery pieces** · "you'll need **any K of N** pieces to restore" |
| minisign / Ed25519 / Argon2id / secretbox | (hidden; shown only under **Technical details**) |
| recipient / identity (age) | (never shown to users) |
| `suite v1 · contract v1 · format v1` | (moved into an **About** dialog) |

### 2.3 Availability honesty
A persistent badge per feature: **Available** (green), **Coming soon** (muted). The Home launcher and
sidebar show both, but "Coming soon" tiles are non-interactive with a one-line teaser. This keeps the
roadmap visible (good for product) without misrepresenting status (per the project's status rules).

---

## 3. Navigation redesign

### 3.1 From 3-level nested tabs → 2-level persistent shell
- **Left sidebar (persistent):** the goal groups from §2.1, each expandable to its task screens.
  Always visible; replaces the top pill + per-view tab bars. One click = one task.
- **Main pane:** exactly one task screen at a time (or Home).
- **Header (slimmed):** app name + a single **About** affordance (hosts the version/suite strings)
  and a global **Settings** (theme, "remember last folder"). The **Locked/Unlocked** badge moves
  *into the Vault screens only* — it's a vault concept, not a global one.

### 3.2 Default workflow
- App opens on **🏠 Home**, not a vault form.
- Home leads with the **3 most common quick tasks** (Lock a file, Check a signature, Open a vault),
  then the full grid.
- Smart defaults on every task: output folder defaults to the input's folder; output name is
  auto-suggested (`report.pdf` → `report.pdf.svenc`); the last-used folder is remembered.

### 3.3 File selection (the highest-impact change)
Replace every path text field with a **read-only field + Browse…** and enable **drag-and-drop** onto
the drop zone. Use the OS-native **Open file**, **Choose folder**, and **Save As** dialogs.
- Implementation note (flagged, not done here): this needs Tauri's **dialog** plugin + a capability
  permission, and optionally `fileDropEnabled`. It is **additive UI/runtime** — it does **not** alter
  any crypto command, IPC argument shape (paths are still `String`s), format, or security property.
  If adding the plugin is undesirable, a fallback keeps text fields but adds drag-drop + path
  validation; the picker is strongly recommended.
- **Save As** naturally lets users choose a non-colliding name, defusing most `SV-OUTPUT-EXISTS`
  dead-ends. (The backend still refuses silent overwrite — unchanged. On the rare collision the UI
  re-opens Save As with a suggested `name (1).svenc`, see §5 error pattern.)

### 3.4 Result-centric feedback
Every action ends in a **result card** in the main pane (not the status bar): success state, the
**output location with a "Show in folder" / "Copy" affordance**, and **next-step buttons**
(e.g., after Sign → "Check this signature"; after Encrypt → "Unlock it" to test). Errors render
**inline** at the offending field plus a summary banner.

---

## 4. Screen mockups / wireframes (text)

ASCII frames. `[ Browse… ]` = native open dialog; `[ Save As… ]` = native save dialog; `(i)` = inline
help tooltip; `▸ Technical details` = collapsed jargon.

### 4.0 Global shell
```
┌───────────────────────────────────────────────────────────────────────────┐
│ 🔒 Security & Privacy Toolkit                              [About] [⚙ Settings]│
├───────────────┬───────────────────────────────────────────────────────────┤
│ 🏠 Home        │                                                           │
│               │                                                           │
│ 🗄 Vaults      │                   ( MAIN PANE: Home or a task )           │
│ 🔐 Protect    │                                                           │
│   Lock a file │                                                           │
│   Unlock file │                                                           │
│   Hide data ⌛ │                                                           │
│ ✅ Prove       │                                                           │
│   Sign a file │                                                           │
│   Check sig   │                                                           │
│   Fingerprint │                                                           │
│   Check intact│                                                           │
│ 🧩 Recovery    │                                                           │
│   Split secret│                                                           │
│   Recover     │                                                           │
│   QR send ⌛   │                                                           │
│ 🔎 Inspect ⌛   │                                                           │
└───────────────┴───────────────────────────────────────────────────────────┘
   (⌛ = Coming soon, shown muted)
```

### 4.1 Home launcher
```
┌ MAIN PANE ────────────────────────────────────────────────────────────────┐
│  What would you like to do?                                                │
│                                                                            │
│  Quick start                                                               │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐           │
│  │ 🔐 Lock a file    │ │ ✅ Check a file   │ │ 🗄 Open a vault   │           │
│  │ Password-protect │ │ Is this download │ │ Your encrypted   │           │
│  │ one file.        │ │ genuine/intact?  │ │ box of files.    │           │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘           │
│                                                                            │
│  All tools                                                                 │
│  Protect: [Lock a file] [Unlock a file] [Hide data ⌛] [Watermark ⌛]        │
│  Prove:   [Sign a file] [Check a signature] [Fingerprint] [Check intact]   │
│  Recovery:[Split secret] [Recover] [QR send ⌛]                             │
│  Inspect: [Detect hidden ⌛] [Inspect metadata ⌛] [Remove metadata ⌛]       │
│                                                                            │
│  Each tile: icon · plain title · one-line "what it does". ⌛ = Coming soon. │
└────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Task screen anatomy (the reusable template)
```
┌ MAIN PANE ────────────────────────────────────────────────────────────────┐
│ 🔐 Lock a file with a password                                             │
│ Turn any file into a locked file only your password can open.              │
│ ▸ When should I use this?  (collapsed: "Send a sensitive file, or store    │
│   one safely. Anyone with the password can open it — there's no recovery.")│
│ ───────────────────────────────────────────────────────────────────────── │
│ 1  Choose the file to lock                                                 │
│    ┌─────────────────────────────────────────────┐                        │
│    │  Drop a file here, or              [ Browse… ]│   report.pdf · 2.4 MB │
│    └─────────────────────────────────────────────┘                        │
│ 2  Set a password                                                          │
│    Password        [ •••••••••••• ]                                        │
│    Confirm         [ •••••••••••• ]   ⚠ shown inline if mismatched         │
│    (i) A typo here can't be undone — the file could never be opened.       │
│ 3  Where to save it                                                        │
│    [ report.pdf.svenc ]                              [ Save As… ]          │
│    ▸ Technical details (Argon2id + secretbox)                              │
│ ───────────────────────────────────────────────────────────────────────── │
│                                            [  Lock file  ]  ← one primary  │
└────────────────────────────────────────────────────────────────────────────┘
        ↓ on success, the same pane swaps to a RESULT card:
┌────────────────────────────────────────────────────────────────────────────┐
│ ✅ Locked.                                                                  │
│ Saved to  ~/Documents/report.pdf.svenc          [ Show in folder ]         │
│ Keep your password safe — it's the only way back in.                       │
│ Next:  [ Unlock it (test) ]   [ Lock another file ]                        │
└────────────────────────────────────────────────────────────────────────────┘
```
This 3-step pattern (Input → Options → Output, one primary CTA, result card) is reused by **every**
task below, so users learn it once.

### 4.3 Unlock a file (Decrypt)
```
🔓 Unlock a file
Open a locked (.svenc) file with its password.
1 Locked file   [ Drop / Browse… ]   report.pdf.svenc
2 Password      [ •••••••••• ]
3 Save opened file as  [ report.pdf ]            [ Save As… ]
                                         [ Unlock file ]
Error state (wrong password OR not a valid locked file → one message, oracle-safe):
  ⚠ Couldn't open this. The password may be wrong, or this isn't a valid locked file.
```

### 4.4 Sign a file + first-run identity setup
```
✍️ Sign a file
Prove a file came from you and hasn't changed since.
┌ First time? You need a signing identity. ───────────────────────────────┐
│ You don't have one yet. [ Create my signing identity ]                   │
│  → opens a guided step: choose a folder, name it ("work-laptop"),        │
│    set a password. Produces:                                             │
│      • public key  (share this so others can check your signatures)      │
│      • private key (.svkey, keep secret — protected by your password)    │
└──────────────────────────────────────────────────────────────────────────┘
1 File to sign       [ Drop / Browse… ]
2 Your signing key   [ Browse… work-laptop.svkey ]  (remembered after 1st use)
3 Password           [ ••••••• ]
                                         [ Sign file ]
Result: ✅ Signed → report.pdf.minisig   [ Show in folder ]
        Next: [ Check this signature ]  [ Share my public key ]
```

### 4.5 Check a signature (Verify Signature)
```
✅ Check a signature
Confirm a file was signed by a specific person and hasn't changed.
1 The file            [ Drop / Browse… ]
2 The signature       [ Browse… *.minisig ]
3 Their public key    [ Browse… *.pub ]
                                         [ Check ]
Result states (prominent, color-coded):
  ✅ Genuine — signed with this key and unchanged.   Fingerprint: ab12…  [Copy]
  ❌ Does NOT match — the file, signature, or public key is wrong, or the file changed.
```

### 4.6 Fingerprint a file (Hash) & Check intact (Verify Integrity)
```
🔢 Fingerprint a file
Get a unique ID (BLAKE3) of a file's exact contents — to compare copies.
1 File   [ Drop / Browse… ]                         [ Get fingerprint ]
Result:  ┌ ab12cd…(64 hex)…ef ┐  [ Copy ]   "Two files with the same fingerprint are identical."

🛡 Check a file is unchanged   (Verify Integrity — composed in the UI, §6)
Confirm a file still matches a fingerprint you were given.
1 File                 [ Drop / Browse… ]
2 Expected fingerprint [ paste the value you were given ]   [ Check ]
Result:  ✅ Matches — unchanged.   /   ❌ Different — this file does not match.
```

### 4.7 Secure Vault — open/create (no jargon up front)
```
🗄 Vaults
A vault is a password-protected box that holds many files.

[ Open an existing vault ]        [ + Create a new vault ]
─ Open ─────────────────────────────────────────────────────────────────────
  Vault file   [ Browse… *.svault ]
  Password     [ •••••••• ]                                  [ Open vault ]
─ Create ───────────────────────────────────────────────────────────────────
  Save new vault as   [ Save As… my-vault.svault ]
  Password            [ •••••• ]   Confirm [ •••••• ]
  ▸ Recovery (optional, recommended)
      ☐ Let me recover this vault from "recovery pieces" if I forget where it is
        (i) You'll split a backup key into N pieces; any K can restore it.
            Total pieces [5]   Needed to restore [3]                 → "any 3 of 5"
                                                          [ Create vault ]
```

### 4.8 Secure Vault — unlocked dashboard (vault context only)
```
┌ my-vault.svault · 🔓 Unlocked · 3 files · recovery: any 3 of 5     [ Lock ] ┐
│ Tabs:  Files   |   Recovery pieces   |   Vault info                         │
│                                                                             │
│ FILES                                                                       │
│   report.pdf      2.4 MB   ab12…   [ Save a copy… ]                         │
│   keys.txt        1 KB     9f0c…   [ Save a copy… ]                         │
│   [ + Add file ]  (Browse… picks the source; name auto-filled, editable)    │
│                                                                             │
│ RECOVERY PIECES  → Split / mint pieces (pre-filled to the vault's 3-of-5)   │
│ VAULT INFO       → uuid, created, KDF cost, signing public key (Copy),      │
│                    "Check this vault file is intact" (integrity_check)      │
│                    — all the old jargon lives here, clearly labelled info.  │
└─────────────────────────────────────────────────────────────────────────────┘
```
Key move: the **vault-only** signing key and the **container integrity check** live here as *vault
info/maintenance*, not as global tools — killing the §1.1 duplication.

### 4.9 Split / Recover (Secret Sharing — vault-bound today, friendlier copy)
```
🧩 Split into recovery pieces            (inside an open vault, or a guided wrapper)
Create N pieces; any K together can restore the secret. Store each piece separately.
  How many pieces total?  [5]      How many needed to restore?  [3]
  Save pieces to folder   [ Choose folder… ]
  (i) "Any 3 of these 5 pieces can restore it. Fewer than 3 reveal nothing."
                                                          [ Create pieces ]
Result: list of 5 files + "Give each to a different trusted place."

🧩 Recover from pieces
  Vault file        [ Browse… ]
  Recovery pieces   [ + Add piece ]  ⟶ multi-select file picker (not a textarea)
                    • piece-1.svshare   • piece-3.svshare   • piece-5.svshare
                                                          [ Recover ]
  Inline count guidance: "You've added 3 of the 3 needed." (uses SV-INSUFFICIENT-SHARES)
```

### 4.10 Coming-soon module screen (honest placeholder)
```
🕵️ Hide data inside a file              [ Coming soon ]
What it will do: conceal a file inside an image/audio so it looks ordinary.
When you'd use it: send something discreetly alongside a normal-looking file.
Status: under evaluation — not available yet.       (no inputs, non-interactive)
```

### 4.11 Error & file-exists pattern (applies everywhere)
```
• Inline first: ⚠ under the specific field ("Choose a file first.").
• Banner for backend errors, plain language, mapped from the coded ApiError:
    SV-UNAUTHORIZED → "Wrong password, or this isn't a valid locked file."
    SV-OUTPUT-EXISTS → non-dead-end: "A file with that name exists." [ Choose a new name… ]
                       → re-opens Save As pre-filled "report.pdf (1).svenc"
    SV-TOO-LARGE     → "This file is 3.1 GB — over the 2 GB limit for locking."
    SV-IO            → "Couldn't read/write there. Check the location and free space."
• Success is never a status-bar footnote — it's the result card (§4.2).
```

---

## 5. Cross-cutting recommendations (mapped to the audit)

| Audit area | Recommendation |
| --- | --- |
| Information architecture | Goal-based sidebar (§2.1); vault-integrity + vault signing key become **vault-internal** info, not global tools. |
| Navigation flow | 2-level shell (sidebar → screen); open on **Home**; badge scoped to Vault. |
| Discoverability | Home launcher with plain-language tiles + "Coming soon" map; first-run identity helper for Sign. |
| Cognitive load | One task / one screen / one primary action; "what / when / output" framing; jargon under **Technical details / Vault info**. |
| Form complexity | Native pickers + drag-drop; smart default output name/folder; multi-select for recovery pieces; n/k explained as "any K of N". |
| Terminology | Apply the §2.2 map globally; remove version string to **About**. |
| Visual hierarchy | Per-feature icons; single filled primary button; prominent **result card**; color-coded verify outcomes. |
| Default workflows | Home-first; quick-start trio; remember last folder. |
| Error handling | Inline-at-field + plain banner; turn `SV-OUTPUT-EXISTS` into a "choose a new name" re-prompt; keep oracle-safe merges. |
| File selection | **Highest priority:** Browse/Save As/Choose-folder dialogs + drag-drop (additive runtime; no backend/crypto/IPC/format change). |

---

## 6. Recommended implementation order (UI only)

Sequenced by **user impact × shippable-against-real-backend-today**. Nothing here needs a backend,
crypto, IPC, format, or architecture change **except** the optional dialog plugin (flagged in 3.3).

**Phase U1 — Foundation & the file-picker win (largest impact).**
- New shell: slim header (About/Settings), **persistent sidebar**, **Home launcher**.
- Reusable **task-screen template** (what/when → input → options → output → result card).
- **Native file/folder/save pickers + drag-drop**; smart default output names; remember last folder.
- Global **terminology pass** (§2.2) and move the version string into About.
- *Why first:* fixes the P0s (paths, IA, jargon, defaults) and every later screen reuses it.

**Phase U2 — Redesign the 5 already-shipped task screens (✅ real backend).**
- **Lock a file / Unlock a file** (Encrypt/Decrypt), **Sign a file** (+ first-run identity helper),
  **Check a signature**, **Fingerprint a file** — all on the new template, with result cards and
  inline errors. De-duplicate the old vault "Verify & integrity" tab into these.

**Phase U3 — Secure Vault re-skin (✅).**
- Vault open/create with progressive recovery options; unlocked **dashboard** (Files / Recovery
  pieces / **Vault info** holding the integrity check, signing public key, and all remaining jargon).

**Phase U4 — Verify Integrity, composed (✅, frontend-only).**
- **"Check a file is unchanged"** = hash the file with the existing `integrity_hash_file` and
  string-compare to a pasted fingerprint. No new backend command; pure UI logic. (Signature-based
  verify-integrity already exists as **Check a signature**.)

**Phase U5 — Secret Sharing screens, friendlier (🟡 vault-bound).**
- Re-skin **Split / Recover** with "any K of N" language and **multi-select** piece pickers over the
  existing `keys_split`/`keys_recover` (still vault-bound; no decoupling implied in the UI copy).

**Phase U6 — Honest "Coming soon" surfaces (🔬).**
- Non-interactive placeholder screens for Steganography, Watermarking, Metadata Protection, Secure QR
  Transfer, Analysis — each states *what it will do / when you'd use it / not available yet*. Completes
  the map and discoverability without overclaiming.

> Deliverable boundary: this document is **review + design**. It changes no code. Building any phase
> above is a separate, explicitly-authorized step; even then it stays within frontend + (optionally)
> the additive dialog plugin, never touching crypto, IPC contracts, formats, security, or architecture.
```

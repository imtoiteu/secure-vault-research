// Security & Privacy Toolkit — internationalization (i18n) runtime + string catalogue.
//
// Loaded BEFORE main.js (see index.html). Pure vanilla JS, no bundler — same constraints as the
// rest of the frontend (CSP forbids inline scripts, so this is a same-origin file).
//
// Design:
//   • Two locales: Vietnamese (`vi`, the DEFAULT) and English (`en`, the fallback).
//   • The user's choice persists in localStorage, which a Tauri webview keeps across restarts.
//   • Static markup is translated by attribute: `data-i18n` (textContent), `data-i18n-html`
//     (innerHTML, for hints that embed <strong>/<code>/<em>), `data-i18n-ph` (placeholder),
//     `data-i18n-title` (tooltip/title). The HTML keeps its English literals as a graceful
//     fallback if JS ever fails to run.
//   • Dynamic strings (result cards, status, validation, lists) call `window.i18n.t(key, params)`
//     from main.js. `{name}` placeholders are interpolated from `params`.
//   • A missing key falls back to English, then to the raw key (so gaps are visible, never blank).
//
// This file changes NO business logic, IPC contract, crypto, or format — it is presentation only.

(function () {
  "use strict";

  const STORAGE_KEY = "sv.lang";
  const DEFAULT_LANG = "vi";
  const SUPPORTED = ["vi", "en"];

  // =========================================================================
  // English catalogue (also the fallback for any key missing from another locale).
  // Values mirror the original hard-coded UI text verbatim where practical.
  // =========================================================================
  const EN = {
    // ---- chrome / header ----
    "app.title": "🔒 Security & Privacy Toolkit",
    "header.attribution": "© Tracy Tran • Secure Vault v0.1.0",
    "header.about": "About",
    "header.language": "Language",
    "lang.vi": "Tiếng Việt",
    "lang.en": "English",

    // ---- sidebar groups + items ----
    "nav.group.vaults": "Vaults",
    "nav.group.protect": "Protect a file",
    "nav.group.authentic": "Prove it's authentic",
    "nav.group.backup": "Back up & recover",
    "nav.group.inspect": "Inspect & clean",
    "nav.home": "🏠 Home",
    "nav.vault": "🗄️ Secure Vault",
    "nav.encrypt": "🔐 Lock a file",
    "nav.decrypt": "🔓 Unlock a file",
    "nav.hide": "🕵️ Hide data in an image",
    "nav.unhide": "🔓 Reveal hidden data",
    "nav.watermark": "💧 Tamper-proof a file",
    "nav.sign": "✍️ Sign a file",
    "nav.verify": "✅ Check a signature",
    "nav.hash": "🔢 Fingerprint a file",
    "nav.intact": "🛡️ Check a file is unchanged",
    "nav.verifyIntegrity": "🧾 Verify a download",
    "nav.splitSecret": "🧩 Split a secret",
    "nav.splitFile": "🧩 Split a file",
    "nav.recoverPieces": "🔗 Recover from pieces",
    "nav.qrTransfer": "📷 Secure QR transfer",
    "nav.detect": "🔎 Detect hidden data",
    "nav.metadataInspect": "🔍 Inspect metadata",
    "nav.metadataClean": "🧹 Remove metadata",
    "nav.metadataCompare": "📑 Compare metadata",

    // ---- home ----
    "home.title": "What would you like to do?",
    "home.hint": "Pick a task. Every tool explains what it does, what it needs, and what you get.",
    "home.recent": "Recent tools",
    "home.quickStart": "Quick start",
    "home.allTools": "All tools",
    "home.q.encrypt.title": "Lock a file",
    "home.q.encrypt.desc": "Password-protect a single file.",
    "home.q.intact.title": "Check a file is unchanged",
    "home.q.intact.desc": "Confirm a file matches the fingerprint you were given.",
    "home.q.vault.title": "Open a vault",
    "home.q.vault.desc": "Your password-protected box of files.",
    "home.t.encrypt": "Lock a file",
    "home.t.decrypt": "Unlock a file",
    "home.t.sign": "Sign a file",
    "home.t.verify": "Check a signature",
    "home.t.hash": "Fingerprint a file",
    "home.t.intact": "Check a file is unchanged",
    "home.t.vault": "Secure Vault",
    "home.t.splitSecret": "Split a secret",
    "home.t.splitFile": "Split a file",
    "home.t.recover": "Recover from pieces",
    "home.t.hide": "Hide data",
    "home.t.detect": "Detect hidden data",
    "home.t.metadata": "Metadata tools",
    "home.soon": "soon",

    // ---- vault: shared ----
    "vault.title": "🗄️ Secure Vault",
    "vault.badge.locked": "Locked",
    "vault.badge.unlocked": "Unlocked",

    // ---- vault: locked view ----
    "vault.open.title": "Open a vault",
    "vault.open.hint": "A vault is a password-protected box that holds your files.",
    "vault.field.vaultFile": "Vault file",
    "vault.ph.openVault": "Choose your vault file…",
    "vault.field.password": "Password",
    "vault.ph.password": "password",
    "vault.btn.open": "Open vault",
    "vault.create.title": "Create a new vault",
    "vault.create.saveAs": "Save new vault as",
    "vault.ph.saveVault": "Choose where to save it…",
    "vault.create.confirm": "Confirm password",
    "vault.ph.repeat": "repeat password",
    "vault.create.typoWarn": "A typo here would lock you out permanently.",
    "vault.recovery.summary": "Set up recovery (optional)",
    "vault.recovery.hint": "If you might lose access, you can split a backup key into pieces now and restore from them later. Decide this when creating — you make the pieces after opening.",
    "vault.recovery.enable": "Enable recovery pieces",
    "vault.field.totalPieces": "Total pieces",
    "vault.field.neededRestore": "Needed to restore",
    "vault.recovery.example": "Example: 5 total, 3 needed → any 3 of the 5 pieces can restore it.",
    "vault.btn.create": "Create vault",
    "vault.more.summary": "More: recover from pieces, or check a vault file",
    "vault.recoverVault.title": "Recover a vault from pieces",
    "vault.recoverVault.hint": "If you can't open a vault the normal way, restore it from its recovery pieces. You need at least the “needed to restore” number; order doesn't matter.",
    "vault.ph.chooseVault": "Choose the vault file…",
    "vault.recoverVault.pieces": "Recovery pieces",
    "vault.ph.addPieces": "Add your recovery piece files…",
    "vault.btn.addPieceFiles": "Add piece files…",
    "vault.btn.recoverOpen": "Recover & open",
    "vault.check.title": "Check a vault file is intact",
    "vault.check.hint": "Confirm a vault file isn't damaged or tampered with — without opening it.",
    "vault.btn.checkIntact": "Check it's intact",
    "vault.btn.showFingerprint": "Show fingerprint",
    "vault.verifySig.title": "Check a signature (advanced)",
    "vault.verifySig.hint": "Same as “Check a signature” in the sidebar — verify a signed file against a public key.",
    "vault.field.signedFile": "Signed file",
    "vault.ph.signedFile": "Choose the signed file…",
    "vault.field.sigFile": "Signature file",
    "vault.ph.minisig": "Choose the .minisig file…",
    "vault.field.pubFile": "Public key file",
    "vault.ph.pubFile": "Choose the .pub file…",
    "vault.btn.checkSig": "Check signature",

    // ---- vault: unlocked view ----
    "vault.banner.default": "Vault",
    "vault.btn.lock": "Lock",
    "vault.files.title": "Files",
    "vault.files.add.ph.source": "Choose a file to add…",
    "vault.files.add.ph.name": "Name in the vault",
    "vault.btn.addFile": "Add file",
    "vault.files.empty": "No items yet. Add a file below.",
    "vault.files.saveCopy": "Save a copy…",
    "vault.sign.title": "Sign a file with this vault",
    "vault.sign.hint": "Adds a signature proving a file came from this vault and hasn't changed. Others check it with this vault's public key (in <strong>Vault details &amp; settings</strong>).",
    "vault.sign.field": "File to sign",
    "vault.ph.signFile": "Choose a file to sign…",
    "vault.btn.sign": "Sign file",
    "vault.shares.title": "Recovery pieces",
    "vault.shares.hint": "Split a backup key into pieces; any “needed to restore” number of them together can restore this vault. Store each piece in a separate trusted place.",
    "vault.shares.note": "Recovery only works if this vault was created with recovery enabled. Match the numbers to how the vault was set up, then store each piece separately.",
    "vault.shares.saveTo": "Save pieces to folder",
    "vault.ph.chooseFolder": "Choose a folder…",
    "vault.btn.makePieces": "Make recovery pieces",
    "vault.details.summary": "Vault details & settings",
    "vault.changePass.title": "Change password",
    "vault.changePass.hint": "Changes the password you type to open this vault. Recovery pieces still work.",
    "vault.changePass.new": "New password",
    "vault.ph.newPass": "new password",
    "vault.changePass.confirm": "Confirm new password",
    "vault.ph.repeatShort": "repeat",
    "vault.btn.changePass": "Change password",
    "vault.pubkey.title": "Public key",
    "vault.pubkey.hint": "Share this so others can verify files this vault signs: save it to a <code>.pub</code> file and use it in <strong>Check a signature</strong>.",
    "vault.pubkey.placeholder": "Click \"Show public key\".",
    "vault.btn.showPubkey": "Show public key",
    "vault.btn.copy": "Copy",
    "vault.tech.title": "Technical details",
    "vault.btn.checkVaultFile": "Check this vault file is intact",

    // ---- vault: dynamic (banner / meta / tech) ----
    "vault.summary.files": "{n} file",
    "vault.summary.files.plural": "{n} files",
    "vault.itemCount": "{n} item",
    "vault.itemCount.plural": "{n} items",
    "vault.summary.noRecovery": "no recovery set up",
    "vault.summary.recovery": "recovery: any {threshold} of {total}",
    "vault.tech.vaultId": "Vault ID: {id}",
    "vault.tech.format": "File format: version {version}",
    "vault.tech.kdf": "Password protection: {alg}, {mem} MiB, {passes} passes",
    "vault.note.recoveryReady": "This vault is set up for recovery: any {threshold} of {total} pieces can restore it. Make the pieces below and keep each one separate.",
    "vault.note.noRecovery": "This vault has no recovery set up, so pieces made here can't restore it. To use recovery, create a new vault with recovery enabled.",

    // ---- lock a file (encrypt) ----
    "enc.title": "🔐 Lock a file with a password",
    "enc.purpose": "Turn any file into a locked file only your password can open.",
    "enc.when.summary": "When should I use this?",
    "enc.when.body": "To send or store one sensitive file safely. Anyone with the password can open it — and there is <strong>no recovery</strong> if you forget the password.",
    "enc.step1": "1  Choose the file to lock",
    "enc.ph.input": "Drop a file here, or click Browse…",
    "enc.step2": "2  Set a password",
    "enc.confirm": "Confirm password",
    "enc.confirmWarn": "A typo here is unrecoverable — the file could never be opened.",
    "enc.step3": "3  Where to save the locked file",
    "enc.ph.output": "/path/to/file.svenc",
    "enc.tech": "▸ Technical details: Argon2id key derivation + secretbox (XSalsa20-Poly1305).",
    "enc.btn": "Lock file",

    // ---- unlock a file (decrypt) ----
    "dec.title": "🔓 Unlock a file",
    "dec.purpose": "Open a locked (<code>.svenc</code>) file with its password.",
    "dec.when.body": "To open a file that was locked with “Lock a file”. You need the password it was locked with.",
    "dec.step1": "1  Choose the locked file",
    "dec.ph.input": "Drop a .svenc file here, or Browse…",
    "dec.step2": "2  Password",
    "dec.step3": "3  Where to save the opened file",
    "dec.ph.output": "/path/to/recovered-file",
    "dec.btn": "Unlock file",

    // ---- hide data (stego) ----
    "hide.title": "🕵️ Hide data inside an image",
    "hide.purpose": "Encrypt a file with your password, then conceal it inside a PNG, BMP, or JPEG image.",
    "hide.when.body": "To tuck a small encrypted file inside an ordinary-looking image. The hiding place is <strong>not</strong> the protection — your <strong>password</strong> is. Concealment only makes the data less obvious; anyone who suspects it still cannot read it without the password.",
    "hide.step1": "1  Choose the cover image (PNG, BMP, or JPEG)",
    "hide.ph.cover": "Drop a PNG/BMP/JPEG here, or Browse…",
    "hide.cover.tech": "▸ Lossless <strong>PNG/BMP</strong> are the most discreet covers. <strong>JPEG</strong> works too (concealed in its DCT coefficients) but is <strong>inherently more detectable</strong> by steganalysis — prefer PNG/BMP when stealth matters. The output keeps the cover's format.",
    "hide.step2": "2  Choose the file to hide",
    "hide.ph.payload": "Drop the secret file here, or Browse…",
    "hide.step3": "3  Set a password",
    "hide.confirm": "Confirm password",
    "hide.confirmWarn": "A typo here is unrecoverable — the hidden data could never be read.",
    "hide.step4": "4  Where to save the image with hidden data",
    "hide.ph.output": "/path/to/output.png",
    "hide.out.tech": "▸ Saved in the cover's format. Technical details: encrypt-then-embed — Argon2id + secretbox, then LSB concealment.",
    "hide.randomize": "Scatter the data across the image (recommended)",
    "hide.btn": "Hide data",

    // ---- reveal hidden data ----
    "unhide.title": "🔓 Reveal data hidden in an image",
    "unhide.purpose": "Recover a file that was hidden with “Hide data”, using its password.",
    "unhide.when.body": "To pull back out a file you (or someone) hid inside an image. You need the password it was hidden with.",
    "unhide.step1": "1  Choose the image with hidden data",
    "unhide.ph.input": "Drop the PNG/BMP/JPEG here, or Browse…",
    "unhide.step2": "2  Password",
    "unhide.step3": "3  Choose the destination folder",
    "unhide.ph.output": "/path/to/destination/folder",
    "unhide.folder.hint": "The revealed file keeps its original name and extension automatically.",
    "unhide.btn": "Reveal data",

    // ---- detect hidden data ----
    "detect.title": "🔎 Detect hidden data",
    "detect.purpose": "Scan an image for signs of hidden data. Heuristic — it can flag suspicion, never prove innocence.",
    "detect.when.body": "For a quick, best-effort read on whether an image might carry concealed data (an appended file, LSB tampering). A low result means “nothing these tests caught” — <strong>not</strong> a guarantee the image is clean.",
    "detect.step1": "1  Choose the image to scan (PNG, BMP, or JPEG)",
    "detect.ph.input": "Drop a PNG/BMP/JPEG here, or Browse…",
    "detect.tech": "▸ For JPEG, the scan covers appended data (after the <code>EOI</code> marker) and DCT-coefficient LSB statistics; for PNG/BMP, appended data and pixel-LSB statistics.",
    "detect.btn": "Scan image",

    // ---- sign a file ----
    "sign.title": "✍️ Sign a file",
    "sign.purpose": "Prove a file came from you and hasn't changed since.",
    "sign.when.body": "So others can confirm a file is genuinely from you. You sign with your private key; they check with your public key. First create a signing identity below.",
    "sign.id.title": "First, your signing identity",
    "sign.id.hint": "Creates a keypair: a <strong>public key</strong> (<code>.pub</code> — share it so others can check your signatures) and a <strong>private key</strong> (<code>.svkey</code> — keep it secret; it's protected by a password).",
    "sign.id.saveTo": "Save identity to folder",
    "sign.ph.keyDir": "/path/to/output/dir",
    "sign.id.name": "Name this identity",
    "sign.ph.keyName": "my-signing-key",
    "sign.id.pass": "Password (protects the private key)",
    "sign.id.confirm": "Confirm password",
    "sign.btn.genkey": "Create signing identity",
    "sign.file.title": "Sign a file",
    "sign.file.hint": "Signs any file with your private key, writing <code>&lt;file&gt;.minisig</code> next to it.",
    "sign.file.toSign": "File to sign",
    "sign.ph.signInput": "/path/to/document.pdf",
    "sign.file.key": "Your private key (<code>.svkey</code>)",
    "sign.ph.signKey": "/path/to/my-signing-key.svkey",
    "sign.file.pass": "Password",
    "sign.btn.sign": "Sign file",

    // ---- check a signature ----
    "verify.title": "✅ Check a signature",
    "verify.purpose": "Confirm a file was signed by a specific person and hasn't changed.",
    "verify.when.body": "When you received a file plus a signature and the signer's public key, and want to be sure the file is genuine and unaltered.",
    "verify.step1": "1  The file",
    "verify.ph.file": "/path/to/document.pdf",
    "verify.step2": "2  The signature (<code>.minisig</code>)",
    "verify.ph.sig": "/path/to/document.pdf.minisig",
    "verify.step3": "3  Their public key (<code>.pub</code>)",
    "verify.ph.pub": "/path/to/signer.pub",
    "verify.btn": "Check",

    // ---- fingerprint a file ----
    "hash.title": "🔢 Fingerprint a file",
    "hash.purpose": "Get a unique ID (BLAKE3) of a file's exact contents.",
    "hash.when.body": "To compare two copies of a file, or to record a value you can re-check later. Two files with the same fingerprint are identical.",
    "hash.choose": "Choose a file",
    "hash.ph": "Drop a file here, or Browse…",
    "hash.btn": "Get fingerprint",

    // ---- watermark ----
    "wm.embed.title": "💧 Tamper-proof an image",
    "wm.embed.purpose": "Stamp an invisible, password-keyed mark into an image so you can later prove it hasn't been altered.",
    "wm.embed.when.body": "To make an image <strong>self-verifying</strong>: the mark is invisible and tied to your password. Later, “Check for tampering” tells you whether the image is unchanged, and <strong>which areas</strong> were altered if not. The mark is <strong>fragile by design</strong> — re-saving as JPEG, resizing, or any edit breaks it. Works on <strong>PNG/BMP</strong> only. This proves <em>integrity</em>, not authorship.",
    "wm.embed.step1": "1  Choose the image to mark (PNG or BMP)",
    "wm.embed.ph.input": "Drop a PNG/BMP here, or Browse…",
    "wm.embed.step2": "2  Set a password (the key for the mark)",
    "wm.embed.pass.tech": "▸ You'll need the same password to check for tampering later. Use a strong one — the mark's forgery-resistance depends on it.",
    "wm.embed.step3": "3  Where to save the marked image (PNG or BMP)",
    "wm.embed.ph.output": "/path/to/marked.png",
    "wm.embed.out.tech": "▸ Saved losslessly. Technical details: a per-block BLAKE3 keyed-MAC of the image content, keyed by Argon2id, embedded in the pixel LSBs. Your original is never changed.",
    "wm.embed.btn": "Add tamper-proof mark",
    "wm.verify.title": "🔍 Check for tampering",
    "wm.verify.purpose": "Verify a marked image against your password.",
    "wm.verify.step1": "1  Choose the marked image (PNG or BMP)",
    "wm.verify.ph.input": "Drop the marked PNG/BMP here, or Browse…",
    "wm.verify.step2": "2  Password",
    "wm.verify.btn": "Check for tampering",

    // ---- check a file is unchanged (intact) ----
    "intact.title": "🛡️ Check a file is unchanged",
    "intact.purpose": "Confirm a file still matches a fingerprint you were given.",
    "intact.when.body": "To check a download, backup, or shared file wasn't altered. You need the fingerprint the sender gave you (the same value <strong>Fingerprint a file</strong> produces). If you were given a signature file instead, use <strong>Check a signature</strong>.",
    "intact.step1": "1  Choose the file",
    "intact.ph.file": "Drop a file here, or Browse…",
    "intact.step2": "2  Paste the fingerprint you were given",
    "intact.ph.hash": "e.g. ab12cd…  (64 characters)",
    "intact.hashNote": "Spaces and capitalisation don't matter.",
    "intact.btn": "Check",

    // ---- verify a download (verify-integrity) ----
    "vi.title": "🧾 Verify a download",
    "vi.purpose": "Check a file against its published fingerprint and/or signature — in one step.",
    "vi.when.body": "When a file was published with a <strong>fingerprint</strong> (BLAKE3), a <strong>signature</strong> + the signer's public key, or both, and you want a single PASS/FAIL. Provide whichever you were given — at least one. (To check only one, <strong>Check a file is unchanged</strong> and <strong>Check a signature</strong> are the focused tools.)",
    "vi.step1": "1  Choose the file",
    "vi.ph.file": "Drop a file here, or Browse…",
    "vi.optional": "(optional)",
    "vi.step2": "2  Expected fingerprint",
    "vi.ph.hash": "e.g. ab12cd…  (64 characters)",
    "vi.hashNote": "Spaces and capitalisation don't matter.",
    "vi.step3.opt": "(optional, <code>.minisig</code>)",
    "vi.step3": "3  Signature",
    "vi.ph.sig": "/path/to/file.minisig",
    "vi.step4.opt": "(needed with a signature, <code>.pub</code>)",
    "vi.step4": "4  Signer's public key",
    "vi.ph.pub": "/path/to/signer.pub",
    "vi.btn": "Verify",

    // ---- split a secret ----
    "ss.title": "🧩 Split a secret",
    "ss.purpose": "Split a password, key, or note into pieces — any chosen number of them together restore it.",
    "ss.when.body": "To share trust across several people or places: no single piece reveals anything, but enough of them together rebuild the secret. You also get one <strong>payload file</strong> — keep it with the pieces; it's needed to recover. It's safe to copy, but don't lose it.",
    "ss.step1": "1  The secret to split",
    "ss.ph.secret": "Type or paste the secret (password, key, recovery phrase…)",
    "ss.secretNote": "Stays on this device. It isn't shown again after you split it.",
    "ss.step2": "2  Save the pieces to a folder",
    "ss.tech": "▸ Technical details: a random key is Shamir-split; the secret is sealed with secretbox (XSalsa20-Poly1305).",
    "ss.btn": "Split into pieces",

    // ---- split a file ----
    "sf.title": "🧩 Split a file",
    "sf.purpose": "Split a file into pieces — any chosen number of them together restore it.",
    "sf.when.body": "To back up a sensitive file (a keyfile, wallet, or document) across several locations. You get tiny piece files plus one <strong>payload file</strong> (the encrypted file); recovery needs the payload and enough pieces.",
    "sf.step1": "1  Choose the file to split",
    "sf.ph.input": "Drop a file here, or click Browse…",
    "sf.step2": "2  Save the pieces to a folder",
    "sf.btn": "Split into pieces",

    // ---- recover from pieces ----
    "rp.title": "🔗 Recover from pieces",
    "rp.purpose": "Rebuild a secret or file from enough of its pieces, plus the payload file.",
    "rp.when.body": "When you have at least the “needed to restore” number of pieces — as files (<code>.svss</code>) or pasted codes — together with the payload file they were made with.",
    "rp.step1": "1  Piece files",
    "rp.ph.files": "Drop piece files here, or click Add piece files…",
    "rp.btn.addFiles": "Add piece files…",
    "rp.orCodes": "Or paste piece codes (one per line)",
    "rp.ph.codes": "Paste Base64 piece codes, one per line (optional if you added files above)",
    "rp.step2": "2  The payload file",
    "rp.ph.payload": "Choose the .payload.svss file…",
    "rp.step3": "3  Where to save the recovered result",
    "rp.ph.output": "/path/to/recovered-output",
    "rp.btn": "Recover",

    // ---- secure QR transfer ----
    "qr.make.title": "📷 Secure QR transfer",
    "qr.make.purpose": "Move Secret Sharing pieces between devices as QR codes — turn pieces into QR images, and recover from scanned/saved QR images.",
    "qr.make.when.body": "After <strong>Split a secret</strong>, to carry the pieces by phone camera or print instead of copy-paste. Each QR holds <strong>one piece</strong> — non-secret on its own; a threshold of them <strong>plus the payload file</strong> rebuilds the secret. The payload file is <strong>not</strong> in the QR codes; move it alongside them.",
    "qr.make.step1": "1  Paste piece codes to turn into QR images (one per line)",
    "qr.make.ph.codes": "Paste the Base64 piece codes from “Split a secret”, one per line",
    "qr.make.tech": "▸ These are the same copy-paste codes shown after splitting a secret. Each line becomes one QR PNG.",
    "qr.make.step2": "2  Save the QR images to a folder",
    "qr.make.btn": "Make QR images",
    "qr.recover.title": "🔗 Recover from QR images",
    "qr.recover.purpose": "Rebuild a secret from enough QR images, plus the payload file.",
    "qr.recover.step1": "1  QR image files (PNG/JPEG)",
    "qr.recover.ph.images": "Drop QR images here, or click Add QR images…",
    "qr.recover.btn.addImages": "Add QR images…",
    "qr.recover.note": "▸ Add at least the “needed to restore” number of pieces.",
    "qr.recover.step2": "2  The payload file",
    "qr.recover.ph.payload": "Choose the .payload.svss file…",
    "qr.recover.step3": "3  Where to save the recovered result",
    "qr.recover.ph.output": "/path/to/recovered-output",
    "qr.recover.btn": "Recover from QR",

    // ---- coming-soon placeholders ----
    "soon.tag": "Coming soon",
    "soon.hide.title": "🕵️ Hide data inside a file",
    "soon.hide.what": "<strong>What it will do:</strong> conceal a file inside an image or audio file so it looks ordinary.",
    "soon.hide.when": "<strong>When you'd use it:</strong> to send something discreetly alongside a normal-looking file.",
    "soon.hide.status": "Status: under evaluation — not available yet.",
    "soon.detect.title": "🔎 Detect hidden data",
    "soon.detect.what": "<strong>What it will do:</strong> scan a file for signs of concealed data.",
    "soon.detect.status": "Status: under evaluation — not available yet.",

    // ---- inspect metadata ----
    "mi.title": "🔍 Inspect metadata",
    "mi.purpose": "See the hidden metadata a file carries — camera, location, author, software, timestamps.",
    "mi.when.body": "Before sharing a photo or document, to see what it quietly reveals about you — GPS coordinates, your name, the device, edit history. Reading is safe and never changes the file.",
    "mi.step1": "1  Choose the file to inspect",
    "mi.ph.file": "Drop any file here, or Browse…",
    "mi.tech": "▸ Works for images, PDFs, Office documents, audio, video, and more. Read-only.",
    "mi.btn": "Inspect",

    // ---- remove metadata ----
    "mc.title": "🧹 Remove metadata",
    "mc.purpose": "Write a clean copy of a file with its embedded metadata stripped out.",
    "mc.when.body": "Before publishing a photo or document, to scrub identifying metadata (GPS, device, author, software). Your original is never touched — a new, cleaned copy is written.",
    "mc.step1": "1  Choose the file to clean",
    "mc.ph.input": "Drop a file here, or Browse…",
    "mc.tech1": "▸ Images and WAV/AVI/MOV/MP4 are <strong>fully stripped</strong>. <strong>PDF</strong> is a best-effort scrub (the old metadata can still be recovered). Office documents, archives, and MP3/FLAC/MKV are <strong>inspect-only</strong> and will be refused here.",
    "mc.step2": "2  Where to save the cleaned copy",
    "mc.ph.output": "/path/to/cleaned-file",
    "mc.tech2": "▸ Keep the same file extension as the original so apps still open it. Technical details: <code>exiftool -all=</code> writes a fresh file; the input is never modified in place.",
    "mc.btn": "Remove metadata",

    // ---- compare metadata ----
    "cmp.title": "📑 Compare metadata",
    "cmp.purpose": "See how two files' embedded metadata differs — what's added, removed, or changed.",
    "cmp.when.body": "To confirm a cleaning step worked (compare original vs cleaned), or to see exactly what metadata two versions of a file carry. File names, sizes, and timestamps are ignored — only the real embedded metadata is compared.",
    "cmp.step1": "1  First file (A)",
    "cmp.ph.a": "Drop a file here, or Browse…",
    "cmp.step2": "2  Second file (B)",
    "cmp.ph.b": "Drop a file here, or Browse…",
    "cmp.btn": "Compare",

    // ---- about modal ----
    "about.title": "About",
    "about.close": "Close",
    "about.blurb": "Security & Privacy Toolkit — an offline desktop app that assembles vetted open-source security tools.",
    "about.version": "Version {app} · vault format v{fmt} · suite v{suite} · contract v{contract}",
    "about.attribution": "© Tracy Tran",

    // ---- shared buttons / labels ----
    "btn.browse": "Browse…",
    "btn.saveAs": "Save As…",
    "btn.chooseFolder": "Choose folder…",
    "btn.working": "Working…",
    "btn.copy": "Copy",
    "btn.copyCode": "Copy code",
    "action.showInFolder": "Show in folder",
    "action.openFile": "Open file",

    // ---- error code messages (keys here are referenced by the MESSAGES map in main.js) ----
    "err.notFound": "That file could not be found.",
    "err.malformed": "That file is not the expected type.",
    "err.incompatibleVersion": "This file needs a newer version of the app.",
    "err.corrupted": "This file is damaged or has been tampered with.",
    "err.unauthorized": "Wrong password, recovery shares, or tampered data.",
    "err.insufficientShares": "Not enough recovery shares.",
    "err.invalidInput": "Something about the input wasn't valid.",
    "err.io": "A file could not be read or written.",
    "err.tooLarge": "That file is too large.",
    "err.timeout": "The operation took too long and was stopped.",
    "err.outputExists": "A file already exists at that location.",
    "err.internal": "Something went wrong inside the app.",
    // refined error messages (with params)
    "err.insufficientShares.detail": "Not enough recovery shares: you added {got}, but {need} are needed.",
    "err.incompatibleVersion.detail": "This file is version {found}; this app supports version {supported}.",
    "err.tooLarge.detail": "That file is {actual}, over the {limit} limit.",
    "err.outputExists.detail": "A file already exists at that path — choose a different name so nothing is overwritten.",

    // ---- status messages ----
    "status.folderOpenCopied": "Couldn't open the folder here — path copied to clipboard.",
    "status.folderOpenFailed": "Couldn't open the folder.",
    "status.fileOpenCopied": "Couldn't open the file here — path copied to clipboard.",
    "status.fileOpenFailed": "Couldn't open the file.",
    "status.copied": "Copied to clipboard.",
    "status.copyFailed": "Couldn't copy — select the text manually.",
    "status.pickerUnavailable": "File picker isn't available here — type the path instead.",
    "status.fileAdded": "File added.",
    "status.savedTo": "Saved “{name}” to {dest}",
    "status.vaultOpened": "Vault opened.",
    "status.locked": "Locked.",
    "status.itemAdded": "Item added.",
    "status.recoveredOpened": "Recovered and opened.",
    "status.passwordChanged": "Password changed.",
    "status.pubkeyLoaded": "Public key loaded. Save it to a .pub file to let others verify your signatures.",
    "status.pubkeyCopied": "Public key copied to clipboard.",
    "status.pubkeySelectAll": "Select-all applied — press ⌘/Ctrl-C to copy.",
    "status.pieceCopied": "Piece code copied — keep it secret.",
    "status.pieceCopyFailed": "Couldn't copy — open the piece file instead.",
    "status.policyRecovery": "Recovery must satisfy 2 ≤ needed ≤ total ≤ 255.",
    "status.policyShares": "Shares must satisfy 2 ≤ needed ≤ total ≤ 255.",
    "status.policyPieces": "Pieces must satisfy 1 ≤ needed ≤ total ≤ 255.",

    // ---- validation (inline field errors) ----
    "v.create.path": "Choose where to save the new vault",
    "v.create.pass": "Set a password",
    "v.create.mismatch": "Passwords don't match. A typo here would lock you out permanently.",
    "v.unlock.path": "Choose the vault file",
    "v.unlock.pass": "Enter your password",
    "v.add.source": "Choose a file to add",
    "v.add.name": "Give it a name in the vault",
    "v.split.outdir": "Choose a folder for the share files",
    "v.recover.path": "Choose the vault file",
    "v.recover.shares": "Add at least one recovery share file.",
    "v.sign.file": "Choose a file to sign",
    "v.verify.file": "Choose the signed file",
    "v.verify.sig": "Choose the signature file",
    "v.verify.pub": "Choose the public key file",
    "v.integrity.path": "Choose the vault file",
    "v.changePass.new": "Enter a new password",
    "v.changePass.mismatch": "Passwords don't match.",
    "v.hash.file": "Choose a file",
    "v.tkverify.file": "Choose the file",
    "v.tkverify.sig": "Choose the signature file",
    "v.tkverify.pub": "Choose the public key file",
    "v.intact.file": "Choose a file",
    "v.intact.hash": "Paste the fingerprint you were given",
    "v.vi.file": "Choose the file",
    "v.vi.bothSig": "A signature check needs both the signature and the public key.",
    "v.vi.need": "Paste a fingerprint, or add a signature + public key.",
    "v.enc.input": "Choose a file to lock",
    "v.enc.output": "Choose where to save the locked file",
    "v.enc.pass": "Set a password",
    "v.enc.mismatch": "Passwords don't match. A typo here is unrecoverable.",
    "v.dec.input": "Choose the locked file",
    "v.dec.output": "Choose where to save the opened file",
    "v.dec.pass": "Enter the password",
    "v.hide.cover": "Choose a cover image",
    "v.hide.payload": "Choose the file to hide",
    "v.hide.output": "Choose where to save the image",
    "v.hide.pass": "Set a password",
    "v.unhide.input": "Choose the image with hidden data",
    "v.unhide.output": "Choose the destination folder",
    "v.unhide.pass": "Enter the password",
    "v.detect.input": "Choose an image to scan",
    "v.mi.file": "Choose a file to inspect",
    "v.mc.input": "Choose a file to clean",
    "v.mc.output": "Choose where to save the cleaned copy",
    "v.cmp.a": "Choose the first file",
    "v.cmp.b": "Choose the second file",
    "v.genkey.dir": "Choose a folder for the identity",
    "v.genkey.name": "Name this identity",
    "v.genkey.pass": "Set a password",
    "v.genkey.mismatch": "Passwords don't match.",
    "v.sign2.input": "Choose a file to sign",
    "v.sign2.key": "Choose your private key (.svkey)",
    "v.sign2.pass": "Enter the key's password",
    "v.ss.text": "Type the secret to split",
    "v.ss.outdir": "Choose a folder for the pieces",
    "v.sf.input": "Choose a file to split",
    "v.sf.outdir": "Choose a folder for the pieces",
    "v.rp.payload": "Choose the payload file",
    "v.rp.output": "Choose where to save the result",
    "v.rp.pieces": "Add at least one piece — a file or a pasted code.",
    "v.qr.outdir": "Choose a folder for the QR images",
    "v.qr.codes": "Paste at least one piece code (one per line).",
    "v.qr.payload": "Choose the payload file",
    "v.qr.output": "Choose where to save the result",
    "v.qr.images": "Add at least one QR image.",
    "v.wm.input": "Choose an image to mark",
    "v.wm.output": "Choose where to save the marked image",
    "v.wm.pass": "Set a password",
    "v.wmv.input": "Choose the marked image",
    "v.wmv.pass": "Enter the password",

    // ---- result cards: prefixes ----
    "res.ok.prefix": "✅ ",
    "res.bad.prefix": "❌ ",

    // ---- result: create vault ----
    "r.create.title": "Vault created",
    "r.create.msg.recovery": "Recovery is enabled — make the pieces after you open it.",
    "r.create.msg.plain": "Now open it: pick this file in “Open a vault” and enter your password.",
    "r.label.savedTo": "Saved to",
    "r.extract.title": "Saved a copy",
    "r.note": "Note",
    "r.ext.caveat": "If the saved file won’t open, rename it to add the original file’s extension (e.g. .pdf, .zip, .jpg).",
    "r.label.originalName": "Original file",
    "r.ext.mismatch": "Recovered as “{name}”. The name you chose differs — use “Save as …” below to keep the original name and extension.",
    "action.saveAsName": "Save as {name}",
    "meta.unavailable.title": "This tool isn’t available in this build",
    "meta.unavailable.msg": "Metadata features need a bundled ExifTool component, which isn’t included in this build. Inspect, Remove, and Compare are disabled here.",
    "r.create.openNow": "Open it now",

    // ---- result: split (vault) ----
    "r.split.title": "Created {n} recovery piece",
    "r.split.title.plural": "Created {n} recovery pieces",
    "r.split.msg": "Any {threshold} of them together can restore this vault. Store each in a separate trusted place.",
    "r.share.label": "Share {index} / {total}",

    // ---- result: sign (vault) ----
    "r.sign.title": "File signed with the vault key",
    "r.label.signature": "Signature",

    // ---- result: verify / integrity (vault) ----
    "r.verify.ok.title": "Signature is valid",
    "r.verify.ok.msg": "Signed with this key, and the file is unchanged.",
    "r.label.fingerprint": "Fingerprint",
    "r.verify.bad.title": "Signature does NOT match",
    "r.verify.bad.msg": "The file, signature, or public key is wrong, or the file changed.",
    "r.integrity.ok.title": "Vault is intact",
    "r.integrity.ok.msg": "Its signature and contents check out.",
    "r.integrity.bad.title": "Integrity check failed",
    "r.integrity.bad.msg": "This vault is damaged or has been tampered with.",
    "r.vaultHash.title": "Vault fingerprint",
    "r.label.blake3": "BLAKE3",
    "r.vaultCheck.ok.title": "This vault file is intact",
    "r.vaultCheck.bad.title": "This vault file failed the check",
    "r.vaultCheck.bad.msg": "It may be damaged or tampered with.",

    // ---- result: fingerprint a file ----
    "r.hash.title": "Fingerprint ready",
    "r.hash.msg": "Two files with the same fingerprint are identical.",

    // ---- result: check a signature (toolkit) ----
    "r.tkverify.ok.title": "Genuine",
    "r.tkverify.ok.msg": "Signed with this key, and the file is unchanged.",
    "r.tkverify.bad.title": "Does NOT match",
    "r.tkverify.bad.msg": "The file, signature, or public key is wrong, or the file changed.",

    // ---- result: check a file is unchanged ----
    "r.intact.ok.title": "Unchanged",
    "r.intact.ok.msg": "This file matches the fingerprint — it hasn't been altered.",
    "r.intact.bad.title": "Does NOT match",
    "r.intact.bad.msg": "This file doesn't match the fingerprint you provided — it may have changed, or be a different file.",
    "r.intact.thisFile": "This file",
    "r.intact.expected": "Expected",
    "r.intact.empty": "(empty)",

    // ---- result: verify a download ----
    "r.vi.ok.title": "Verified",
    "r.vi.ok.msg": "Every check you asked for passed — this file is exactly what was published.",
    "r.vi.bad.title": "Does NOT verify",
    "r.vi.bad.msg": "At least one check failed — the file may have changed, or an input is wrong.",
    "r.vi.fpMatch": "Fingerprint match",
    "r.vi.yes": "yes",
    "r.vi.no": "NO",
    "r.vi.sig": "Signature",
    "r.vi.valid": "valid",
    "r.vi.invalid": "INVALID",

    // ---- result: lock a file ----
    "r.enc.title": "File locked",
    "r.enc.msg": "Keep your password safe — it's the only way to open this file.",
    "r.enc.another": "Lock another file",
    "r.exists.title": "A file already exists there",
    "r.exists.msg": "Nothing was overwritten. Choose a different name and try again.",
    "r.exists.pickNew": "Pick a new name…",

    // ---- result: unlock a file ----
    "r.dec.title": "File unlocked",
    "r.dec.bad.title": "Couldn't unlock this file",
    "r.dec.bad.msg": "The password is wrong, or this isn't a valid locked file.",

    // ---- result: hide data ----
    "r.hide.title": "Data hidden",
    "r.hide.msg": "Keep your password safe — it's the only way to reveal this data.",
    "r.hide.size": "Hidden file size",
    "r.hide.capacity": "Capacity used",
    "r.hide.capacityVal": "{pct}% of {capacity}",
    "r.hide.tooBig.title": "File too big to hide",
    "r.hide.tooBig.msg": "The file you're hiding is larger than this image can hold. Use a bigger cover image, or hide a smaller file.",
    "r.hide.unsupported.title": "Unsupported image",
    "r.hide.unsupported.msg": "The cover must be a PNG or BMP image.",

    // ---- result: reveal data ----
    "r.unhide.title": "Data revealed",
    "r.label.size": "Size",
    "r.unhide.bad.title": "Couldn't reveal any data",
    "r.unhide.bad.msg": "The password is wrong, this image carries no hidden data, or it was altered — these are indistinguishable by design.",

    // ---- result: detect ----
    "r.detect.title": "Scan complete",
    "r.detect.msg.elevated": "This image shows signs that may indicate hidden data — treat it with suspicion.",
    "r.detect.msg.clean": "No strong signs of hidden data were found. This is not a guarantee the image is clean.",
    "r.detect.verdict": "Verdict",
    "r.detect.note": "Note",
    "r.detect.unsupported.title": "Unsupported image",
    "r.detect.unsupported.msg": "The image must be a PNG or BMP.",
    "detect.verdict.NotObserved": "Nothing detected by these tests",
    "detect.verdict.Low": "Low suspicion",
    "detect.verdict.Elevated": "Elevated suspicion",
    "detect.verdict.High": "High suspicion",

    // ---- result: inspect metadata ----
    "r.mi.title": "Metadata read",
    "r.mi.unknownType": "unknown type",
    "r.mi.fieldCount": "{n} field",
    "r.mi.fieldCount.plural": "{n} fields",
    "r.mi.msg": "{summary}. This includes file-system facts; embedded metadata is what travels with the file.",

    // ---- result: remove metadata ----
    "r.mc.format": "Format",
    "r.mc.before": "Metadata fields before",
    "r.mc.after": "Metadata fields after",
    "r.mc.removed": "Fields removed",
    "r.mc.ok.title": "Cleaned copy written",
    "r.mc.ok.msg": "All embedded metadata was removed. Your original file was not changed.",
    "r.mc.best.title": "Best-effort scrub written",
    "r.mc.best.msg": "This is a PDF: metadata was removed by an incremental update, so the previous values may still be recoverable from the file. For a guaranteed scrub, re-export the PDF from its source. Your original was not changed.",

    // ---- result: compare metadata ----
    "r.cmp.same.title": "Identical embedded metadata",
    "r.cmp.diff.title": "Differences found",
    "r.cmp.same.msg": "Both files carry the same embedded metadata. (File names, sizes, and timestamps are ignored.)",
    "r.cmp.diff.msg": "{n} difference in embedded metadata. (File names, sizes, and timestamps are ignored.)",
    "r.cmp.diff.msg.plural": "{n} differences in embedded metadata. (File names, sizes, and timestamps are ignored.)",
    "r.cmp.changed": "changed · {key}",
    "r.cmp.onlyA": "only in A · {name}",
    "r.cmp.onlyB": "only in B · {name}",
    "r.cmp.arrow": "{a}  →  {b}",

    // ---- result: generate signing keypair ----
    "r.genkey.title": "Signing identity created",
    "r.genkey.msg": "Keep the private key (.svkey) and its password safe. Share the public key so others can verify.",
    "r.genkey.pub": "Public key",
    "r.genkey.priv": "Private key",
    "r.genkey.pubHex": "Public (hex)",

    // ---- result: sign a file (toolkit) ----
    "r.sign2.title": "File signed",
    "r.sign2.checkSig": "Check this signature",
    "r.sign2.bad.title": "Couldn't sign",
    "r.sign2.bad.msg": "The password for this signing key is wrong.",

    // ---- result: split secret / file ----
    "r.piece.label": "Piece {index} / {total}",
    "r.ss.title": "Made {n} pieces",
    "r.ss.msg": "Any {threshold} together restore the secret. Keep the payload file with them — it's needed to recover. Each code below is secret; store the pieces separately.",
    "r.payload.label": "Payload file",
    "r.sf.title": "Made {n} pieces",
    "r.sf.msg": "Any {threshold} of these piece files plus the payload file can restore your file. Store each piece separately.",

    // ---- result: recover from pieces ----
    "r.recover.title": "Recovered",
    "r.recover.msg": "The pieces matched and the secret was rebuilt.",
    "r.recover.bad.title": "Couldn't recover",
    "r.recover.bad.msg": "These pieces don't match, are from a different split, or the payload is wrong or damaged.",

    // ---- result: QR make / recover ----
    "r.qrmake.title": "Made {n} QR image",
    "r.qrmake.title.plural": "Made {n} QR images",
    "r.qrmake.msg": "Each QR holds one piece. Move a threshold of them — plus the payload file — to recover.",
    "r.qr.pieceLabel": "Piece {n}",
    "r.qrrecover.title": "Recovered",
    "r.qrrecover.msg": "The QR pieces matched and the secret was rebuilt.",
    "r.qr.badRead.title": "Couldn't read a QR image",
    "r.qr.badRead.msg": "One of the images has no readable QR code. Re-capture it (sharper, well-lit, the whole code in frame) and try again.",

    // ---- result: watermark embed / verify ----
    "r.wm.title": "Tamper-proof mark added",
    "r.wm.msg": "This image is now self-verifying with your password. Any later edit — including re-saving as JPEG or resizing — will show up as tampering.",
    "r.wm.regions": "Check regions",
    "r.wm.bad.title": "Couldn't mark this image",
    "r.wmv.intact.title": "Intact",
    "r.wmv.intact.msg": "Every region checks out — this image is unchanged since it was marked with this password.",
    "r.wmv.regionsChecked": "Regions checked",
    "r.wmv.tampered.title": "Tampered",
    "r.wmv.tampered.msg": "This image was altered after marking. {tampered} of {total} regions changed.",
    "r.wmv.altered": "Altered regions",
    "r.wmv.alteredVal": "{tampered} of {total}",
    "r.wmv.none.title": "No valid mark",
    "r.wmv.none.msg": "No watermark was found for this password. The image may be unmarked, marked with a different password, re-saved as JPEG/resized (which destroys the mark), or entirely replaced.",
  };

  // =========================================================================
  // Vietnamese catalogue (the default locale). Same key set as EN.
  // =========================================================================
  const VI = {
    // ---- chrome / header ----
    "app.title": "🔒 Bộ công cụ Bảo mật & Riêng tư",
    "header.attribution": "© Tracy Tran • Secure Vault v0.1.0",
    "header.about": "Giới thiệu",
    "header.language": "Ngôn ngữ",
    "lang.vi": "Tiếng Việt",
    "lang.en": "English",

    // ---- sidebar groups + items ----
    "nav.group.vaults": "Két an toàn",
    "nav.group.protect": "Bảo vệ tệp",
    "nav.group.authentic": "Chứng minh tính xác thực",
    "nav.group.backup": "Sao lưu & khôi phục",
    "nav.group.inspect": "Kiểm tra & làm sạch",
    "nav.home": "🏠 Trang chủ",
    "nav.vault": "🗄️ Két an toàn",
    "nav.encrypt": "🔐 Khóa tệp",
    "nav.decrypt": "🔓 Mở khóa tệp",
    "nav.hide": "🕵️ Giấu dữ liệu trong ảnh",
    "nav.unhide": "🔓 Hiện dữ liệu ẩn",
    "nav.watermark": "💧 Chống giả mạo tệp",
    "nav.sign": "✍️ Ký tệp",
    "nav.verify": "✅ Kiểm tra chữ ký",
    "nav.hash": "🔢 Lấy vân tay tệp",
    "nav.intact": "🛡️ Kiểm tra tệp chưa bị đổi",
    "nav.verifyIntegrity": "🧾 Xác minh tệp tải về",
    "nav.splitSecret": "🧩 Chia nhỏ bí mật",
    "nav.splitFile": "🧩 Chia nhỏ tệp",
    "nav.recoverPieces": "🔗 Khôi phục từ các mảnh",
    "nav.qrTransfer": "📷 Chuyển qua mã QR an toàn",
    "nav.detect": "🔎 Phát hiện dữ liệu ẩn",
    "nav.metadataInspect": "🔍 Xem siêu dữ liệu",
    "nav.metadataClean": "🧹 Xóa siêu dữ liệu",
    "nav.metadataCompare": "📑 So sánh siêu dữ liệu",

    // ---- home ----
    "home.title": "Bạn muốn làm gì?",
    "home.hint": "Hãy chọn một tác vụ. Mỗi công cụ đều giải thích nó làm gì, cần gì, và bạn nhận được gì.",
    "home.recent": "Công cụ gần đây",
    "home.quickStart": "Bắt đầu nhanh",
    "home.allTools": "Tất cả công cụ",
    "home.q.encrypt.title": "Khóa tệp",
    "home.q.encrypt.desc": "Bảo vệ một tệp bằng mật khẩu.",
    "home.q.intact.title": "Kiểm tra tệp chưa bị đổi",
    "home.q.intact.desc": "Xác nhận tệp khớp với vân tay bạn được cung cấp.",
    "home.q.vault.title": "Mở két an toàn",
    "home.q.vault.desc": "Hộp chứa tệp được bảo vệ bằng mật khẩu của bạn.",
    "home.t.encrypt": "Khóa tệp",
    "home.t.decrypt": "Mở khóa tệp",
    "home.t.sign": "Ký tệp",
    "home.t.verify": "Kiểm tra chữ ký",
    "home.t.hash": "Lấy vân tay tệp",
    "home.t.intact": "Kiểm tra tệp chưa bị đổi",
    "home.t.vault": "Két an toàn",
    "home.t.splitSecret": "Chia nhỏ bí mật",
    "home.t.splitFile": "Chia nhỏ tệp",
    "home.t.recover": "Khôi phục từ các mảnh",
    "home.t.hide": "Giấu dữ liệu",
    "home.t.detect": "Phát hiện dữ liệu ẩn",
    "home.t.metadata": "Công cụ siêu dữ liệu",
    "home.soon": "sắp có",

    // ---- vault: shared ----
    "vault.title": "🗄️ Két an toàn",
    "vault.badge.locked": "Đã khóa",
    "vault.badge.unlocked": "Đã mở",

    // ---- vault: locked view ----
    "vault.open.title": "Mở két an toàn",
    "vault.open.hint": "Két an toàn là một hộp được bảo vệ bằng mật khẩu để chứa các tệp của bạn.",
    "vault.field.vaultFile": "Tệp két",
    "vault.ph.openVault": "Chọn tệp két của bạn…",
    "vault.field.password": "Mật khẩu",
    "vault.ph.password": "mật khẩu",
    "vault.btn.open": "Mở két",
    "vault.create.title": "Tạo két mới",
    "vault.create.saveAs": "Lưu két mới thành",
    "vault.ph.saveVault": "Chọn nơi lưu…",
    "vault.create.confirm": "Xác nhận mật khẩu",
    "vault.ph.repeat": "nhập lại mật khẩu",
    "vault.create.typoWarn": "Gõ sai ở đây sẽ khiến bạn mất quyền truy cập vĩnh viễn.",
    "vault.recovery.summary": "Thiết lập khôi phục (tùy chọn)",
    "vault.recovery.hint": "Nếu bạn có thể mất quyền truy cập, bạn có thể chia khóa dự phòng thành nhiều mảnh ngay bây giờ và khôi phục từ chúng sau này. Hãy quyết định khi tạo — bạn tạo các mảnh sau khi mở.",
    "vault.recovery.enable": "Bật các mảnh khôi phục",
    "vault.field.totalPieces": "Tổng số mảnh",
    "vault.field.neededRestore": "Số mảnh cần để khôi phục",
    "vault.recovery.example": "Ví dụ: tổng 5, cần 3 → bất kỳ 3 trong 5 mảnh đều có thể khôi phục.",
    "vault.btn.create": "Tạo két",
    "vault.more.summary": "Thêm: khôi phục từ các mảnh, hoặc kiểm tra tệp két",
    "vault.recoverVault.title": "Khôi phục két từ các mảnh",
    "vault.recoverVault.hint": "Nếu không thể mở két theo cách thông thường, hãy khôi phục nó từ các mảnh khôi phục. Bạn cần ít nhất số mảnh “cần để khôi phục”; thứ tự không quan trọng.",
    "vault.ph.chooseVault": "Chọn tệp két…",
    "vault.recoverVault.pieces": "Các mảnh khôi phục",
    "vault.ph.addPieces": "Thêm các tệp mảnh khôi phục của bạn…",
    "vault.btn.addPieceFiles": "Thêm tệp mảnh…",
    "vault.btn.recoverOpen": "Khôi phục & mở",
    "vault.check.title": "Kiểm tra tệp két còn nguyên vẹn",
    "vault.check.hint": "Xác nhận tệp két không bị hỏng hay bị can thiệp — mà không cần mở nó.",
    "vault.btn.checkIntact": "Kiểm tra nguyên vẹn",
    "vault.btn.showFingerprint": "Hiện vân tay",
    "vault.verifySig.title": "Kiểm tra chữ ký (nâng cao)",
    "vault.verifySig.hint": "Giống “Kiểm tra chữ ký” ở thanh bên — xác minh tệp đã ký với một khóa công khai.",
    "vault.field.signedFile": "Tệp đã ký",
    "vault.ph.signedFile": "Chọn tệp đã ký…",
    "vault.field.sigFile": "Tệp chữ ký",
    "vault.ph.minisig": "Chọn tệp .minisig…",
    "vault.field.pubFile": "Tệp khóa công khai",
    "vault.ph.pubFile": "Chọn tệp .pub…",
    "vault.btn.checkSig": "Kiểm tra chữ ký",

    // ---- vault: unlocked view ----
    "vault.banner.default": "Két",
    "vault.btn.lock": "Khóa",
    "vault.files.title": "Tệp",
    "vault.files.add.ph.source": "Chọn tệp để thêm…",
    "vault.files.add.ph.name": "Tên trong két",
    "vault.btn.addFile": "Thêm tệp",
    "vault.files.empty": "Chưa có mục nào. Hãy thêm một tệp bên dưới.",
    "vault.files.saveCopy": "Lưu một bản…",
    "vault.sign.title": "Ký một tệp bằng két này",
    "vault.sign.hint": "Thêm chữ ký chứng minh tệp đến từ két này và chưa bị thay đổi. Người khác kiểm tra bằng khóa công khai của két (trong <strong>Chi tiết &amp; cài đặt két</strong>).",
    "vault.sign.field": "Tệp cần ký",
    "vault.ph.signFile": "Chọn tệp để ký…",
    "vault.btn.sign": "Ký tệp",
    "vault.shares.title": "Các mảnh khôi phục",
    "vault.shares.hint": "Chia khóa dự phòng thành nhiều mảnh; bất kỳ số mảnh “cần để khôi phục” nào gộp lại đều có thể khôi phục két này. Hãy cất mỗi mảnh ở một nơi tin cậy riêng.",
    "vault.shares.note": "Khôi phục chỉ hoạt động nếu két được tạo với chế độ khôi phục bật. Hãy khớp các con số với cách két được thiết lập, rồi cất riêng mỗi mảnh.",
    "vault.shares.saveTo": "Lưu các mảnh vào thư mục",
    "vault.ph.chooseFolder": "Chọn một thư mục…",
    "vault.btn.makePieces": "Tạo các mảnh khôi phục",
    "vault.details.summary": "Chi tiết & cài đặt két",
    "vault.changePass.title": "Đổi mật khẩu",
    "vault.changePass.hint": "Đổi mật khẩu bạn gõ để mở két này. Các mảnh khôi phục vẫn hoạt động.",
    "vault.changePass.new": "Mật khẩu mới",
    "vault.ph.newPass": "mật khẩu mới",
    "vault.changePass.confirm": "Xác nhận mật khẩu mới",
    "vault.ph.repeatShort": "nhập lại",
    "vault.btn.changePass": "Đổi mật khẩu",
    "vault.pubkey.title": "Khóa công khai",
    "vault.pubkey.hint": "Chia sẻ khóa này để người khác xác minh các tệp két này ký: lưu vào một tệp <code>.pub</code> và dùng trong <strong>Kiểm tra chữ ký</strong>.",
    "vault.pubkey.placeholder": "Bấm \"Hiện khóa công khai\".",
    "vault.btn.showPubkey": "Hiện khóa công khai",
    "vault.btn.copy": "Sao chép",
    "vault.tech.title": "Chi tiết kỹ thuật",
    "vault.btn.checkVaultFile": "Kiểm tra tệp két này còn nguyên vẹn",

    // ---- vault: dynamic (banner / meta / tech) ----
    "vault.summary.files": "{n} tệp",
    "vault.summary.files.plural": "{n} tệp",
    "vault.itemCount": "{n} mục",
    "vault.itemCount.plural": "{n} mục",
    "vault.summary.noRecovery": "chưa thiết lập khôi phục",
    "vault.summary.recovery": "khôi phục: bất kỳ {threshold} trong {total}",
    "vault.tech.vaultId": "Mã két: {id}",
    "vault.tech.format": "Định dạng tệp: phiên bản {version}",
    "vault.tech.kdf": "Bảo vệ mật khẩu: {alg}, {mem} MiB, {passes} lượt",
    "vault.note.recoveryReady": "Két này được thiết lập để khôi phục: bất kỳ {threshold} trong {total} mảnh đều có thể khôi phục. Hãy tạo các mảnh bên dưới và cất riêng mỗi mảnh.",
    "vault.note.noRecovery": "Két này chưa thiết lập khôi phục, nên các mảnh tạo ở đây không thể khôi phục nó. Để dùng khôi phục, hãy tạo một két mới với chế độ khôi phục bật.",

    // ---- lock a file (encrypt) ----
    "enc.title": "🔐 Khóa tệp bằng mật khẩu",
    "enc.purpose": "Biến bất kỳ tệp nào thành tệp đã khóa mà chỉ mật khẩu của bạn mới mở được.",
    "enc.when.summary": "Khi nào nên dùng?",
    "enc.when.body": "Để gửi hoặc lưu trữ an toàn một tệp nhạy cảm. Bất kỳ ai có mật khẩu đều mở được — và <strong>không có cách khôi phục</strong> nếu bạn quên mật khẩu.",
    "enc.step1": "1  Chọn tệp cần khóa",
    "enc.ph.input": "Kéo thả tệp vào đây, hoặc bấm Duyệt…",
    "enc.step2": "2  Đặt mật khẩu",
    "enc.confirm": "Xác nhận mật khẩu",
    "enc.confirmWarn": "Gõ sai ở đây là không thể khôi phục — tệp sẽ không bao giờ mở được.",
    "enc.step3": "3  Nơi lưu tệp đã khóa",
    "enc.ph.output": "/đường-dẫn/tới/tệp.svenc",
    "enc.tech": "▸ Chi tiết kỹ thuật: dẫn xuất khóa Argon2id + secretbox (XSalsa20-Poly1305).",
    "enc.btn": "Khóa tệp",

    // ---- unlock a file (decrypt) ----
    "dec.title": "🔓 Mở khóa tệp",
    "dec.purpose": "Mở một tệp đã khóa (<code>.svenc</code>) bằng mật khẩu của nó.",
    "dec.when.body": "Để mở một tệp đã được khóa bằng “Khóa tệp”. Bạn cần mật khẩu đã dùng để khóa nó.",
    "dec.step1": "1  Chọn tệp đã khóa",
    "dec.ph.input": "Kéo thả tệp .svenc vào đây, hoặc Duyệt…",
    "dec.step2": "2  Mật khẩu",
    "dec.step3": "3  Nơi lưu tệp đã mở",
    "dec.ph.output": "/đường-dẫn/tới/tệp-khôi-phục",
    "dec.btn": "Mở khóa tệp",

    // ---- hide data (stego) ----
    "hide.title": "🕵️ Giấu dữ liệu bên trong ảnh",
    "hide.purpose": "Mã hóa một tệp bằng mật khẩu, rồi giấu nó bên trong ảnh PNG, BMP hoặc JPEG.",
    "hide.when.body": "Để giấu một tệp nhỏ đã mã hóa bên trong một ảnh trông bình thường. Nơi giấu <strong>không phải</strong> là sự bảo vệ — <strong>mật khẩu</strong> của bạn mới là. Việc che giấu chỉ làm dữ liệu bớt lộ; ai nghi ngờ vẫn không đọc được nếu không có mật khẩu.",
    "hide.step1": "1  Chọn ảnh nền (PNG, BMP hoặc JPEG)",
    "hide.ph.cover": "Kéo thả PNG/BMP/JPEG vào đây, hoặc Duyệt…",
    "hide.cover.tech": "▸ Ảnh nền <strong>PNG/BMP</strong> không mất dữ liệu là kín đáo nhất. <strong>JPEG</strong> cũng được (giấu trong các hệ số DCT) nhưng <strong>vốn dễ bị phát hiện hơn</strong> bằng phân tích giấu tin — hãy ưu tiên PNG/BMP khi cần kín đáo. Kết quả giữ nguyên định dạng của ảnh nền.",
    "hide.step2": "2  Chọn tệp cần giấu",
    "hide.ph.payload": "Kéo thả tệp bí mật vào đây, hoặc Duyệt…",
    "hide.step3": "3  Đặt mật khẩu",
    "hide.confirm": "Xác nhận mật khẩu",
    "hide.confirmWarn": "Gõ sai ở đây là không thể khôi phục — dữ liệu giấu sẽ không bao giờ đọc được.",
    "hide.step4": "4  Nơi lưu ảnh có dữ liệu giấu",
    "hide.ph.output": "/đường-dẫn/tới/ket-qua.png",
    "hide.out.tech": "▸ Lưu theo định dạng của ảnh nền. Chi tiết kỹ thuật: mã hóa rồi nhúng — Argon2id + secretbox, sau đó giấu theo bit LSB.",
    "hide.randomize": "Rải dữ liệu khắp ảnh (khuyên dùng)",
    "hide.btn": "Giấu dữ liệu",

    // ---- reveal hidden data ----
    "unhide.title": "🔓 Hiện dữ liệu giấu trong ảnh",
    "unhide.purpose": "Khôi phục một tệp đã được giấu bằng “Giấu dữ liệu”, dùng mật khẩu của nó.",
    "unhide.when.body": "Để lấy lại một tệp mà bạn (hoặc ai đó) đã giấu trong ảnh. Bạn cần mật khẩu đã dùng để giấu nó.",
    "unhide.step1": "1  Chọn ảnh có dữ liệu giấu",
    "unhide.ph.input": "Kéo thả PNG/BMP/JPEG vào đây, hoặc Duyệt…",
    "unhide.step2": "2  Mật khẩu",
    "unhide.step3": "3  Chọn thư mục đích",
    "unhide.ph.output": "/đường-dẫn/tới/thư-mục-đích",
    "unhide.folder.hint": "Tệp được hiện ra sẽ tự động giữ nguyên tên và phần mở rộng gốc.",
    "unhide.btn": "Hiện dữ liệu",

    // ---- detect hidden data ----
    "detect.title": "🔎 Phát hiện dữ liệu ẩn",
    "detect.purpose": "Quét ảnh tìm dấu hiệu dữ liệu ẩn. Mang tính suy đoán — có thể cảnh báo nghi ngờ, nhưng không bao giờ chứng minh là sạch.",
    "detect.when.body": "Để có một đánh giá nhanh, theo khả năng tốt nhất, về việc ảnh có thể chứa dữ liệu ẩn hay không (tệp nối thêm, can thiệp LSB). Kết quả thấp nghĩa là “những phép thử này không bắt được gì” — <strong>không</strong> phải đảm bảo ảnh sạch.",
    "detect.step1": "1  Chọn ảnh cần quét (PNG, BMP hoặc JPEG)",
    "detect.ph.input": "Kéo thả PNG/BMP/JPEG vào đây, hoặc Duyệt…",
    "detect.tech": "▸ Với JPEG, phép quét xét dữ liệu nối thêm (sau dấu <code>EOI</code>) và thống kê LSB của hệ số DCT; với PNG/BMP, xét dữ liệu nối thêm và thống kê LSB của điểm ảnh.",
    "detect.btn": "Quét ảnh",

    // ---- sign a file ----
    "sign.title": "✍️ Ký tệp",
    "sign.purpose": "Chứng minh một tệp đến từ bạn và chưa thay đổi kể từ đó.",
    "sign.when.body": "Để người khác xác nhận một tệp thực sự đến từ bạn. Bạn ký bằng khóa bí mật; họ kiểm tra bằng khóa công khai của bạn. Trước tiên hãy tạo một danh tính ký bên dưới.",
    "sign.id.title": "Trước tiên, danh tính ký của bạn",
    "sign.id.hint": "Tạo một cặp khóa: một <strong>khóa công khai</strong> (<code>.pub</code> — chia sẻ để người khác kiểm tra chữ ký của bạn) và một <strong>khóa bí mật</strong> (<code>.svkey</code> — giữ bí mật; được bảo vệ bằng mật khẩu).",
    "sign.id.saveTo": "Lưu danh tính vào thư mục",
    "sign.ph.keyDir": "/đường-dẫn/tới/thư-mục-xuất",
    "sign.id.name": "Đặt tên cho danh tính này",
    "sign.ph.keyName": "khoa-ky-cua-toi",
    "sign.id.pass": "Mật khẩu (bảo vệ khóa bí mật)",
    "sign.id.confirm": "Xác nhận mật khẩu",
    "sign.btn.genkey": "Tạo danh tính ký",
    "sign.file.title": "Ký một tệp",
    "sign.file.hint": "Ký bất kỳ tệp nào bằng khóa bí mật của bạn, ghi tệp <code>&lt;tệp&gt;.minisig</code> bên cạnh nó.",
    "sign.file.toSign": "Tệp cần ký",
    "sign.ph.signInput": "/đường-dẫn/tới/tai-lieu.pdf",
    "sign.file.key": "Khóa bí mật của bạn (<code>.svkey</code>)",
    "sign.ph.signKey": "/đường-dẫn/tới/khoa-ky-cua-toi.svkey",
    "sign.file.pass": "Mật khẩu",
    "sign.btn.sign": "Ký tệp",

    // ---- check a signature ----
    "verify.title": "✅ Kiểm tra chữ ký",
    "verify.purpose": "Xác nhận một tệp đã được ký bởi một người cụ thể và chưa thay đổi.",
    "verify.when.body": "Khi bạn nhận được một tệp kèm chữ ký và khóa công khai của người ký, và muốn chắc chắn tệp là thật và chưa bị sửa.",
    "verify.step1": "1  Tệp",
    "verify.ph.file": "/đường-dẫn/tới/tai-lieu.pdf",
    "verify.step2": "2  Chữ ký (<code>.minisig</code>)",
    "verify.ph.sig": "/đường-dẫn/tới/tai-lieu.pdf.minisig",
    "verify.step3": "3  Khóa công khai của họ (<code>.pub</code>)",
    "verify.ph.pub": "/đường-dẫn/tới/nguoi-ky.pub",
    "verify.btn": "Kiểm tra",

    // ---- fingerprint a file ----
    "hash.title": "🔢 Lấy vân tay tệp",
    "hash.purpose": "Lấy một mã nhận dạng duy nhất (BLAKE3) của đúng nội dung tệp.",
    "hash.when.body": "Để so sánh hai bản của một tệp, hoặc ghi lại một giá trị để kiểm tra lại sau. Hai tệp có cùng vân tay là giống hệt nhau.",
    "hash.choose": "Chọn một tệp",
    "hash.ph": "Kéo thả tệp vào đây, hoặc Duyệt…",
    "hash.btn": "Lấy vân tay",

    // ---- watermark ----
    "wm.embed.title": "💧 Chống giả mạo ảnh",
    "wm.embed.purpose": "Đóng một dấu vô hình, khóa bằng mật khẩu vào ảnh để sau này bạn có thể chứng minh nó chưa bị sửa.",
    "wm.embed.when.body": "Để ảnh có thể <strong>tự xác minh</strong>: dấu là vô hình và gắn với mật khẩu của bạn. Sau này, “Kiểm tra giả mạo” cho biết ảnh có còn nguyên vẹn không, và <strong>vùng nào</strong> bị sửa nếu có. Dấu <strong>vốn dễ vỡ theo thiết kế</strong> — lưu lại thành JPEG, đổi kích thước, hay bất kỳ chỉnh sửa nào đều phá vỡ nó. Chỉ dùng cho <strong>PNG/BMP</strong>. Điều này chứng minh <em>tính toàn vẹn</em>, không phải tác giả.",
    "wm.embed.step1": "1  Chọn ảnh cần đánh dấu (PNG hoặc BMP)",
    "wm.embed.ph.input": "Kéo thả PNG/BMP vào đây, hoặc Duyệt…",
    "wm.embed.step2": "2  Đặt mật khẩu (khóa cho dấu)",
    "wm.embed.pass.tech": "▸ Bạn sẽ cần đúng mật khẩu này để kiểm tra giả mạo sau. Hãy dùng mật khẩu mạnh — khả năng chống làm giả của dấu phụ thuộc vào nó.",
    "wm.embed.step3": "3  Nơi lưu ảnh đã đánh dấu (PNG hoặc BMP)",
    "wm.embed.ph.output": "/đường-dẫn/tới/anh-da-danh-dau.png",
    "wm.embed.out.tech": "▸ Lưu không mất dữ liệu. Chi tiết kỹ thuật: một MAC khóa BLAKE3 theo từng khối của nội dung ảnh, khóa bằng Argon2id, nhúng vào bit LSB của điểm ảnh. Ảnh gốc của bạn không bao giờ bị thay đổi.",
    "wm.embed.btn": "Thêm dấu chống giả mạo",
    "wm.verify.title": "🔍 Kiểm tra giả mạo",
    "wm.verify.purpose": "Xác minh một ảnh đã đánh dấu với mật khẩu của bạn.",
    "wm.verify.step1": "1  Chọn ảnh đã đánh dấu (PNG hoặc BMP)",
    "wm.verify.ph.input": "Kéo thả ảnh PNG/BMP đã đánh dấu vào đây, hoặc Duyệt…",
    "wm.verify.step2": "2  Mật khẩu",
    "wm.verify.btn": "Kiểm tra giả mạo",

    // ---- check a file is unchanged (intact) ----
    "intact.title": "🛡️ Kiểm tra tệp chưa bị đổi",
    "intact.purpose": "Xác nhận một tệp vẫn khớp với vân tay bạn được cung cấp.",
    "intact.when.body": "Để kiểm tra một tệp tải về, bản sao lưu, hay tệp được chia sẻ chưa bị sửa. Bạn cần vân tay mà người gửi cung cấp (cùng giá trị mà <strong>Lấy vân tay tệp</strong> tạo ra). Nếu bạn được cung cấp một tệp chữ ký thay vì vân tay, hãy dùng <strong>Kiểm tra chữ ký</strong>.",
    "intact.step1": "1  Chọn tệp",
    "intact.ph.file": "Kéo thả tệp vào đây, hoặc Duyệt…",
    "intact.step2": "2  Dán vân tay bạn được cung cấp",
    "intact.ph.hash": "vd. ab12cd…  (64 ký tự)",
    "intact.hashNote": "Khoảng trắng và chữ hoa/thường không quan trọng.",
    "intact.btn": "Kiểm tra",

    // ---- verify a download (verify-integrity) ----
    "vi.title": "🧾 Xác minh tệp tải về",
    "vi.purpose": "Kiểm tra một tệp với vân tay và/hoặc chữ ký đã công bố của nó — trong một bước.",
    "vi.when.body": "Khi một tệp được công bố kèm một <strong>vân tay</strong> (BLAKE3), một <strong>chữ ký</strong> + khóa công khai của người ký, hoặc cả hai, và bạn muốn một kết quả ĐẠT/KHÔNG ĐẠT duy nhất. Hãy cung cấp thứ bạn có — ít nhất một. (Để chỉ kiểm tra một thứ, <strong>Kiểm tra tệp chưa bị đổi</strong> và <strong>Kiểm tra chữ ký</strong> là các công cụ chuyên biệt.)",
    "vi.step1": "1  Chọn tệp",
    "vi.ph.file": "Kéo thả tệp vào đây, hoặc Duyệt…",
    "vi.optional": "(tùy chọn)",
    "vi.step2": "2  Vân tay mong đợi",
    "vi.ph.hash": "vd. ab12cd…  (64 ký tự)",
    "vi.hashNote": "Khoảng trắng và chữ hoa/thường không quan trọng.",
    "vi.step3.opt": "(tùy chọn, <code>.minisig</code>)",
    "vi.step3": "3  Chữ ký",
    "vi.ph.sig": "/đường-dẫn/tới/tệp.minisig",
    "vi.step4.opt": "(cần khi có chữ ký, <code>.pub</code>)",
    "vi.step4": "4  Khóa công khai của người ký",
    "vi.ph.pub": "/đường-dẫn/tới/nguoi-ky.pub",
    "vi.btn": "Xác minh",

    // ---- split a secret ----
    "ss.title": "🧩 Chia nhỏ bí mật",
    "ss.purpose": "Chia một mật khẩu, khóa, hay ghi chú thành nhiều mảnh — bất kỳ số lượng đã chọn nào gộp lại đều khôi phục được.",
    "ss.when.body": "Để chia sẻ sự tin cậy giữa nhiều người hoặc nhiều nơi: không mảnh đơn lẻ nào tiết lộ điều gì, nhưng đủ số mảnh gộp lại sẽ dựng lại bí mật. Bạn cũng nhận được một <strong>tệp dữ liệu (payload)</strong> — hãy giữ nó cùng các mảnh; nó cần thiết để khôi phục. Sao chép thì an toàn, nhưng đừng làm mất.",
    "ss.step1": "1  Bí mật cần chia",
    "ss.ph.secret": "Gõ hoặc dán bí mật (mật khẩu, khóa, cụm từ khôi phục…)",
    "ss.secretNote": "Ở lại trên thiết bị này. Nó sẽ không hiện lại sau khi bạn chia.",
    "ss.step2": "2  Lưu các mảnh vào một thư mục",
    "ss.tech": "▸ Chi tiết kỹ thuật: một khóa ngẫu nhiên được chia Shamir; bí mật được niêm phong bằng secretbox (XSalsa20-Poly1305).",
    "ss.btn": "Chia thành các mảnh",

    // ---- split a file ----
    "sf.title": "🧩 Chia nhỏ tệp",
    "sf.purpose": "Chia một tệp thành nhiều mảnh — bất kỳ số lượng đã chọn nào gộp lại đều khôi phục được.",
    "sf.when.body": "Để sao lưu một tệp nhạy cảm (tệp khóa, ví, hay tài liệu) ở nhiều nơi. Bạn nhận được các tệp mảnh nhỏ cùng một <strong>tệp dữ liệu (payload)</strong> (tệp đã mã hóa); khôi phục cần payload và đủ số mảnh.",
    "sf.step1": "1  Chọn tệp cần chia",
    "sf.ph.input": "Kéo thả tệp vào đây, hoặc bấm Duyệt…",
    "sf.step2": "2  Lưu các mảnh vào một thư mục",
    "sf.btn": "Chia thành các mảnh",

    // ---- recover from pieces ----
    "rp.title": "🔗 Khôi phục từ các mảnh",
    "rp.purpose": "Dựng lại một bí mật hoặc tệp từ đủ số mảnh của nó, cùng tệp dữ liệu (payload).",
    "rp.when.body": "Khi bạn có ít nhất số mảnh “cần để khôi phục” — dạng tệp (<code>.svss</code>) hoặc mã đã dán — cùng với tệp dữ liệu (payload) mà chúng được tạo ra cùng.",
    "rp.step1": "1  Các tệp mảnh",
    "rp.ph.files": "Kéo thả tệp mảnh vào đây, hoặc bấm Thêm tệp mảnh…",
    "rp.btn.addFiles": "Thêm tệp mảnh…",
    "rp.orCodes": "Hoặc dán mã mảnh (mỗi dòng một mã)",
    "rp.ph.codes": "Dán mã mảnh Base64, mỗi dòng một mã (tùy chọn nếu bạn đã thêm tệp ở trên)",
    "rp.step2": "2  Tệp dữ liệu (payload)",
    "rp.ph.payload": "Chọn tệp .payload.svss…",
    "rp.step3": "3  Nơi lưu kết quả khôi phục",
    "rp.ph.output": "/đường-dẫn/tới/ket-qua-khoi-phuc",
    "rp.btn": "Khôi phục",

    // ---- secure QR transfer ----
    "qr.make.title": "📷 Chuyển qua mã QR an toàn",
    "qr.make.purpose": "Chuyển các mảnh Chia sẻ Bí mật giữa các thiết bị dưới dạng mã QR — biến các mảnh thành ảnh QR, và khôi phục từ ảnh QR đã quét/lưu.",
    "qr.make.when.body": "Sau <strong>Chia nhỏ bí mật</strong>, để mang các mảnh bằng camera điện thoại hoặc in ra thay vì sao chép-dán. Mỗi QR chứa <strong>một mảnh</strong> — tự nó không bí mật; một ngưỡng số mảnh <strong>cùng tệp dữ liệu (payload)</strong> sẽ dựng lại bí mật. Tệp payload <strong>không</strong> nằm trong các mã QR; hãy chuyển nó kèm theo.",
    "qr.make.step1": "1  Dán mã mảnh để biến thành ảnh QR (mỗi dòng một mã)",
    "qr.make.ph.codes": "Dán mã mảnh Base64 từ “Chia nhỏ bí mật”, mỗi dòng một mã",
    "qr.make.tech": "▸ Đây là cùng các mã sao chép-dán hiện ra sau khi chia bí mật. Mỗi dòng trở thành một ảnh QR PNG.",
    "qr.make.step2": "2  Lưu các ảnh QR vào một thư mục",
    "qr.make.btn": "Tạo ảnh QR",
    "qr.recover.title": "🔗 Khôi phục từ ảnh QR",
    "qr.recover.purpose": "Dựng lại một bí mật từ đủ số ảnh QR, cùng tệp dữ liệu (payload).",
    "qr.recover.step1": "1  Các tệp ảnh QR (PNG/JPEG)",
    "qr.recover.ph.images": "Kéo thả ảnh QR vào đây, hoặc bấm Thêm ảnh QR…",
    "qr.recover.btn.addImages": "Thêm ảnh QR…",
    "qr.recover.note": "▸ Hãy thêm ít nhất số mảnh “cần để khôi phục”.",
    "qr.recover.step2": "2  Tệp dữ liệu (payload)",
    "qr.recover.ph.payload": "Chọn tệp .payload.svss…",
    "qr.recover.step3": "3  Nơi lưu kết quả khôi phục",
    "qr.recover.ph.output": "/đường-dẫn/tới/ket-qua-khoi-phuc",
    "qr.recover.btn": "Khôi phục từ QR",

    // ---- coming-soon placeholders ----
    "soon.tag": "Sắp có",
    "soon.hide.title": "🕵️ Giấu dữ liệu bên trong tệp",
    "soon.hide.what": "<strong>Nó sẽ làm gì:</strong> giấu một tệp bên trong ảnh hoặc tệp âm thanh để trông bình thường.",
    "soon.hide.when": "<strong>Khi nào bạn dùng:</strong> để gửi một thứ gì đó một cách kín đáo kèm theo một tệp trông bình thường.",
    "soon.hide.status": "Trạng thái: đang đánh giá — chưa khả dụng.",
    "soon.detect.title": "🔎 Phát hiện dữ liệu ẩn",
    "soon.detect.what": "<strong>Nó sẽ làm gì:</strong> quét một tệp tìm dấu hiệu dữ liệu được che giấu.",
    "soon.detect.status": "Trạng thái: đang đánh giá — chưa khả dụng.",

    // ---- inspect metadata ----
    "mi.title": "🔍 Xem siêu dữ liệu",
    "mi.purpose": "Xem siêu dữ liệu ẩn mà một tệp mang theo — máy ảnh, vị trí, tác giả, phần mềm, dấu thời gian.",
    "mi.when.body": "Trước khi chia sẻ một ảnh hay tài liệu, để xem nó âm thầm tiết lộ gì về bạn — tọa độ GPS, tên bạn, thiết bị, lịch sử chỉnh sửa. Việc đọc là an toàn và không bao giờ thay đổi tệp.",
    "mi.step1": "1  Chọn tệp cần xem",
    "mi.ph.file": "Kéo thả bất kỳ tệp nào vào đây, hoặc Duyệt…",
    "mi.tech": "▸ Hoạt động với ảnh, PDF, tài liệu Office, âm thanh, video, và nhiều hơn nữa. Chỉ đọc.",
    "mi.btn": "Xem",

    // ---- remove metadata ----
    "mc.title": "🧹 Xóa siêu dữ liệu",
    "mc.purpose": "Ghi một bản sao sạch của tệp với siêu dữ liệu nhúng đã được loại bỏ.",
    "mc.when.body": "Trước khi công bố một ảnh hay tài liệu, để loại bỏ siêu dữ liệu nhận dạng (GPS, thiết bị, tác giả, phần mềm). Tệp gốc của bạn không bao giờ bị động đến — một bản sao mới đã làm sạch được ghi ra.",
    "mc.step1": "1  Chọn tệp cần làm sạch",
    "mc.ph.input": "Kéo thả tệp vào đây, hoặc Duyệt…",
    "mc.tech1": "▸ Ảnh và WAV/AVI/MOV/MP4 được <strong>loại bỏ hoàn toàn</strong>. <strong>PDF</strong> là làm sạch theo nỗ lực tốt nhất (siêu dữ liệu cũ vẫn có thể khôi phục được). Tài liệu Office, kho nén, và MP3/FLAC/MKV là <strong>chỉ xem</strong> và sẽ bị từ chối ở đây.",
    "mc.step2": "2  Nơi lưu bản sao đã làm sạch",
    "mc.ph.output": "/đường-dẫn/tới/tệp-da-lam-sach",
    "mc.tech2": "▸ Hãy giữ nguyên phần mở rộng tệp như bản gốc để các ứng dụng vẫn mở được. Chi tiết kỹ thuật: <code>exiftool -all=</code> ghi một tệp mới; tệp đầu vào không bao giờ bị sửa tại chỗ.",
    "mc.btn": "Xóa siêu dữ liệu",

    // ---- compare metadata ----
    "cmp.title": "📑 So sánh siêu dữ liệu",
    "cmp.purpose": "Xem siêu dữ liệu nhúng của hai tệp khác nhau ra sao — gì được thêm, bị xóa, hay thay đổi.",
    "cmp.when.body": "Để xác nhận một bước làm sạch đã hiệu quả (so bản gốc với bản đã làm sạch), hoặc để xem chính xác siêu dữ liệu mà hai phiên bản của một tệp mang theo. Tên tệp, kích thước và dấu thời gian được bỏ qua — chỉ siêu dữ liệu nhúng thực sự được so sánh.",
    "cmp.step1": "1  Tệp thứ nhất (A)",
    "cmp.ph.a": "Kéo thả tệp vào đây, hoặc Duyệt…",
    "cmp.step2": "2  Tệp thứ hai (B)",
    "cmp.ph.b": "Kéo thả tệp vào đây, hoặc Duyệt…",
    "cmp.btn": "So sánh",

    // ---- about modal ----
    "about.title": "Giới thiệu",
    "about.close": "Đóng",
    "about.blurb": "Bộ công cụ Bảo mật & Riêng tư — một ứng dụng máy tính ngoại tuyến tập hợp các công cụ bảo mật mã nguồn mở đã được kiểm chứng.",
    "about.version": "Phiên bản {app} · định dạng két v{fmt} · bộ mã hóa v{suite} · hợp đồng v{contract}",
    "about.attribution": "© Tracy Tran",

    // ---- shared buttons / labels ----
    "btn.browse": "Duyệt…",
    "btn.saveAs": "Lưu thành…",
    "btn.chooseFolder": "Chọn thư mục…",
    "btn.working": "Đang xử lý…",
    "btn.copy": "Sao chép",
    "btn.copyCode": "Sao chép mã",
    "action.showInFolder": "Hiện trong thư mục",
    "action.openFile": "Mở tệp",

    // ---- error code messages ----
    "err.notFound": "Không tìm thấy tệp đó.",
    "err.malformed": "Tệp đó không đúng kiểu mong đợi.",
    "err.incompatibleVersion": "Tệp này cần một phiên bản ứng dụng mới hơn.",
    "err.corrupted": "Tệp này bị hỏng hoặc đã bị can thiệp.",
    "err.unauthorized": "Sai mật khẩu, sai mảnh khôi phục, hoặc dữ liệu bị can thiệp.",
    "err.insufficientShares": "Không đủ mảnh khôi phục.",
    "err.invalidInput": "Có gì đó trong dữ liệu nhập không hợp lệ.",
    "err.io": "Không thể đọc hoặc ghi một tệp.",
    "err.tooLarge": "Tệp đó quá lớn.",
    "err.timeout": "Thao tác mất quá nhiều thời gian và đã bị dừng.",
    "err.outputExists": "Đã có một tệp ở vị trí đó.",
    "err.internal": "Có lỗi xảy ra bên trong ứng dụng.",
    "err.insufficientShares.detail": "Không đủ mảnh khôi phục: bạn đã thêm {got}, nhưng cần {need}.",
    "err.incompatibleVersion.detail": "Tệp này là phiên bản {found}; ứng dụng này hỗ trợ phiên bản {supported}.",
    "err.tooLarge.detail": "Tệp đó là {actual}, vượt quá giới hạn {limit}.",
    "err.outputExists.detail": "Đã có một tệp ở đường dẫn đó — hãy chọn tên khác để không ghi đè lên gì cả.",

    // ---- status messages ----
    "status.folderOpenCopied": "Không mở được thư mục ở đây — đã sao chép đường dẫn vào bộ nhớ tạm.",
    "status.folderOpenFailed": "Không mở được thư mục.",
    "status.fileOpenCopied": "Không mở được tệp ở đây — đã sao chép đường dẫn vào bộ nhớ tạm.",
    "status.fileOpenFailed": "Không mở được tệp.",
    "status.copied": "Đã sao chép vào bộ nhớ tạm.",
    "status.copyFailed": "Không sao chép được — hãy chọn văn bản thủ công.",
    "status.pickerUnavailable": "Bộ chọn tệp không khả dụng ở đây — hãy tự gõ đường dẫn.",
    "status.fileAdded": "Đã thêm tệp.",
    "status.savedTo": "Đã lưu “{name}” vào {dest}",
    "status.vaultOpened": "Đã mở két.",
    "status.locked": "Đã khóa.",
    "status.itemAdded": "Đã thêm mục.",
    "status.recoveredOpened": "Đã khôi phục và mở.",
    "status.passwordChanged": "Đã đổi mật khẩu.",
    "status.pubkeyLoaded": "Đã nạp khóa công khai. Hãy lưu nó vào một tệp .pub để người khác xác minh chữ ký của bạn.",
    "status.pubkeyCopied": "Đã sao chép khóa công khai vào bộ nhớ tạm.",
    "status.pubkeySelectAll": "Đã chọn toàn bộ — nhấn ⌘/Ctrl-C để sao chép.",
    "status.pieceCopied": "Đã sao chép mã mảnh — hãy giữ bí mật.",
    "status.pieceCopyFailed": "Không sao chép được — hãy mở tệp mảnh thay thế.",
    "status.policyRecovery": "Khôi phục phải thỏa: 2 ≤ cần ≤ tổng ≤ 255.",
    "status.policyShares": "Các mảnh phải thỏa: 2 ≤ cần ≤ tổng ≤ 255.",
    "status.policyPieces": "Các mảnh phải thỏa: 1 ≤ cần ≤ tổng ≤ 255.",

    // ---- validation (inline field errors) ----
    "v.create.path": "Chọn nơi lưu két mới",
    "v.create.pass": "Đặt một mật khẩu",
    "v.create.mismatch": "Mật khẩu không khớp. Gõ sai ở đây sẽ khiến bạn mất quyền truy cập vĩnh viễn.",
    "v.unlock.path": "Chọn tệp két",
    "v.unlock.pass": "Nhập mật khẩu của bạn",
    "v.add.source": "Chọn một tệp để thêm",
    "v.add.name": "Đặt cho nó một tên trong két",
    "v.split.outdir": "Chọn một thư mục cho các tệp mảnh",
    "v.recover.path": "Chọn tệp két",
    "v.recover.shares": "Thêm ít nhất một tệp mảnh khôi phục.",
    "v.sign.file": "Chọn một tệp để ký",
    "v.verify.file": "Chọn tệp đã ký",
    "v.verify.sig": "Chọn tệp chữ ký",
    "v.verify.pub": "Chọn tệp khóa công khai",
    "v.integrity.path": "Chọn tệp két",
    "v.changePass.new": "Nhập một mật khẩu mới",
    "v.changePass.mismatch": "Mật khẩu không khớp.",
    "v.hash.file": "Chọn một tệp",
    "v.tkverify.file": "Chọn tệp",
    "v.tkverify.sig": "Chọn tệp chữ ký",
    "v.tkverify.pub": "Chọn tệp khóa công khai",
    "v.intact.file": "Chọn một tệp",
    "v.intact.hash": "Dán vân tay bạn được cung cấp",
    "v.vi.file": "Chọn tệp",
    "v.vi.bothSig": "Kiểm tra chữ ký cần cả chữ ký và khóa công khai.",
    "v.vi.need": "Dán một vân tay, hoặc thêm chữ ký + khóa công khai.",
    "v.enc.input": "Chọn một tệp để khóa",
    "v.enc.output": "Chọn nơi lưu tệp đã khóa",
    "v.enc.pass": "Đặt một mật khẩu",
    "v.enc.mismatch": "Mật khẩu không khớp. Gõ sai ở đây là không thể khôi phục.",
    "v.dec.input": "Chọn tệp đã khóa",
    "v.dec.output": "Chọn nơi lưu tệp đã mở",
    "v.dec.pass": "Nhập mật khẩu",
    "v.hide.cover": "Chọn một ảnh nền",
    "v.hide.payload": "Chọn tệp cần giấu",
    "v.hide.output": "Chọn nơi lưu ảnh",
    "v.hide.pass": "Đặt một mật khẩu",
    "v.unhide.input": "Chọn ảnh có dữ liệu giấu",
    "v.unhide.output": "Chọn thư mục đích",
    "v.unhide.pass": "Nhập mật khẩu",
    "v.detect.input": "Chọn một ảnh để quét",
    "v.mi.file": "Chọn một tệp để xem",
    "v.mc.input": "Chọn một tệp để làm sạch",
    "v.mc.output": "Chọn nơi lưu bản sao đã làm sạch",
    "v.cmp.a": "Chọn tệp thứ nhất",
    "v.cmp.b": "Chọn tệp thứ hai",
    "v.genkey.dir": "Chọn một thư mục cho danh tính",
    "v.genkey.name": "Đặt tên cho danh tính này",
    "v.genkey.pass": "Đặt một mật khẩu",
    "v.genkey.mismatch": "Mật khẩu không khớp.",
    "v.sign2.input": "Chọn một tệp để ký",
    "v.sign2.key": "Chọn khóa bí mật của bạn (.svkey)",
    "v.sign2.pass": "Nhập mật khẩu của khóa",
    "v.ss.text": "Gõ bí mật cần chia",
    "v.ss.outdir": "Chọn một thư mục cho các mảnh",
    "v.sf.input": "Chọn một tệp để chia",
    "v.sf.outdir": "Chọn một thư mục cho các mảnh",
    "v.rp.payload": "Chọn tệp dữ liệu (payload)",
    "v.rp.output": "Chọn nơi lưu kết quả",
    "v.rp.pieces": "Thêm ít nhất một mảnh — một tệp hoặc một mã đã dán.",
    "v.qr.outdir": "Chọn một thư mục cho các ảnh QR",
    "v.qr.codes": "Dán ít nhất một mã mảnh (mỗi dòng một mã).",
    "v.qr.payload": "Chọn tệp dữ liệu (payload)",
    "v.qr.output": "Chọn nơi lưu kết quả",
    "v.qr.images": "Thêm ít nhất một ảnh QR.",
    "v.wm.input": "Chọn một ảnh để đánh dấu",
    "v.wm.output": "Chọn nơi lưu ảnh đã đánh dấu",
    "v.wm.pass": "Đặt một mật khẩu",
    "v.wmv.input": "Chọn ảnh đã đánh dấu",
    "v.wmv.pass": "Nhập mật khẩu",

    // ---- result cards: prefixes ----
    "res.ok.prefix": "✅ ",
    "res.bad.prefix": "❌ ",

    // ---- result: create vault ----
    "r.create.title": "Đã tạo két",
    "r.create.msg.recovery": "Khôi phục đã bật — hãy tạo các mảnh sau khi bạn mở nó.",
    "r.create.msg.plain": "Giờ hãy mở nó: chọn tệp này trong “Mở két” và nhập mật khẩu.",
    "r.label.savedTo": "Đã lưu vào",
    "r.extract.title": "Đã lưu một bản sao",
    "r.note": "Lưu ý",
    "r.ext.caveat": "Nếu tệp đã lưu không mở được, hãy đổi tên để thêm phần mở rộng gốc của tệp (ví dụ .pdf, .zip, .jpg).",
    "r.label.originalName": "Tệp gốc",
    "r.ext.mismatch": "Đã khôi phục thành “{name}”. Tên bạn chọn khác — hãy dùng “Lưu thành …” bên dưới để giữ tên và phần mở rộng gốc.",
    "action.saveAsName": "Lưu thành {name}",
    "meta.unavailable.title": "Công cụ này không khả dụng trong bản dựng này",
    "meta.unavailable.msg": "Các tính năng siêu dữ liệu cần thành phần ExifTool đi kèm, vốn không có trong bản dựng này. Kiểm tra, Xóa và So sánh bị vô hiệu hóa ở đây.",
    "r.create.openNow": "Mở ngay bây giờ",

    // ---- result: split (vault) ----
    "r.split.title": "Đã tạo {n} mảnh khôi phục",
    "r.split.title.plural": "Đã tạo {n} mảnh khôi phục",
    "r.split.msg": "Bất kỳ {threshold} mảnh gộp lại đều có thể khôi phục két này. Hãy cất mỗi mảnh ở một nơi tin cậy riêng.",
    "r.share.label": "Mảnh {index} / {total}",

    // ---- result: sign (vault) ----
    "r.sign.title": "Đã ký tệp bằng khóa của két",
    "r.label.signature": "Chữ ký",

    // ---- result: verify / integrity (vault) ----
    "r.verify.ok.title": "Chữ ký hợp lệ",
    "r.verify.ok.msg": "Được ký bằng khóa này, và tệp chưa bị thay đổi.",
    "r.label.fingerprint": "Vân tay",
    "r.verify.bad.title": "Chữ ký KHÔNG khớp",
    "r.verify.bad.msg": "Tệp, chữ ký, hoặc khóa công khai sai, hoặc tệp đã thay đổi.",
    "r.integrity.ok.title": "Két còn nguyên vẹn",
    "r.integrity.ok.msg": "Chữ ký và nội dung của nó đều ổn.",
    "r.integrity.bad.title": "Kiểm tra toàn vẹn thất bại",
    "r.integrity.bad.msg": "Két này bị hỏng hoặc đã bị can thiệp.",
    "r.vaultHash.title": "Vân tay của két",
    "r.label.blake3": "BLAKE3",
    "r.vaultCheck.ok.title": "Tệp két này còn nguyên vẹn",
    "r.vaultCheck.bad.title": "Tệp két này không qua được kiểm tra",
    "r.vaultCheck.bad.msg": "Nó có thể bị hỏng hoặc bị can thiệp.",

    // ---- result: fingerprint a file ----
    "r.hash.title": "Vân tay đã sẵn sàng",
    "r.hash.msg": "Hai tệp có cùng vân tay là giống hệt nhau.",

    // ---- result: check a signature (toolkit) ----
    "r.tkverify.ok.title": "Chính hãng",
    "r.tkverify.ok.msg": "Được ký bằng khóa này, và tệp chưa bị thay đổi.",
    "r.tkverify.bad.title": "KHÔNG khớp",
    "r.tkverify.bad.msg": "Tệp, chữ ký, hoặc khóa công khai sai, hoặc tệp đã thay đổi.",

    // ---- result: check a file is unchanged ----
    "r.intact.ok.title": "Chưa thay đổi",
    "r.intact.ok.msg": "Tệp này khớp với vân tay — nó chưa bị sửa.",
    "r.intact.bad.title": "KHÔNG khớp",
    "r.intact.bad.msg": "Tệp này không khớp với vân tay bạn cung cấp — nó có thể đã thay đổi, hoặc là một tệp khác.",
    "r.intact.thisFile": "Tệp này",
    "r.intact.expected": "Mong đợi",
    "r.intact.empty": "(trống)",

    // ---- result: verify a download ----
    "r.vi.ok.title": "Đã xác minh",
    "r.vi.ok.msg": "Mọi kiểm tra bạn yêu cầu đều đạt — tệp này đúng y như đã công bố.",
    "r.vi.bad.title": "KHÔNG xác minh được",
    "r.vi.bad.msg": "Ít nhất một kiểm tra thất bại — tệp có thể đã thay đổi, hoặc một dữ liệu nhập bị sai.",
    "r.vi.fpMatch": "Vân tay khớp",
    "r.vi.yes": "có",
    "r.vi.no": "KHÔNG",
    "r.vi.sig": "Chữ ký",
    "r.vi.valid": "hợp lệ",
    "r.vi.invalid": "KHÔNG HỢP LỆ",

    // ---- result: lock a file ----
    "r.enc.title": "Đã khóa tệp",
    "r.enc.msg": "Hãy giữ mật khẩu an toàn — đó là cách duy nhất để mở tệp này.",
    "r.enc.another": "Khóa tệp khác",
    "r.exists.title": "Đã có một tệp ở đó",
    "r.exists.msg": "Không có gì bị ghi đè. Hãy chọn một tên khác và thử lại.",
    "r.exists.pickNew": "Chọn tên mới…",

    // ---- result: unlock a file ----
    "r.dec.title": "Đã mở khóa tệp",
    "r.dec.bad.title": "Không mở khóa được tệp này",
    "r.dec.bad.msg": "Mật khẩu sai, hoặc đây không phải một tệp đã khóa hợp lệ.",

    // ---- result: hide data ----
    "r.hide.title": "Đã giấu dữ liệu",
    "r.hide.msg": "Hãy giữ mật khẩu an toàn — đó là cách duy nhất để hiện dữ liệu này.",
    "r.hide.size": "Kích thước tệp giấu",
    "r.hide.capacity": "Dung lượng đã dùng",
    "r.hide.capacityVal": "{pct}% của {capacity}",
    "r.hide.tooBig.title": "Tệp quá lớn để giấu",
    "r.hide.tooBig.msg": "Tệp bạn đang giấu lớn hơn sức chứa của ảnh này. Hãy dùng ảnh nền lớn hơn, hoặc giấu một tệp nhỏ hơn.",
    "r.hide.unsupported.title": "Ảnh không được hỗ trợ",
    "r.hide.unsupported.msg": "Ảnh nền phải là ảnh PNG hoặc BMP.",

    // ---- result: reveal data ----
    "r.unhide.title": "Đã hiện dữ liệu",
    "r.label.size": "Kích thước",
    "r.unhide.bad.title": "Không hiện được dữ liệu nào",
    "r.unhide.bad.msg": "Mật khẩu sai, ảnh này không chứa dữ liệu giấu, hoặc nó đã bị sửa — theo thiết kế, các trường hợp này không phân biệt được.",

    // ---- result: detect ----
    "r.detect.title": "Quét xong",
    "r.detect.msg.elevated": "Ảnh này có dấu hiệu có thể cho thấy dữ liệu ẩn — hãy thận trọng với nó.",
    "r.detect.msg.clean": "Không tìm thấy dấu hiệu rõ ràng nào của dữ liệu ẩn. Đây không phải đảm bảo ảnh sạch.",
    "r.detect.verdict": "Kết luận",
    "r.detect.note": "Lưu ý",
    "r.detect.unsupported.title": "Ảnh không được hỗ trợ",
    "r.detect.unsupported.msg": "Ảnh phải là PNG hoặc BMP.",
    "detect.verdict.NotObserved": "Các phép thử này không phát hiện gì",
    "detect.verdict.Low": "Nghi ngờ thấp",
    "detect.verdict.Elevated": "Nghi ngờ khá cao",
    "detect.verdict.High": "Nghi ngờ cao",

    // ---- result: inspect metadata ----
    "r.mi.title": "Đã đọc siêu dữ liệu",
    "r.mi.unknownType": "kiểu không xác định",
    "r.mi.fieldCount": "{n} trường",
    "r.mi.fieldCount.plural": "{n} trường",
    "r.mi.msg": "{summary}. Phần này gồm cả thông tin hệ thống tệp; siêu dữ liệu nhúng mới là thứ đi theo tệp.",

    // ---- result: remove metadata ----
    "r.mc.format": "Định dạng",
    "r.mc.before": "Số trường siêu dữ liệu trước",
    "r.mc.after": "Số trường siêu dữ liệu sau",
    "r.mc.removed": "Số trường đã xóa",
    "r.mc.ok.title": "Đã ghi bản sao sạch",
    "r.mc.ok.msg": "Toàn bộ siêu dữ liệu nhúng đã được loại bỏ. Tệp gốc của bạn không bị thay đổi.",
    "r.mc.best.title": "Đã ghi bản làm sạch theo nỗ lực tốt nhất",
    "r.mc.best.msg": "Đây là PDF: siêu dữ liệu được loại bỏ bằng một bản cập nhật tăng dần, nên các giá trị trước đó vẫn có thể khôi phục từ tệp. Để làm sạch đảm bảo, hãy xuất lại PDF từ nguồn của nó. Tệp gốc của bạn không bị thay đổi.",

    // ---- result: compare metadata ----
    "r.cmp.same.title": "Siêu dữ liệu nhúng giống hệt nhau",
    "r.cmp.diff.title": "Đã tìm thấy khác biệt",
    "r.cmp.same.msg": "Cả hai tệp mang cùng siêu dữ liệu nhúng. (Tên tệp, kích thước và dấu thời gian được bỏ qua.)",
    "r.cmp.diff.msg": "{n} khác biệt trong siêu dữ liệu nhúng. (Tên tệp, kích thước và dấu thời gian được bỏ qua.)",
    "r.cmp.diff.msg.plural": "{n} khác biệt trong siêu dữ liệu nhúng. (Tên tệp, kích thước và dấu thời gian được bỏ qua.)",
    "r.cmp.changed": "đã đổi · {key}",
    "r.cmp.onlyA": "chỉ ở A · {name}",
    "r.cmp.onlyB": "chỉ ở B · {name}",
    "r.cmp.arrow": "{a}  →  {b}",

    // ---- result: generate signing keypair ----
    "r.genkey.title": "Đã tạo danh tính ký",
    "r.genkey.msg": "Hãy giữ khóa bí mật (.svkey) và mật khẩu của nó an toàn. Chia sẻ khóa công khai để người khác xác minh.",
    "r.genkey.pub": "Khóa công khai",
    "r.genkey.priv": "Khóa bí mật",
    "r.genkey.pubHex": "Công khai (hex)",

    // ---- result: sign a file (toolkit) ----
    "r.sign2.title": "Đã ký tệp",
    "r.sign2.checkSig": "Kiểm tra chữ ký này",
    "r.sign2.bad.title": "Không ký được",
    "r.sign2.bad.msg": "Mật khẩu của khóa ký này bị sai.",

    // ---- result: split secret / file ----
    "r.piece.label": "Mảnh {index} / {total}",
    "r.ss.title": "Đã tạo {n} mảnh",
    "r.ss.msg": "Bất kỳ {threshold} mảnh gộp lại đều khôi phục được bí mật. Hãy giữ tệp dữ liệu (payload) cùng chúng — nó cần để khôi phục. Mỗi mã bên dưới đều bí mật; hãy cất riêng các mảnh.",
    "r.payload.label": "Tệp dữ liệu (payload)",
    "r.sf.title": "Đã tạo {n} mảnh",
    "r.sf.msg": "Bất kỳ {threshold} tệp mảnh này cộng với tệp dữ liệu (payload) đều có thể khôi phục tệp của bạn. Hãy cất riêng mỗi mảnh.",

    // ---- result: recover from pieces ----
    "r.recover.title": "Đã khôi phục",
    "r.recover.msg": "Các mảnh khớp nhau và bí mật đã được dựng lại.",
    "r.recover.bad.title": "Không khôi phục được",
    "r.recover.bad.msg": "Các mảnh này không khớp, thuộc một lần chia khác, hoặc tệp dữ liệu (payload) sai hay bị hỏng.",

    // ---- result: QR make / recover ----
    "r.qrmake.title": "Đã tạo {n} ảnh QR",
    "r.qrmake.title.plural": "Đã tạo {n} ảnh QR",
    "r.qrmake.msg": "Mỗi QR chứa một mảnh. Hãy chuyển một ngưỡng số mảnh — cùng tệp dữ liệu (payload) — để khôi phục.",
    "r.qr.pieceLabel": "Mảnh {n}",
    "r.qrrecover.title": "Đã khôi phục",
    "r.qrrecover.msg": "Các mảnh QR khớp nhau và bí mật đã được dựng lại.",
    "r.qr.badRead.title": "Không đọc được một ảnh QR",
    "r.qr.badRead.msg": "Một trong các ảnh không có mã QR đọc được. Hãy chụp lại (sắc nét hơn, đủ sáng, toàn bộ mã trong khung) và thử lại.",

    // ---- result: watermark embed / verify ----
    "r.wm.title": "Đã thêm dấu chống giả mạo",
    "r.wm.msg": "Ảnh này giờ tự xác minh được bằng mật khẩu của bạn. Bất kỳ chỉnh sửa nào về sau — kể cả lưu lại thành JPEG hay đổi kích thước — đều sẽ lộ ra là giả mạo.",
    "r.wm.regions": "Số vùng kiểm tra",
    "r.wm.bad.title": "Không đánh dấu được ảnh này",
    "r.wmv.intact.title": "Nguyên vẹn",
    "r.wmv.intact.msg": "Mọi vùng đều ổn — ảnh này chưa thay đổi kể từ khi được đánh dấu bằng mật khẩu này.",
    "r.wmv.regionsChecked": "Số vùng đã kiểm tra",
    "r.wmv.tampered.title": "Bị giả mạo",
    "r.wmv.tampered.msg": "Ảnh này đã bị sửa sau khi đánh dấu. {tampered} trong {total} vùng đã thay đổi.",
    "r.wmv.altered": "Số vùng bị thay đổi",
    "r.wmv.alteredVal": "{tampered} trong {total}",
    "r.wmv.none.title": "Không có dấu hợp lệ",
    "r.wmv.none.msg": "Không tìm thấy dấu chống giả mạo cho mật khẩu này. Ảnh có thể chưa được đánh dấu, được đánh dấu bằng mật khẩu khác, đã lưu lại thành JPEG/đổi kích thước (việc này phá hủy dấu), hoặc đã bị thay thế hoàn toàn.",
  };

  const DICT = { vi: VI, en: EN };

  // -------------------------------------------------------------------------

  function readStoredLang() {
    try {
      const v = window.localStorage.getItem(STORAGE_KEY);
      if (v && SUPPORTED.indexOf(v) !== -1) return v;
    } catch (_) {
      /* localStorage may be unavailable; fall through to the default */
    }
    return DEFAULT_LANG;
  }

  let lang = readStoredLang();

  // Look up a key in the active locale, falling back to English, then to the raw key (so a
  // missing string is visible rather than blank). `{name}` placeholders are filled from `params`.
  function t(key, params) {
    const table = DICT[lang] || EN;
    let s = table[key];
    if (s == null) s = EN[key];
    if (s == null) s = key;
    if (params) {
      s = s.replace(/\{(\w+)\}/g, function (m, k) {
        return params[k] != null ? String(params[k]) : m;
      });
    }
    return s;
  }

  // Translate the static markup under `root` (default: whole document).
  function apply(root) {
    root = root || document;
    root.querySelectorAll("[data-i18n]").forEach(function (el) {
      el.textContent = t(el.getAttribute("data-i18n"));
    });
    root.querySelectorAll("[data-i18n-html]").forEach(function (el) {
      el.innerHTML = t(el.getAttribute("data-i18n-html"));
    });
    root.querySelectorAll("[data-i18n-ph]").forEach(function (el) {
      el.setAttribute("placeholder", t(el.getAttribute("data-i18n-ph")));
    });
    root.querySelectorAll("[data-i18n-title]").forEach(function (el) {
      el.setAttribute("title", t(el.getAttribute("data-i18n-title")));
    });
    document.documentElement.lang = lang;
  }

  function setLang(next) {
    if (SUPPORTED.indexOf(next) === -1 || next === lang) {
      // Still re-apply if the same language is re-selected (no-op for content, harmless).
      if (SUPPORTED.indexOf(next) === -1) return;
    }
    lang = next;
    try {
      window.localStorage.setItem(STORAGE_KEY, next);
    } catch (_) {
      /* persistence best-effort */
    }
    apply(document);
    if (typeof window.onLangChange === "function") {
      try {
        window.onLangChange(lang);
      } catch (_) {
        /* never let a listener break language switching */
      }
    }
  }

  function getLang() {
    return lang;
  }

  window.i18n = {
    t: t,
    apply: apply,
    setLang: setLang,
    getLang: getLang,
    SUPPORTED: SUPPORTED,
    DEFAULT_LANG: DEFAULT_LANG,
  };

  // Translate the static markup as soon as this script runs. It is loaded at the end of <body>
  // (before main.js), so the elements above already exist — this avoids a flash of English before
  // main.js initializes.
  apply(document);
})();

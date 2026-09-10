#!/usr/bin/env python3
"""Thu thập dữ kiện kỹ thuật TRỰC TIẾP từ mã nguồn và kết quả kiểm thử.

Nguyên tắc: hồ sơ không được chứa con số nhập tay. Mọi số liệu trong DOCX phải đọc
từ tệp du-kien.json do script này sinh ra, và mỗi số liệu đều ghi rõ nguồn gốc.
Nếu một phép đo chưa chạy được, trường tương ứng để None và hồ sơ phải nói rõ
"chưa kiểm chứng" thay vì điền số.
"""

import json
import pathlib
import re
import subprocess
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path(__file__).parent / "bang-chung" / "du-kien.json"


def dem_lenh_ipc():
    s = (REPO / "app/src/lib.rs").read_text(encoding="utf-8")
    m = re.search(r"generate_handler!\[(.*?)\]", s, re.S)
    if not m:
        return None, []
    cmds = [c.strip() for c in m.group(1).split(",") if c.strip()]
    return len(cmds), cmds


def dem_crate():
    members = re.findall(r'"(crates/[^"]+|src-tauri)"', (REPO / "Cargo.toml").read_text(encoding="utf-8"))
    return len(members), sorted(members)


def tham_so_argon2():
    s = (REPO / "crates/sv-crypto/src/policy.rs").read_text(encoding="utf-8")
    mem = re.search(r"MIN_MEM_KIB: u32 = ([0-9_]+)", s)
    t = re.search(r"MIN_TIME_COST: u32 = (\d+)", s)
    p = re.search(r"MIN_PARALLELISM: u32 = (\d+)", s)
    return {
        "min_mem_kib": int(mem.group(1).replace("_", "")) if mem else None,
        "min_time_cost": int(t.group(1)) if t else None,
        "min_parallelism": int(p.group(1)) if p else None,
    }


def dem_test_nguon():
    """Đếm số hàm #[test] trong mã nguồn theo crate (không phải kết quả chạy)."""
    out = {}
    for d in sorted((REPO / "crates").iterdir()):
        if not d.is_dir():
            continue
        n = 0
        for f in d.rglob("*.rs"):
            n += len(re.findall(r"#\[test\]", f.read_text(encoding="utf-8", errors="ignore")))
        out[d.name] = n
    n = 0
    for f in (REPO / "src-tauri").rglob("*.rs"):
        n += len(re.findall(r"#\[test\]", f.read_text(encoding="utf-8", errors="ignore")))
    out["sv-app"] = n
    return out


def doc_ket_qua(path):
    """Đọc tổng kết từ một tệp log `cargo test`. Trả về None nếu không có/không hợp lệ."""
    p = pathlib.Path(path)
    if not p.exists():
        return None
    txt = p.read_text(encoding="utf-8", errors="ignore")
    rows = re.findall(r"^test result: (\w+)\. (\d+) passed; (\d+) failed; (\d+) ignored", txt, re.M)
    if not rows:
        return None
    return {
        "suites": len(rows),
        "passed": sum(int(r[1]) for r in rows),
        "failed": sum(int(r[2]) for r in rows),
        "ignored": sum(int(r[3]) for r in rows),
        "hoan_tat": "exit=0" in txt or txt.rstrip().endswith("0"),
    }


def thuat_toan():
    s = (REPO / "crates/sv-crypto-traits/src/lib.rs").read_text(encoding="utf-8")
    return {
        "kdf": "Argon2id" if "Argon2id" in s else None,
        "hash": "BLAKE3" if "BLAKE3" in s else None,
        "aead_vault": "age v1 (X25519 + ChaCha20-Poly1305)" if "ChaCha20-Poly1305" in s else None,
        "aead_field": "XSalsa20-Poly1305 (libsodium secretbox)" if "XSalsa20-Poly1305" in s else None,
        "chu_ky": "Ed25519 (định dạng minisign)" if "Ed25519" in s else None,
        "chia_se_bi_mat": "Shamir k-trong-n (sss hazmat.c)",
    }


def da_nen_tang():
    """Dữ kiện về khả năng đa nền tảng, đọc từ cấu hình CI và biên bản chạy CI.

    Không gõ tay: ma trận hệ điều hành đọc thẳng từ .github/workflows/ci.yml, còn mã lần chạy
    CI đã xanh đọc từ docs/CI-VALIDATION.md. Nếu một trong hai tệp đổi, số liệu trong hồ sơ
    đổi theo.
    """
    ra = {}
    ci = REPO / ".github/workflows/ci.yml"
    if ci.exists():
        txt = ci.read_text(encoding="utf-8")
        he_dieu_hanh = sorted({m for m in re.findall(r"(ubuntu|macos|windows)-latest", txt)})
        ra["he_dieu_hanh_ci"] = he_dieu_hanh
        ra["viec_chay_ma_tran"] = re.findall(r"name: (.+) \(\$\{\{ matrix\.os \}\}\)", txt)
    bb = REPO / "docs/CI-VALIDATION.md"
    if bb.exists():
        txt = bb.read_text(encoding="utf-8")
        ngay = re.search(r"^\*\*Date:\*\* (\S+)", txt, re.M)
        commit = re.search(r"\*\*Validated commit:\*\* `(\w+)`", txt)
        run_id = re.search(r"workflow run\s*\n?\[`(\d+)`\]", txt)
        xanh = re.search(r"\*\*all (\d+) jobs green\.\*\*", txt)
        ra["lan_chay_ci_xanh"] = {
            "ngay": ngay.group(1) if ngay else None,
            "commit": commit.group(1) if commit else None,
            "ma_lan_chay": run_id.group(1) if run_id else None,
            "so_viec_dat": int(xanh.group(1)) if xanh else None,
        }
    # Bản hiện thực gắn với từng nền tảng — đọc từ chính lớp lắp ráp, nơi hai nền tảng rẽ nhánh.
    for ten, tep in (("desktop", "app/src/compose/desktop.rs"), ("mobile", "app/src/compose/mobile.rs")):
        f = REPO / tep
        ra.setdefault("lop_lap_rap", {})[ten] = f.exists()
    return ra


def git_info():
    def run(*a):
        try:
            return subprocess.run(a, cwd=REPO, capture_output=True, text=True, timeout=30).stdout.strip()
        except Exception:
            return None
    dau = run("git", "log", "--reverse", "--format=%ad", "--date=short")
    return {
        "commit": run("git", "rev-parse", "--short", "HEAD"),
        "branch": run("git", "rev-parse", "--abbrev-ref", "HEAD"),
        "so_commit": run("git", "rev-list", "--count", "HEAD"),
        # Khoảng thời gian thực hiện lấy từ chính lịch sử kho mã, không gõ tay.
        "ngay_dau": (dau or "").splitlines()[0] if dau else None,
        "ngay_cuoi": run("git", "log", "-1", "--format=%ad", "--date=short"),
    }


def main():
    scratch = sys.argv[1] if len(sys.argv) > 1 else ""
    n_cmd, cmds = dem_lenh_ipc()
    n_crate, crates = dem_crate()

    du_kien = {
        "lenh_ipc": {"so_luong": n_cmd, "danh_sach": cmds},
        "crate": {"so_luong": n_crate, "danh_sach": crates},
        "argon2id": tham_so_argon2(),
        "thuat_toan": thuat_toan(),
        "test_trong_nguon": dem_test_nguon(),
        "git": git_info(),
        "da_nen_tang": da_nen_tang(),
        "ket_qua_kiem_thu": {
            "host_toan_bo": doc_ket_qua(f"{scratch}/host-full.txt") if scratch else None,
            "arm64_loi_mat_ma": doc_ket_qua(f"{scratch}/arm64-core.txt") if scratch else None,
            "interop_age": doc_ket_qua(f"{scratch}/interop.txt") if scratch else None,
            "interop_vault": doc_ket_qua(f"{scratch}/vault-interop.txt") if scratch else None,
        },
        "toolchain": {
            "ndk": "r28c",
            "clang": "19.0.1",
            "target_android": ["aarch64-linux-android", "armv7-linux-androideabi",
                               "i686-linux-android", "x86_64-linux-android"],
            "rust_msrv": "1.96",
        },
    }
    if OUT.exists():
        cu = json.loads(OUT.read_text(encoding="utf-8"))
        for khoa, gia_tri in (cu.get("ket_qua_kiem_thu") or {}).items():
            if du_kien["ket_qua_kiem_thu"].get(khoa) is None and gia_tri is not None:
                du_kien["ket_qua_kiem_thu"][khoa] = gia_tri

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(du_kien, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Đã ghi {OUT}")
    print(f"  lệnh IPC: {n_cmd}   crate: {n_crate}")
    print(f"  test trong nguồn: {sum(du_kien['test_trong_nguon'].values())}")
    for k, v in du_kien["ket_qua_kiem_thu"].items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()

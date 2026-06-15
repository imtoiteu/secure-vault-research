//! KDF parameter policy.
//!
//! The [`Kdf`](sv_crypto_traits::Kdf) primitive validates only *structural* parameter
//! correctness. This module holds the **deployment policy** — the minimum strength a vault
//! should be created with — kept separate so constrained devices can still open a vault
//! created elsewhere (verification never enforces the floor; creation does).
//!
//! Defaults/floor are conservative interactive values (open question Q5); recalibration
//! against real hardware is an M7 task.

use std::time::{Duration, Instant};

use sv_crypto_traits::{Argon2idParams, Kdf, KdfParams, Salt, SALT_LEN};

/// Minimum Argon2id memory cost, KiB (OWASP Argon2id floor: 19 MiB).
pub const MIN_MEM_KIB: u32 = 19_456;
/// Minimum Argon2id time cost (passes).
pub const MIN_TIME_COST: u32 = 2;
/// Minimum Argon2id parallelism (lanes).
pub const MIN_PARALLELISM: u32 = 1;
/// Upper bound on the time cost the calibrator will choose (keeps `calibrate` bounded).
pub const MAX_CALIBRATED_TIME_COST: u32 = 24;

/// Recommended parameters for creating a new vault.
#[must_use]
pub fn recommended() -> KdfParams {
    KdfParams::default()
}

/// Calibrate Argon2id `time_cost` to a target per-derivation duration **on this machine**
/// (M7 / A4), at a fixed memory budget, never below the policy floor. Use at vault creation
/// (or in a settings UI) so the cost tracks the user's hardware instead of a fixed guess.
///
/// `mem_kib` is clamped up to [`MIN_MEM_KIB`]; `time_cost` rises from the floor until a single
/// derivation takes at least `target` or [`MAX_CALIBRATED_TIME_COST`] is reached. The result
/// always satisfies [`meets_recommended`].
#[must_use]
pub fn calibrate(target: Duration, mem_kib: u32) -> KdfParams {
    let mem_kib = mem_kib.max(MIN_MEM_KIB);
    let kdf = crate::Argon2Kdf;
    let salt = Salt([0u8; SALT_LEN]);
    let mut time_cost = MIN_TIME_COST;
    loop {
        let params = KdfParams::Argon2id(Argon2idParams {
            mem_kib,
            time_cost,
            parallelism: MIN_PARALLELISM,
        });
        let start = Instant::now();
        let _ = kdf.derive(b"secure-vault calibration", &salt, &params);
        if start.elapsed() >= target || time_cost >= MAX_CALIBRATED_TIME_COST {
            return params;
        }
        time_cost += 1;
    }
}

/// Whether `params` meet the recommended minimum strength for vault creation.
#[must_use]
pub fn meets_recommended(params: &KdfParams) -> bool {
    match params {
        KdfParams::Argon2id(p) => {
            p.mem_kib >= MIN_MEM_KIB
                && p.time_cost >= MIN_TIME_COST
                && p.parallelism >= MIN_PARALLELISM
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use sv_crypto_traits::Argon2idParams;

    #[test]
    fn recommended_meets_its_own_floor() {
        assert!(meets_recommended(&recommended()));
    }

    #[test]
    fn weak_params_are_rejected_by_policy() {
        let weak = KdfParams::Argon2id(Argon2idParams {
            mem_kib: 8,
            time_cost: 1,
            parallelism: 1,
        });
        assert!(!meets_recommended(&weak));
    }

    #[test]
    fn calibrate_clamps_to_floor_and_meets_policy() {
        // Tiny target → returns after the first measured derivation; a sub-floor memory
        // request is clamped up. The result must satisfy the creation policy.
        let p = calibrate(Duration::from_millis(1), 4096);
        assert!(meets_recommended(&p));
        let KdfParams::Argon2id(a) = p;
        assert!(a.mem_kib >= MIN_MEM_KIB);
        assert!(a.time_cost >= MIN_TIME_COST && a.time_cost <= MAX_CALIBRATED_TIME_COST);
    }
}

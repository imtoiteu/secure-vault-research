//! Body **placement schedule** — the order in which ciphertext bits are written across carrier
//! sites. Two strategies: [`SequentialSelector`] and a seeded [`PermutedSelector`].
//!
//! **Placement is not a security boundary.** The permutation seed is `BLAKE3(salt)`, and `salt` is
//! public framing in the SVSTEG header. Spreading bits only blunts the most trivial sequential-LSB
//! signatures; *all* confidentiality is the AEAD in [`crate::seal`]. The seed is therefore derived
//! with a plain hash (not a secret KDF) and lives in a non-zeroizing buffer by design.
//!
//! The permutation PRNG is BLAKE3 in counter mode (built from the existing `Blake3Hasher`), so the
//! crate needs no additional RNG dependency and the schedule is fully deterministic and testable.

use sv_crypto::Blake3Hasher;
use sv_crypto_traits::{Hasher, Salt};

/// Which placement schedule a frame uses (encoded in the SVSTEG `flags` byte).
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SelectorKind {
    Sequential,
    Permuted,
}

/// Produces the ordered list of body sites a frame occupies.
pub trait SiteSelector {
    /// The first `count` body sites, in embedding order, drawn from `[body_offset, site_count)`.
    ///
    /// The caller's capacity guard guarantees `count <= site_count - body_offset`; implementations
    /// clamp defensively but never read or write outside the body range.
    fn schedule(&self, site_count: usize, body_offset: usize, count: usize) -> Vec<usize>;
}

/// Body bits are written into consecutive sites starting just after the header.
#[derive(Debug, Default, Clone, Copy)]
pub struct SequentialSelector;

impl SiteSelector for SequentialSelector {
    fn schedule(&self, site_count: usize, body_offset: usize, count: usize) -> Vec<usize> {
        let end = body_offset.saturating_add(count).min(site_count);
        (body_offset..end).collect()
    }
}

/// Body bits are written into a seeded pseudo-random permutation of the body sites.
#[derive(Debug, Clone)]
pub struct PermutedSelector {
    seed: [u8; 32],
}

impl PermutedSelector {
    /// Seed the permutation from the public per-image `salt` (`seed = BLAKE3(salt)`).
    #[must_use]
    pub fn from_salt(salt: &Salt) -> Self {
        Self {
            seed: Blake3Hasher.hash(&salt.0).0,
        }
    }
}

impl SiteSelector for PermutedSelector {
    fn schedule(&self, site_count: usize, body_offset: usize, count: usize) -> Vec<usize> {
        let body_len = site_count.saturating_sub(body_offset);
        let count = count.min(body_len);
        let mut indices: Vec<usize> = (body_offset..site_count).collect();
        let mut rng = Blake3CounterRng::new(self.seed);
        // Partial Fisher-Yates: the first `count` positions become a uniform, ordered selection of
        // distinct body sites. Only `count` swaps are needed (not the full `body_len`).
        for i in 0..count {
            let j = i + rng.below(body_len - i);
            indices.swap(i, j);
        }
        indices.truncate(count);
        indices
    }
}

/// Deterministic byte stream = BLAKE3 keyed-hash in counter mode. Not security-critical (placement
/// is public); chosen only for a uniform, dependency-free, reproducible shuffle.
#[derive(Debug)]
struct Blake3CounterRng {
    key: [u8; 32],
    counter: u64,
    buf: [u8; 32],
    pos: usize,
}

impl Blake3CounterRng {
    fn new(seed: [u8; 32]) -> Self {
        Self {
            key: seed,
            counter: 0,
            buf: [0u8; 32],
            pos: 32, // forces a refill on the first draw
        }
    }

    fn refill(&mut self) {
        self.buf = Blake3Hasher
            .keyed_hash(&self.key, &self.counter.to_le_bytes())
            .0;
        self.counter = self.counter.wrapping_add(1);
        self.pos = 0;
    }

    fn next_u64(&mut self) -> u64 {
        if self.pos + 8 > self.buf.len() {
            self.refill();
        }
        let bytes: [u8; 8] = self.buf[self.pos..self.pos + 8]
            .try_into()
            .expect("8 bytes available");
        self.pos += 8;
        u64::from_le_bytes(bytes)
    }

    /// Unbiased integer in `[0, bound)` by rejection sampling. `bound` must be non-zero.
    fn below(&mut self, bound: usize) -> usize {
        debug_assert!(bound > 0, "below(0) is undefined");
        let bound = bound as u64;
        // Reject the short tail so the modulo is unbiased.
        let zone = u64::MAX - (u64::MAX % bound);
        loop {
            let x = self.next_u64();
            if x < zone {
                return (x % bound) as usize;
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashSet;

    const SITE_COUNT: usize = 1000;
    const BODY_OFFSET: usize = 432;

    #[test]
    fn sequential_is_contiguous_after_the_header() {
        let s = SequentialSelector;
        let sched = s.schedule(SITE_COUNT, BODY_OFFSET, 40);
        assert_eq!(sched.len(), 40);
        assert_eq!(sched[0], BODY_OFFSET);
        assert_eq!(*sched.last().unwrap(), BODY_OFFSET + 39);
    }

    #[test]
    fn permuted_is_deterministic_for_a_given_salt() {
        let sel = PermutedSelector::from_salt(&Salt([5u8; 16]));
        let a = sel.schedule(SITE_COUNT, BODY_OFFSET, 100);
        let b = sel.schedule(SITE_COUNT, BODY_OFFSET, 100);
        assert_eq!(a, b);
    }

    #[test]
    fn permuted_differs_across_salts() {
        let a =
            PermutedSelector::from_salt(&Salt([1u8; 16])).schedule(SITE_COUNT, BODY_OFFSET, 100);
        let b =
            PermutedSelector::from_salt(&Salt([2u8; 16])).schedule(SITE_COUNT, BODY_OFFSET, 100);
        assert_ne!(a, b);
    }

    #[test]
    fn permuted_sites_are_distinct_and_within_the_body() {
        let sel = PermutedSelector::from_salt(&Salt([9u8; 16]));
        let count = 300;
        let sched = sel.schedule(SITE_COUNT, BODY_OFFSET, count);
        assert_eq!(sched.len(), count);
        let set: HashSet<usize> = sched.iter().copied().collect();
        assert_eq!(set.len(), count, "no duplicate sites");
        assert!(
            sched
                .iter()
                .all(|&s| (BODY_OFFSET..SITE_COUNT).contains(&s)),
            "every site is in the body range, never a header site"
        );
    }

    #[test]
    fn schedule_clamps_when_count_exceeds_body() {
        // Defensive: asking for more than the body can hold yields at most the body.
        let body = SITE_COUNT - BODY_OFFSET;
        let seq = SequentialSelector.schedule(SITE_COUNT, BODY_OFFSET, body + 50);
        assert_eq!(seq.len(), body);
        let perm = PermutedSelector::from_salt(&Salt([0u8; 16])).schedule(
            SITE_COUNT,
            BODY_OFFSET,
            body + 50,
        );
        assert_eq!(perm.len(), body);
    }
}

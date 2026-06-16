//! The bit-packing layer: writes/reads whole bytes across an ordered list of carrier sites.
//!
//! The byte ↔ bit convention is **MSB-first within each byte** and is purely internal (the same
//! [`Embedder`] writes and reads), so it never needs to interoperate with another tool. The header
//! is written over a sequential site list; the body over a [`crate::selector::SiteSelector`] order.

use crate::carrier::Carrier;
use crate::error::StegoError;

/// Maps a byte stream onto a list of 1-bit sites (and back).
pub trait Embedder {
    /// Write `bytes` (`bytes.len() * 8` bits, MSB-first) into the first `bytes.len() * 8` of `sites`.
    fn write_bits(
        &self,
        carrier: &mut dyn Carrier,
        sites: &[usize],
        bytes: &[u8],
    ) -> Result<(), StegoError>;

    /// Read `byte_len` bytes (`byte_len * 8` bits, MSB-first) from the first `byte_len * 8` of `sites`.
    fn read_bits(
        &self,
        carrier: &dyn Carrier,
        sites: &[usize],
        byte_len: usize,
    ) -> Result<Vec<u8>, StegoError>;
}

/// The Phase-1 embedder: one payload bit per site, MSB-first.
#[derive(Debug, Default, Clone, Copy)]
pub struct LsbEmbedder;

impl Embedder for LsbEmbedder {
    fn write_bits(
        &self,
        carrier: &mut dyn Carrier,
        sites: &[usize],
        bytes: &[u8],
    ) -> Result<(), StegoError> {
        // The caller's capacity guard guarantees enough sites; treat a shortfall as an internal bug.
        if sites.len() < bytes.len() * 8 {
            return Err(StegoError::Internal);
        }
        for (i, &byte) in bytes.iter().enumerate() {
            for bit in 0..8 {
                let value = (byte >> (7 - bit)) & 1 == 1;
                carrier.write_bit(sites[i * 8 + bit], value);
            }
        }
        Ok(())
    }

    fn read_bits(
        &self,
        carrier: &dyn Carrier,
        sites: &[usize],
        byte_len: usize,
    ) -> Result<Vec<u8>, StegoError> {
        if sites.len() < byte_len * 8 {
            return Err(StegoError::Internal);
        }
        let mut out = vec![0u8; byte_len];
        for (i, slot) in out.iter_mut().enumerate() {
            let mut byte = 0u8;
            for bit in 0..8 {
                if carrier.read_bit(sites[i * 8 + bit]) {
                    byte |= 1 << (7 - bit);
                }
            }
            *slot = byte;
        }
        Ok(out)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::carrier::Carrier;

    /// A trivial in-memory carrier (one bit per site) for testing the embedder in isolation.
    #[derive(Debug)]
    struct VecCarrier {
        bits: Vec<bool>,
    }
    impl VecCarrier {
        fn new(n: usize) -> Self {
            Self {
                bits: vec![false; n],
            }
        }
    }
    impl Carrier for VecCarrier {
        fn site_count(&self) -> usize {
            self.bits.len()
        }
        fn read_bit(&self, site: usize) -> bool {
            self.bits[site]
        }
        fn write_bit(&mut self, site: usize, value: bool) {
            self.bits[site] = value;
        }
        fn serialize(&self) -> Result<Vec<u8>, StegoError> {
            Err(StegoError::Internal)
        }
        fn format_name(&self) -> &'static str {
            "vec"
        }
        fn kind(&self) -> crate::carrier::CarrierKind {
            crate::carrier::CarrierKind::Spatial
        }
    }

    #[test]
    fn write_then_read_roundtrips_msb_first() {
        let mut c = VecCarrier::new(64);
        let sites: Vec<usize> = (0..64).collect();
        let bytes = [0b1010_0001u8, 0x00, 0xFF, 0x7E];
        let e = LsbEmbedder;
        e.write_bits(&mut c, &sites, &bytes).unwrap();
        // MSB-first: byte 0 high bit lands on site 0.
        assert!(c.read_bit(0));
        assert!(!c.read_bit(1));
        let back = e.read_bits(&c, &sites, bytes.len()).unwrap();
        assert_eq!(back, bytes);
    }

    #[test]
    fn refuses_when_too_few_sites() {
        let mut c = VecCarrier::new(8);
        let sites: Vec<usize> = (0..8).collect();
        let e = LsbEmbedder;
        assert!(matches!(
            e.write_bits(&mut c, &sites, &[0u8, 0u8]),
            Err(StegoError::Internal)
        ));
        assert!(matches!(
            e.read_bits(&c, &sites, 2),
            Err(StegoError::Internal)
        ));
    }

    #[test]
    fn read_follows_arbitrary_site_order() {
        // The same site order on write and read recovers the bytes even when non-contiguous.
        let mut c = VecCarrier::new(32);
        let sites: Vec<usize> = (0..16).rev().collect(); // 15,14,...,0
        let e = LsbEmbedder;
        e.write_bits(&mut c, &sites, &[0xC3, 0x5A]).unwrap();
        assert_eq!(e.read_bits(&c, &sites, 2).unwrap(), vec![0xC3, 0x5A]);
    }
}

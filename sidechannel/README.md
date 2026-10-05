# sidechannel - Phase 4: side-channel-guided SecurityAccess (the novel angle)

Instrument the 0x27 seed/key exchange and use physical leakage as an extra feedback
signal for the fuzzer - and use the fuzzer to drive the ECU into the states worth measuring.

Planned (only after Phases 0-3 land a responding 0x27 on the bench):
- Capture power/EM traces around the 0x27 seed->key computation (ChipWhisperer, RESEARCH.md §4).
- **TVLA first** (Welch t-test) to *locate* leakage before any full attack (RESEARCH.md §4).
- Feed timing/side-channel observations back into `src/fuzzer` as an additional oracle
  (the DiffFuzz-style coupling, RESEARCH.md §6).

Data hygiene: raw traces are large and stay out of git (see `.gitignore`). No keys, seeds,
or vehicle-identifying data in the repo (PROJECT.md §4.6). Genuine findings -> responsible
disclosure, never raw publication.

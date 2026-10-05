# src/fuzzer - Phase 3: stateful, grammar-aware UDS fuzzer (core contribution)

The primary engineering contribution. A mutation engine over a UDS / ISO-TP grammar that
adapts to feedback: NRCs, response timings, and bus-off events.

Design sketch (do not build until Phase 2 hands over a real service map):
- **Grammar layer** - encode UDS message structure (PCI / SID / sub-function / DID / data)
  and ISO-TP framing as a mutatable grammar (Superion / Nautilus / Grammarinator ideas,
  RESEARCH.md §3). boofuzz as the pragmatic base (§3).
- **State layer** - model session state (0x10) and SecurityAccess state (0x27); drive the
  ECU into states worth testing (online state manipulation, RESEARCH.md §2).
- **Oracle** - consume Phase-2 NRC/timing signals + bus-off as feedback (ECUFuzz-style
  diagnosis-guided feedback, RESEARCH.md §2).

Phase 4 couples this fuzzer with side-channel/timing observations of 0x27 - the novel
intersection (RESEARCH.md §6, DiffFuzz). Keep the oracle interface pluggable so a
side-channel feedback source can be added without reworking the mutation engine.

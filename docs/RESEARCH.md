# VULCAN - Research Grounding

Curated, annotated bibliography for the project. It supports two tracks - **UDS/CAN fuzzing** and **side-channel analysis** - and the intersection VULCAN targets.

> Note: entries are summarized in our own words. Read the originals; do not treat these one-liners as substitutes. Entries that carry a URL were link-checked while compiling this list; the rest are well-established references to pull from the venue or Google Scholar.

---

## 0. Standards (the ground truth)

- **ISO 14229 - Unified Diagnostic Services (UDS).**  The protocol under test. Defines services (SIDs), sub-functions, DIDs, NRCs, sessions, and SecurityAccess (0x27).
- **ISO 15765-2 - Diagnostic communication over CAN (DoCAN), transport & network layer (ISO-TP).**  How multi-frame UDS messages are segmented over CAN. The fuzzer must speak this correctly.
- **ISO 11898 - Controller Area Network.**  Physical and data-link layer; relevant for termination, bitrate, and bus-off behavior.

---

## 1. Foundational automotive security

- **Koscher et al., "Experimental Security Analysis of a Modern Automobile," IEEE S&P 2010.**  First systematic academic teardown of in-vehicle networks; establishes the CAN/diagnostic threat model.
- **Checkoway et al., "Comprehensive Experimental Analyses of Automotive Attack Surfaces," USENIX Security 2011.**  Extends the attack surface to remote/indirect vectors. Context for why bench diagnostic research matters.
- **Miller & Valasek, "Remote Exploitation of an Unaltered Passenger Vehicle," 2015.**  The Jeep work; the canonical demonstration of CAN-level control. Good framing for portfolio/interview narrative.

---

## 2. UDS / diagnostic-protocol fuzzing (closest prior art)

- **Chen et al., "ECUFuzz: Structure-Aware, Diagnosis-Guided ECU Firmware Fuzzing," ISSTA 2025.**  https://chenbihuan.github.io/paper/issta25-chen-ecufuzz.pdf - Uses UDS itself (DTC polling via 0x19, clearing via 0x14, session control 0x10) as a **feedback/monitoring channel** to guide fuzzing. Directly relevant to Phase 2-3: how to read ECU state as a fuzzing oracle.
- **"Automated Threat Evaluation of Automotive Diagnostic Protocols."**  https://d-nb.info/1257161407/34 - **Online state manipulation** to trigger different ECU behaviors while testing, with a highly automated UDS scanning workflow. Core reference for the *stateful* side of our fuzzer.
- **VehicleSec/NDSS 2024, "Exploiting Diagnostic Protocol Vulnerabilities on ECUs."**  https://www.ndss-symposium.org/wp-content/uploads/vehiclesec2024-46-paper.pdf - Breaks down UDS message structure (PCI / SID / sub-function / data) and diagnostic-protocol weaknesses. Useful attack-surface map.
- **"Accelerated UDS Fuzzing (BB-FAST approach)," MDPI Electronics 2026.**  https://www.mdpi.com/2079-9292/15/6/1223 - Algorithmic optimization to speed up UDS fuzzing (demonstrated on LIN-bus, transferable ideas). Good for making a bench fuzzer practical.
- **Zhang & Li, "Diagnostic Communication and Visual System based on Vehicle UDS Protocol," arXiv:2206.12653.**  https://arxiv.org/pdf/2206.12653 - Clean, implementation-level description of a UDS client (KWP2000/DoCAN lineage). Handy reference while building our own client.

---

## 3. Grammar-aware fuzzing (the technique to adapt to UDS)

- **Wang et al., "Superion: Grammar-Aware Greybox Fuzzing," ICSE 2019.**  Grammar-aware mutation over structured inputs - the template for encoding a UDS/ISO-TP grammar into the mutator.
- **Aschermann et al., "Nautilus: Fishing for Deep Bugs with Grammars," NDSS 2019.**  Combines grammars with coverage feedback; conceptual basis for grammar + state feedback.
- **Pham et al., "Smart Greybox Fuzzing," IEEE TSE 2019.**  Structure-aware mutation for file formats; ideas transfer to protocol structure.
- **Hodován et al., "Grammarinator: A Grammar-Based Open-Source Fuzzer," 2018.**  Practical grammar-fuzzer design.
- **Peach Fuzzer / boofuzz.**  boofuzz: https://github.com/jtpereyda/boofuzz - Protocol/state fuzzing frameworks; boofuzz is the pragmatic base for Phase 3.

---

## 4. Side-channel analysis (Phase 4 foundations)

- **Kocher, Jaffe, Jun, "Differential Power Analysis," CRYPTO 1999.**  The origin of DPA; the statistical core of power side-channel attacks.
- **Brier, Clavier, Olivier, "Correlation Power Analysis with a Leakage Model," CHES 2004.**  CPA; the workhorse distinguisher we'd use against a seed-key implementation.
- **Goodwill, Jun, Jaffe, Rohatgi, "A Testing Methodology for Side-Channel Resistance Validation (TVLA)," 2011.**  The leakage-detection methodology (Welch t-test) to *find* leakage before mounting a full attack - the right first step on the cluster's 0x27 handling.
- **O'Flynn & Chen, "ChipWhisperer: An Open-Source Platform for Hardware Embedded Security Research," COSADE 2014.**  The capture/analysis platform (already in the researcher's toolkit from the ASCON masking work).

---

## 5. Automotive seed-key / SecurityAccess (the target of the novel angle)

- **"Automotive Firmware Extraction and Analysis Techniques."**  https://embercrypt.com/assets/pubs/Automotive_Firmware_Extraction_Analysis.pdf - Clear treatment of the SecurityAccess **seed-key challenge-response** and non-intrusive firmware acquisition; grounds what 0x27 actually does inside the ECU.
- **Wouters et al., "Dismantling DST80-based Immobiliser Systems," CHES 2020.**  Real-world cryptographic weaknesses in automotive immobiliser/seed-key systems; strong precedent for scrutinizing 0x27 algorithms.
- **SecurityAccess algorithm analysis (practitioner reference).**  https://reverseengineer.net/uds-securityaccess-algorithm-analysis/ - Practical view of 0x27 seed->key data flow and modern defenses (HSM-stored keys, certificate/PKI auth, AUTOSAR Secure Diagnostics). Useful for scoping what is and isn't attackable on a given ECU.

---

## 6. The intersection VULCAN targets (where the gap is)

- **Nilizadeh, Noller, Păsăreanu, "DiffFuzz: Differential Fuzzing for Side-Channel Analysis," ICSE 2019.**  Uses fuzzing to *surface* timing/space side channels in software - the clearest existing bridge between the two tracks, and a template for feedback-coupling them.

**Framing.** The prior art above treats UDS fuzzing (Section 2/3) and hardware side-channel analysis (Section 4/5) as **separate** disciplines. VULCAN's proposition is to **couple** them: use side-channel / timing observations of the SecurityAccess (0x27) exchange as an additional feedback signal to guide a grammar-aware, stateful UDS fuzzer - and conversely, use the fuzzer to drive the ECU into the states worth measuring. DiffFuzz shows the coupling is sound in software; doing it on a physical automotive ECU bench is the contribution. This is the story for ESCAR / Pwn2Own Automotive.

---

## 7. Tools (living list)

- **CaringCaribou** -  https://github.com/CaringCaribou/caringcaribou - UDS discovery & CAN listing.
- **python-can / cantools / can-isotp** -  https://github.com/hardbyte/python-can - SocketCAN Python stack + DBC parsing + ISO-TP.
- **boofuzz** -  https://github.com/jtpereyda/boofuzz - stateful protocol fuzzing base.
- **SavvyCAN** -  https://github.com/collin80/SavvyCAN - visual CAN reverse-engineering.
- **ChipWhisperer (NewAE)** -  https://github.com/newaetech/chipwhisperer - side-channel capture & analysis.

---

*Keep this file current: when a technique lands in `src/` or `sidechannel/`, link back to the entry that motivated it.*

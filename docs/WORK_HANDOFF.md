# EQAT 2.0 — пакет передачи в ChatGPT Work / технический контракт

## Результат предварительного этапа
- User-owned Excel source of truth: 71 sheets, 161 unique test IDs, 35 FullPackage fields.
- SOP drafts: 130 with separate analysis field, 8 without this field, 23 requiring authored/linked SOP.
- Two machines: A with HexaPOD + Catalyst; B without both; all photon/electron energies from Excel present on both.
- No measurements, no baseline, no validated clinical thresholds and no clinical deployment.
- Local server first; remote access later through approved secure gateway.
- Code prototype in `src/qa_program_builder.py`; tests in `tests/`.
- Source reviews are partial; no source-level regulatory compliance audit has been completed.

## Work task 1 — complete source-to-test evidence mapping
For each 161 test, find exact source document (edition, pages, section), compare:
test purpose; measurable quantity; frequency; action/warning criteria; phantom geometry; setup steps; computation; triggers; FFF/SRS special considerations; service/acceptance vs periodic QA distinction.
Output an evidence table with explicit grades: VERIFIED / CONTRADICTION / UNRESOLVED / LOCALLY_DERIVED.
Never invent page numbers or infer criteria from an unrelated standard.
Handle copyright as bibliographic citations and local paraphrased SOP, not copying proprietary manuals to GitHub.

## Work task 2 — SOP authoring
Resolve 23 missing procedure rows; fill 8 MLC analysis sections.
Produce each complete SOP version with input template, executable steps for authorized operators, formulas, assessment, troubleshooting, data to retain, references and clinician verification.
Shared procedures allowed with separate output criteria and test codes.
Require clinical QMP approval, never silently mark `approved`.

## Work task 3 — architecture + repo implementation
Build FastAPI + React/TS + PostgreSQL module with immutable test/SOP/criterion versions and machine feature history.
Deliver database migrations, typed API, import of `data/test_definitions.json`, schema validation, two-machine program builder and audit log.
No direct connections to LINAC, iCOM, MOSAIQ or clinical OIS on the MVP.
Use read-only DICOM/TRF import on manually exported/de-identified fixtures.
Use version-pinned PyMedPhys and Pylinac only after source/API audit.

## Work task 4 — compare QATrack+ options
Evaluate (A) QATrack+ integration with EQAT analytic workers vs (B) own QA Management:
permissions, digital signatures, QA schedules, review stages, multi-machine support, self-hosting, API, licensing, maintainability and migration. Document recommendation with dependencies and costs/risks. Do not assume pyQAserver current dependencies are supported.

## Work task 5 — next milestone acceptance tests
- Exactly 161 unique tests imported.
- Per-test source/provenance and SOP status surfaced.
- Complete 35 FullPackage fields preserved separately, without duplication of registry tests.
- A: HEX and SGRT eligible; B: HEX 15 + SGRT 20 not applicable.
- ABC, XVI, iView per-machine availability unknown until confirmed; no false PASS/FAIL or assumed baseline.
- Approval workflow prevents scheduling unapproved clinical procedures.
- QA run stores parent dataset checksum, algorithm version, test/SOP/criterion version, operator and reviewer.
- At least one machine config change produces a new program revision while historical results remain unchanged.
- Authorization rejects write operations to connected clinical systems.
- All generated fixtures are synthetic, with no real patient identifiers.

## Non-negotiable safety constraints
No production deployment or automated beam delivery. No edits to iCOM-CAT/SRI/service configs. No MOSAIQ SQL writes. No patient data in GitHub. No false equivalence between TRF consistency and dosimetric PSQA. Remote access only after security review.

## Open factual questions — not blockers for design
Machine serial numbers and precise Integrity/TCS versions; XVI/iView and ABC distribution; availability/calibration of QuickCheck, Octavius 4D Rotation Unit, TOR 18FG, pencil CTDI chamber, other metrology; vendor document version matching actual machine; local regulatory/approval process.

## Files
`README.md`; `data/`; `schemas/`; `src/`; `tests/`; `docs/`.

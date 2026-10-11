# ADR-0001: Automated SBOM and CBOM Supply Chain Governance Pipeline

## Metadata

| Field | Value |
|---|---|
| ADR ID | ADR-0001 |
| Status | Accepted |
| Created Date | 2026-10-11 |
| Decision Date | 2026-10-11 |
| Effective Date | 2026-10-11 |
| Architecture Domain | Security / Supply Chain Governance / Cryptography / DevOps |
| Scope | Software & Cryptographic Supply Chain Security (Repository & CI/CD) |
| Decision Owner | Lead DevSecOps Architect |
| Named Decision Maker | DevSecOps Engineering & Identity Architecture Team |
| Approval Authority | Architecture Review Board (ARB) / Security Governance Committee |
| Approval Evidence ID | ARB-2026-10-SEC-007 |
| APM Code(s) | SEC-SUPPLYCHAIN-01 |
| NIRA Reference(s) | NIRA-SEC-2026-044 |
| Tags | sbom, cbom, cyclonedx, spdx, supply-chain, pqc, oauth2, dcr, mtls, jwks, par, pkce, keycloak, ast-analysis, devsecops |

---

## Business and Architecture Context

### Problem Statement

The `DCR-demo` repository provides an end-to-end reference implementation and demonstration harness for high-assurance OAuth 2.0 / OpenID Connect (OIDC) architectures. It showcases:
1. **Dynamic Client Registration (RFC 7591 / OIDC DCR)**: Automated registration of clients against identity providers (Keycloak).
2. **Mutual TLS (mTLS) Authentication (RFC 8705)**: Certificate-bound access tokens and mutual TLS client authentication.
3. **JSON Web Key Sets (JWKS) & Private Key JWT (RFC 7523)**: Cryptographic client assertion validation and key rotation.
4. **Pushed Authorization Requests (PAR / RFC 9126)** and **Proof Key for Code Exchange (PKCE / RFC 7636)**: Hardened front-channel flows preventing interception attacks.
5. **On-the-fly Public Key Infrastructure (PKI)**: Automated X.509 CA, server, and client certificate issuance via Python's `cryptography` library.

Because this codebase actively provisions cryptographic assets (X.509 certificates, RSA 2048-bit keypairs, SHA-256 digital signatures) and integrates with identity platforms (Keycloak 26.0), it serves as a critical model for zero-trust authorization architectures.

Modern cybersecurity and software supply chain mandates—such as Executive Order 14028, NIST SP 800-218 (Secure Software Development Framework - SSDF), NIST SP 800-63B (Digital Identity Guidelines), and NIST IR 8547 (PQC Transition Guidance)—require verifiable software inventories via Software Bills of Materials (SBOMs) and cryptographic asset tracking via Cryptographic Bills of Materials (CBOMs).

Without an automated, continuous SBOM and CBOM pipeline embedded directly into continuous integration (CI):
1. **Supply Chain Vulnerability Blind Spots:** Third-party Python dependencies (e.g., `cryptography`, `requests`), container images (Keycloak 26), and GitHub Actions risk untracked vulnerabilities, transitive CVEs, and integrity drift.
2. **Cryptographic Opacity:** Cryptographic algorithms, key sizes, and certificate generation routines across scripts (`setup.py`, `jwks_dcr_demo.py`, `par_mtls_visual.py`, `mtls_pkce_demo.py`) lack formal, machine-readable inventorying and discovery.
3. **PQC Transition Gap:** As organizations transition toward post-quantum standards (NIST FIPS 203 ML-KEM, FIPS 204 ML-DSA, FIPS 205 SLH-DSA), distinguishing quantum-resilient mechanisms from quantum-vulnerable public key algorithms (e.g., RSA-2048 client assertions, classical mTLS certificates) requires automated, reproducible auditing.
4. **Attestation Deficit:** External auditors and enterprise consumers lack machine-readable, standards-compliant CycloneDX and SPDX attestations verifying the repository's supply chain integrity and cryptographic agility.

### Current Situation

Prior to this decision, `DCR-demo` maintained automated setup and interactive DCR demonstration workflows, but:
1. No automated CI workflow existed to generate, validate, and publish SBOMs or CBOMs upon branch commits or pull requests.
2. Cryptographic scanning was not integrated into repository testing or AST call-site analysis.
3. There were no build gates to catch schema non-conformance or empty supply chain inventories.
4. Cryptographic auditing and PQC migration readiness were not continuously reported to project documentation.

### Decision Drivers

- **Cryptographic Visibility & Identity Governance:** Automated cataloging of all digital signature algorithms, key lengths, hash digests, and PKI certificate workflows across source code.
- **Regulatory & Compliance Alignment:** Direct conformance with EO 14028, NTIA minimum SBOM elements, NIST SSDF, and CycloneDX v1.5–1.7 / SPDX v2.3 standards.
- **Continuous Quality & Gate Enforcement:** Automated test gates in CI ensuring schema validity, non-empty components, and verified cryptographic metadata.
- **Dual-Engine Interoperability:** Support for both SPDX (v2.3) and CycloneDX (v1.7) formats to enable seamless integration with modern DevSecOps scanners and policy engines.
- **Parity Between Local & CI Workflows:** Developer-friendly CLI scripts mirroring CI execution for fast local validation.

---

## Assumptions

- The repository codebase consists of Python automation, PKI generation, and HTTP demonstration scripts interfacing with containerized Keycloak services.
- Build environments support Python 3.11+ and GitHub Actions runner environments executing Node 24 compliant actions.
- Post-Quantum Cryptography transition will require continuous visibility across software dependencies, network cipher suites, and credential algorithms over the multi-year migration window.

---

## Constraints

- CI workflows must execute within standard GitHub-hosted runner environments without introducing excessive build latency (< 2-3 minutes).
- Tooling must execute locally via standard Python and Bash scripts without requiring proprietary commercial SaaS dependencies.
- All GitHub Actions must use immutable SHA-pinned references and comply with Node 24 runtime standards.

---

## Alternatives Considered

| Option | Advantages | Disadvantages / Risks | Disposition |
|---|---|---|---|
| **Option 1: Status Quo (Ad-hoc Manual Reviews)** | Zero CI runtime overhead; no workflow maintenance. | High operational and compliance risk; inventory quickly becomes obsolete; zero automated detection of cryptographic regressions. | **Rejected** |
| **Option 2: Standalone SBOM-Only Scanning (Syft Only)** | Simple pipeline; fast CycloneDX/SPDX generation. | Lacks cryptographic asset identification; fails to inspect PKI/crypto primitives or provide CBOM inventories. | **Rejected** |
| **Option 3: cbomkit-Only Scanner** | Captures cryptographic assets in CycloneDX format. | Omits SPDX SBOM generation required by enterprise procurement standards; lacks custom AST call-site analysis. | **Rejected** |
| **Option 4: Integrated Dual-Engine SBOM/CBOM + AST Analysis + Automated CI Harness (Selected)** | Comprehensive coverage: dual-engine SBOM (CycloneDX & SPDX via Anchore/Syft) and CBOM (cbomkit); semantic AST cryptographic scanning (`scan_crypto_ast.py`); automated validation harness (`test_boms.sh`); automated PQC readiness reporting (`analyze_cbom.py`); identical local execution scripts. | Slight increase in CI workflow duration (~60-90s); requires Python 3.11 runtime setup in CI runner; produces artifacts requiring retention policies. | **Selected** |

---

## Decision

### Selected Option

Adopt **Option 4: Integrated Dual-Engine SBOM/CBOM + AST Analysis + Automated CI Harness** across the repository.

Specifically:
1. **GitHub Actions Workflow (`.github/workflows/sbom-cbom.yml`):**
   - Configured with Node 24 pinned actions (`actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1`, `anchore/sbom-action@006b7ce8314066bdf1765b4500370d40fa6917a3`, `cbomkit/cbomkit-action@34a3d960625ae7f7f1b59455eff93a96df090eb7`, `actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065`, `actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02`).
   - Generates both CycloneDX JSON (`oss/sbom.cyclonedx.json`) and SPDX JSON (`oss/sbom.spdx.json`) SBOMs via Anchore / Syft.
   - Generates CycloneDX CBOM (`oss/cbom.json`) via `cbomkit`.
   - Executes semantic AST cryptographic analysis via `scripts/scan_crypto_ast.py`.
   - Executes validation and test harness via `scripts/test_boms.sh`.
   - Assesses Post-Quantum Cryptography (PQC) readiness and outputs dashboard summaries via `scripts/analyze_cbom.py`.
   - Automatically maintains `docs/security/CRYPTOGRAPHIC_AUDIT.md` and archives BOM artifacts.
2. **Local Tooling Suite (`scripts/`):**
   - `scripts/generate_boms.sh`: Portable CLI script for local generation across source trees or Docker images.
   - `scripts/test_boms.sh`: Strict verification harness testing syntax, CycloneDX schema conformance, and component counts.
   - `scripts/scan_crypto_ast.py`: Python AST walker identifying cryptographic call-sites, key generation, and cipher instantiations.
   - `scripts/analyze_cbom.py`: PQC readiness analysis, algorithm categorization, and Markdown/JSON report generator.
   - `scripts/attach_oci_bom.sh` & `scripts/fetch_oci_cbom.py`: OCI artifact publishing and retrieval utilities.

### Rationale

This multi-tiered architecture provides defense-in-depth supply chain and cryptographic visibility. For a repository implementing OAuth 2.0 Dynamic Client Registration, mTLS mutual authentication, and cryptographic client assertions, uniting package-level SBOM inventories with cryptographic CBOM asset tracking and AST call-site analysis bridges the gap between third-party dependency vulnerabilities and application cryptographic posture. Automated testing in CI ensures corrupt, incomplete, or drifting BOMs fail fast prior to release.

---

## Consequences

### Benefits

- **Continuous Compliance:** Instant audit readiness for modern SBOM/CBOM standards across both SPDX and CycloneDX specifications.
- **PQC Migration Visibility:** Continuous visibility into quantum-vulnerable algorithms (RSA-2048 digital signatures and classical mTLS) alongside quantum-safe hash functions (SHA-256) across dependencies and source code.
- **Automated Verification:** The `test_boms.sh` harness prevents empty or schema-invalid BOMs from being published.
- **Dual Developer & CI Experience:** Developers can run identical verification locally prior to pushing code.

### Trade-offs and Negative Consequences

- **CI Pipeline Latency:** Adds approximately 60-90 seconds to workflow execution time.
- **Maintenance Overhead:** Periodic updates to tool action SHAs and known algorithm catalogs (`known_cbom_catalog.json`) are required as cryptographic standards evolve.
- **Artifact Storage:** Retention of BOM artifacts in GitHub Actions consumes artifact storage quota (mitigated with 90-day retention policy).

### New Constraints

- Repository CI runners must provide Python 3.11+ runtime for AST and analysis scripts.
- GitHub Actions token permissions must grant `contents: write` for automated cryptographic audit report synchronization on `main` branch pushes.

### Follow-on Decisions and Activities

- Configure pull request checks to fail if high-risk deprecated algorithms (e.g., MD5 for digital signatures, DES, RC4) are newly introduced in source call-sites.
- Establish an automated schedule for nightly container image baseline scans (`scripts/generate_boms.sh -t docker`).
- Integrate OCI cosign / notation attestation signing for generated BOM artifacts in release workflows.

---

## Security, Privacy, and Risk Considerations

- **Integrity & Authenticity:** All workflow dependencies use immutable SHA-256 commit pins to mitigate supply chain tampering of actions.
- **Confidentiality:** Scans inspect public dependencies and cryptographic declarations; no secret keys, private keys, or credentials are embedded in generated BOM artifacts.
- **Supply Chain Traceability:** BOMs link directly to commit SHAs and repository metadata.

---

## Technical Debt Assessment

- **Catalog Maintenance:** The static cryptographic catalog in `scripts/known_cbom_catalog.json` must be reviewed annually against NIST PQC standardization updates.

---

## Review and Lifecycle

- **Review Schedule:** Annual or upon major NIST PQC milestone release.
- **Supersedes:** None (Initial baseline governance record).
- **Superseded By:** None.

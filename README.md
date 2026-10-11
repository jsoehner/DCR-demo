# OAuth 2.0 Dynamic Client Registration (DCR) & Advanced Security Suite

This repository provides an automated, hands-on demonstration and reference architecture for high-assurance **OAuth 2.0 and OpenID Connect (OIDC)** security patterns using containerized **Keycloak 26.0** and Python cryptographic automation.

It showcases end-to-end implementations of:
- **Dynamic Client Registration (RFC 7591 / OIDC DCR)**: Registering clients programmatically with software statements and JWKS.
- **Mutual TLS (mTLS) Client Authentication (RFC 8705)**: Zero-shared-secret authentication utilizing X.509 client certificates and certificate-bound access tokens.
- **JSON Web Key Sets (JWKS) & Private Key JWT (RFC 7523)**: Client assertions signed with dedicated asymmetric RSA keys (`private_key_jwt`).
- **Pushed Authorization Requests (PAR / RFC 9126)**: Secure authorization code flow preventing request tampering and URI leakage.
- **Proof Key for Code Exchange (PKCE / RFC 7636)**: Authorization code interception mitigation.
- **Automated Public Key Infrastructure (PKI)**: Dynamic generation of root CA, server certificates, and client certificates via Python's `cryptography` library.

---

## Architecture & Demonstration Modules

| Script / Module | Protocol Standard | Description |
|---|---|---|
| [`setup.py`](setup.py) | PKI / Docker | Generates CA and server X.509 certificates, writes `docker-compose.yml`, boots Keycloak 26 over mTLS HTTPS (port 8443), and initializes realm configuration. |
| [`jwks_dcr_demo.py`](jwks_dcr_demo.py) | RFC 7591 / RFC 7523 | Generates an RSA-2048 keypair, formats a public JWKS, registers the client dynamically via Keycloak's DCR endpoint, and authenticates using signed JWT assertions. |
| [`jwks_dcr_visual.py`](jwks_dcr_visual.py) | RFC 7591 / RFC 7523 | Visual step-by-step walkthrough of the JWKS DCR and JWT assertion lifecycle with formatted inspection banners. |
| [`mtls_client_creds_visual.py`](mtls_client_creds_visual.py) | RFC 8705 | Demonstrates Client Credentials Grant where client identity is verified via mutual TLS client certificate exchange against Keycloak. |
| [`par_mtls_visual.py`](par_mtls_visual.py) | RFC 9126 / RFC 8705 | Executes Pushed Authorization Requests (PAR) over mTLS, obtaining a secure `request_uri` reference prior to browser redirection. |
| [`mtls_pkce_demo.py`](mtls_pkce_demo.py) | RFC 7636 / RFC 8705 | Combined mTLS authentication and PKCE (code verifier / code challenge) authorization code flow. |
| [`setup_pkce.py`](setup_pkce.py) | RFC 7636 | Automated client and user configuration for PKCE testing against Keycloak. |

---

## Prerequisites & Getting Started

### Prerequisites

- **Python 3.11+**
- **Docker & Docker Compose** (for running Keycloak 26 container)
- Python packages:
  ```bash
  pip install cryptography requests
  ```

### Quickstart

1. **Bootstrap Keycloak and PKI:**
   ```bash
   python3 setup.py
   ```
   This generates the X.509 certificate authority and server certificates under `certs/`, spins up the `quay.io/keycloak/keycloak:26.0` container on `https://127.0.0.1:8443`, and configures the `master` realm.

2. **Run the JWKS Dynamic Client Registration Demo:**
   ```bash
   python3 jwks_dcr_visual.py
   ```

3. **Run the Pushed Authorization Requests (PAR) + mTLS Demo:**
   ```bash
   python3 par_mtls_visual.py
   ```

4. **Run the Mutual TLS Client Credentials Demo:**
   ```bash
   python3 mtls_client_creds_visual.py
   ```

---

## Automated SBOM & CBOM Supply Chain Pipeline

This repository integrates an automated Software Bill of Materials (SBOM) and Cryptographic Bill of Materials (CBOM) supply chain pipeline to satisfy modern security and compliance mandates (Executive Order 14028, NIST SP 800-218 SSDF, and NIST IR 8547 PQC Migration Guidance).

### CI Pipeline Stages

The GitHub Actions workflow [`.github/workflows/sbom-cbom.yml`](.github/workflows/sbom-cbom.yml) executes on every push to `main` and all pull requests:

1. **Dual-Engine SBOM Generation**: Uses `anchore/sbom-action` to generate standard CycloneDX (`oss/sbom.cyclonedx.json`) and SPDX (`oss/sbom.spdx.json`) inventory files.
2. **Cryptographic Bill of Materials (CBOM)**: Uses `cbomkit/cbomkit-action` to discover cryptographic algorithms, certificates, keys, and cryptographic assets (`oss/cbom.json`).
3. **Dual-Engine AST Semantic Crypto Scan**: Executes `scripts/scan_crypto_ast.py` to parse source code abstract syntax trees (ASTs), mapping cryptographic call-sites, key generations (e.g., RSA-2048, X.509), and cipher initializations to the CBOM inventory.
4. **Automated Verification Harness**: Runs `scripts/test_boms.sh` to validate JSON schemas, verify required CycloneDX attributes, and enforce non-empty inventory thresholds as a build gate.
5. **Post-Quantum Cryptography (PQC) Assessment**: Runs `scripts/analyze_cbom.py` to classify cryptographic assets by quantum-readiness and output markdown summary dashboards to `$GITHUB_STEP_SUMMARY`.
6. **Continuous Governance Publishing**: Automatically syncs the latest cryptographic posture to [`docs/security/CRYPTOGRAPHIC_AUDIT.md`](docs/security/CRYPTOGRAPHIC_AUDIT.md) and publishes all BOM assets to workflow artifacts.

---

## Local Scripts & Verification

All pipeline stages can be executed locally in development environments using scripts in `scripts/`:

### 1. Generating BOMs (`scripts/generate_boms.sh`)

Generate SBOMs and CBOMs for either source directories or Docker container images:

```bash
# Scan current repository directory (outputs to oss/)
bash scripts/generate_boms.sh -t dir .

# Scan a local Docker image
bash scripts/generate_boms.sh -t docker DCR-demo:local

# Specify custom output directory and format
bash scripts/generate_boms.sh -t dir -o build/boms -f cyclonedx-json .
```

### 2. Testing & Validating BOMs (`scripts/test_boms.sh`)

Run automated JSON validation, schema verification, and inventory count checks:

```bash
bash scripts/test_boms.sh oss
```

### 3. Scanning Source AST for Crypto Callsites (`scripts/scan_crypto_ast.py`)

Scan Python and repository source code ASTs for cryptographic primitive invocations and reconcile with an existing CBOM:

```bash
python3 scripts/scan_crypto_ast.py . \
  --cbom oss/cbom.json \
  --output-json oss/crypto-callsites.json
```

### 4. PQC Readiness Analysis (`scripts/analyze_cbom.py`)

Analyze a generated CBOM against software dependencies and generate markdown or JSON risk summaries:

```bash
python3 scripts/analyze_cbom.py oss/cbom.json \
  --sbom oss/sbom.spdx.json \
  --json oss/crypto-analysis.json \
  --markdown docs/security/CRYPTOGRAPHIC_AUDIT.md
```

### 5. OCI Artifact Attachment (`scripts/attach_oci_bom.sh` & `scripts/fetch_oci_cbom.py`)

Publish and retrieve CBOMs attached to OCI container registries:

```bash
# Attach CBOM to container image in registry
bash scripts/attach_oci_bom.sh oss/cbom.json my-registry.io/app:v1.0.0

# Fetch CBOM from container image
python3 scripts/fetch_oci_cbom.py my-registry.io/app:v1.0.0 --output-dir oss
```

---

## Architectural Decision Records (ADRs)

Key architectural decisions governing this repository's security, supply chain, and cryptography strategy are documented under [`docs/adr/`](docs/adr/):

- [**ADR-0001: Automated SBOM and CBOM Supply Chain Governance Pipeline**](docs/adr/0001-automated-sbom-cbom-supply-chain-governance.md) - Context, alternatives considered, decision rationale, and downstream consequences for adopting automated dual-engine SBOM/CBOM scanning, AST call-site analysis, and CI gate verification.

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

## 🔐 SBOM, CBOM & PQC Governance

This repository integrates the [`jsoehner/jsi-bom-actions`](https://github.com/jsoehner/jsi-bom-actions) GitHub Action ([`.github/workflows/sbom-cbom.yml`](.github/workflows/sbom-cbom.yml)) for automated Software Bill of Materials (SBOM), Cryptographic Bill of Materials (CBOM), and Post-Quantum Cryptography (PQC) readiness auditing.

- **Latest Audit Report:** [`docs/security/CRYPTOGRAPHIC_AUDIT.md`](docs/security/CRYPTOGRAPHIC_AUDIT.md)
- **Learn More:** [jsoehner/jsi-bom-actions](https://github.com/jsoehner/jsi-bom-actions)

---

## Architectural Decision Records (ADRs)

Key architectural decisions governing this repository's security, supply chain, and cryptography strategy are documented under [`docs/adr/`](docs/adr/):

- [**ADR-0001: Automated SBOM and CBOM Supply Chain Governance Pipeline**](docs/adr/0001-automated-sbom-cbom-supply-chain-governance.md) - Context, alternatives considered, decision rationale, and downstream consequences for adopting automated dual-engine SBOM/CBOM scanning, AST call-site analysis, and CI gate verification.

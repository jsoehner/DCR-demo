## 🛡️ Cryptographic Bill of Materials (CBOM) & PQC Migration Assessment

**Format**: CycloneDX (v1.6) | **First-Party Code Crypto Assets**: 2 | **Total Tracked Crypto Assets**: 2

### 📊 Post-Quantum Migration Scorecard

| Metric | Count | Migration Status |
|---|---|---|
| **Post-Quantum Ready (PQC)** | **0** | 🟢 Quantum-Resistant (NIST FIPS 203/204/205) |
| **Quantum-Vulnerable (Backlog)** | **1** | 🔴 At Risk of 'Harvest Now, Decrypt Later' |
| **Classical Symmetric / Digest** | **1** | 🟡 Classical Security (Requires AES-256 / SHA-256+) |
| **Asymmetric PQC Migration Progress** | **0.0%** | (0 of 1 asymmetric primitives migrated) |

### 🎯 Cryptographic Supply Chain Coverage & Confidence

| Evaluation Layer | Coverage / Status | Audit Confidence Assessment |
|---|---|---|
| **First-Party Code (`src/`)** | **100% Audited** (0 Custom Primitives) | 🟢 **HIGH** (Direct AST & SAST verified clean) |
| **Third-Party Supply Chain** | **No external dependencies in SBOM** | 🟢 **HIGH** (Self-contained scope) |

| **System OS Inventory** | **Pending Update** | 🟡 **Warning** (Local OS crypto components not yet inventoried) |

### ✅ Post-Quantum Ready Assets

> ⚠️ **No Post-Quantum Ready assets detected.** Immediate migration planning recommended for asymmetric key exchanges and digital signatures.

### ⚠️ Quantum-Vulnerable Assets & Remediation Plan

| Component / Algorithm | Type / Primitive | Key Length / Curve | Recommended Target | Provenance / Context |
|---|---|---|---|---|
| **`RSA-2048`**<br><sub>RSA-2048</sub> | algorithm / signature | 2048 | **ML-KEM-768 / Kyber (FIPS 203)** | First-Party Code (SAST/AST)<br>`jwks_dcr_demo.py:22`<br><sub><code>from cryptography.hazmat.primitives.asymmetric import rsa, padding</code></sub><br><br>`jwks_dcr_demo.py:226`<br><sub><code>Console.explain("Generating a dedicated RSA 2048-bit Key Pair for the App.")</code></sub><br><br>`jwks_dcr_demo.py:227`<br><sub><code>self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)</code></sub><br><br>`jwks_dcr_demo.py:330`<br><sub><code>ca_key = rsa.generate_private_key(65537, 2048)</code></sub><br><br>`jwks_dcr_demo.py:337`<br><sub><code>srv_key = rsa.generate_private_key(65537, 2048)</code></sub><br><br>`par_mtls_visual.py:22`<br><sub><code>from cryptography.hazmat.primitives.asymmetric import rsa, padding</code></sub><br><br>`mtls_pkce_demo.py:22`<br><sub><code>from cryptography.hazmat.primitives.asymmetric import rsa, padding</code></sub><br><br>`mtls_client_creds_visual.py:17`<br><sub><code>from cryptography.hazmat.primitives.asymmetric import rsa, padding</code></sub><br><br>`setup.py:14`<br><sub><code>from cryptography.hazmat.primitives.asymmetric import rsa</code></sub><br><br>`setup_pkce.py:19`<br><sub><code>from cryptography.hazmat.primitives.asymmetric import rsa</code></sub><br><br>`jwks_dcr_visual.py:22`<br><sub><code>from cryptography.hazmat.primitives.asymmetric import rsa, padding</code></sub><br><br>`jwks_dcr_visual.py:226`<br><sub><code>Console.explain("Generating a dedicated RSA 2048-bit Key Pair for the App.")</code></sub><br><br>`jwks_dcr_visual.py:227`<br><sub><code>self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)</code></sub><br><br>`jwks_dcr_visual.py:330`<br><sub><code>ca_key = rsa.generate_private_key(65537, 2048)</code></sub><br><br>`jwks_dcr_visual.py:337`<br><sub><code>srv_key = rsa.generate_private_key(65537, 2048)</code></sub> |

### 🔒 Classical Symmetric & Digest Assets

| Component Name | Primitive | Key Length | Quantum Resistance Assessment | Provenance / Location(s) |
|---|---|---|---|---|
| `SHA-256` | hash | 256 | Quantum-Resistant (Grover's proof) | First-Party Code (SAST/AST)<br>`jwks_dcr_demo.py:172`<br>`jwks_dcr_demo.py:222`<br>`jwks_dcr_demo.py:334`<br>`jwks_dcr_demo.py:341`<br>`jwks_dcr_visual.py:172`<br>`jwks_dcr_visual.py:222`<br>`jwks_dcr_visual.py:334`<br>`jwks_dcr_visual.py:341` |

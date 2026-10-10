## 🛡️ Cryptographic Bill of Materials (CBOM) & PQC Migration Assessment

**Format**: CycloneDX (v1.6) | **Total Components**: 5 | **Crypto Assets**: 5

### 📊 Post-Quantum Migration Scorecard

| Metric | Count | Migration Status |
|---|---|---|
| **Post-Quantum Ready (PQC)** | **0** | 🟢 Quantum-Resistant (NIST FIPS 203/204/205) |
| **Quantum-Vulnerable (Backlog)** | **1** | 🔴 At Risk of 'Harvest Now, Decrypt Later' |
| **Classical Symmetric / Hashing** | **4** | 🟡 Classical Security (Requires AES-256 / SHA-256+) |
| **Asymmetric PQC Migration Progress** | **0.0%** | (0 of 1 asymmetric primitives migrated) |

### ✅ Post-Quantum Cryptography Migrated Assets

> ⚠️ **No Post-Quantum Ready assets detected.** Immediate migration planning recommended for asymmetric key exchanges and digital signatures.

### ⚠️ Quantum-Vulnerable Assets & Remediation Plan

| Component / Algorithm | Type / Primitive | Key Length / Curve | Recommended Target | Source Location(s) & Code Context |
|---|---|---|---|---|
| **`RSA-2048`**<br><sub>RSA-2048</sub> | algorithm / pke | 2048 | **ML-KEM-768 / Kyber (FIPS 203)** | `setup.py`<br><br>`setup.py`<br><br>`setup.py`<br><br>`setup.py:14`<br><sub><code>from cryptography.hazmat.primitives.asymmetric import rsa</code></sub><br><br>`setup.py:167`<br><sub><code>print(f"      [App] Generating RSA Keys...")</code></sub><br><br>`setup.py:168`<br><sub><code>self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)</code></sub><br><br>`setup.py:253`<br><sub><code>self.ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)</code></sub><br><br>`setup.py:263`<br><sub><code>srv_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)</code></sub> |

### 🔒 Classical Symmetric & Digest Assets

| Component Name | Primitive | Key Length | Quantum Resistance Assessment | Location(s) |
|---|---|---|---|---|
| `private-key@d3b0e8ee-190f-4595-99c1-16422d2a1b88` | unknown | N/A | Review key length for Grover resistance | `setup.py` |
| `private-key@6ef05d51-57fc-4f0a-b32f-d2aad4f290eb` | unknown | N/A | Review key length for Grover resistance | `setup.py` |
| `private-key@8d7a4a88-5ffc-4fd9-bfed-14ff3abe4a7d` | unknown | N/A | Review key length for Grover resistance | `setup.py` |
| `SHA-256` | hash | 256 | Quantum-Resistant (Grover's proof) | `setup.py:175`<br>`setup.py:257`<br>`setup.py:267`<br>`setup.py:314` |

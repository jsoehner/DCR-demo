import os
import time
import subprocess
import shutil
import requests
import json
import sys
import ipaddress
import textwrap
from datetime import datetime, timedelta, timezone
from cryptography import x509
from cryptography.x509.oid import NameOID, ExtendedKeyUsageOID, ExtensionOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# --- CONFIGURATION ---
BASE_DIR = os.getcwd()
CERT_DIR = os.path.join(BASE_DIR, "certs")
COMPOSE_FILE = os.path.join(BASE_DIR, "docker-compose.yml")
KC_PORT = 8443
KC_URL = f"https://127.0.0.1:{KC_PORT}"
REALM = "master"
ADMIN_USER = "admin"
ADMIN_PASS = "admin"

# Docker Compose Template
DOCKER_COMPOSE_TEMPLATE = """
services:
  keycloak:
    image: quay.io/keycloak/keycloak:26.0
    container_name: mtls_keycloak
    command: start-dev --http-enabled=false --https-client-auth=request
    environment:
      KEYCLOAK_ADMIN: {admin_user}
      KEYCLOAK_ADMIN_PASSWORD: {admin_pass}
      KC_HTTPS_CERTIFICATE_FILE: /opt/keycloak/conf/server.crt.pem
      KC_HTTPS_CERTIFICATE_KEY_FILE: /opt/keycloak/conf/server.key.pem
      KC_HTTPS_TRUST_STORE_FILE: /opt/keycloak/conf/ca.crt.pem
      KC_HTTPS_TRUST_STORE_PASSWORD: password
      KC_HTTPS_TRUST_STORE_TYPE: PEM
      KC_SPI_X509CERT_LOOKUP_PROVIDER: default
      KC_SPI_X509CERT_LOOKUP_DEFAULT_SSL_CLIENT_CERT_SUBJECT_DN: true
      KC_LOG_LEVEL: info
    volumes:
      - {cert_dir}:/opt/keycloak/conf:ro,z
    ports:
      - "{port}:{port}"
"""

# --- DEBUGGING TOOL (ENHANCED PARSER) ---
class DebugLogger:
    @staticmethod
    def _parse_x509_name(name):
        return name.rfc4514_string()

    @staticmethod
    def inspect_pem(title, pem_bytes):
        print(f"\n      📄 [INTERNAL ARTIFACT: {title}]")
        print("      " + "-" * 50)
        print(textwrap.indent(pem_bytes.decode('utf-8').strip(), '      '))
        print("      " + "-" * 50)

        try:
            # Try parsing as Certificate
            cert = x509.load_pem_x509_certificate(pem_bytes)
            DebugLogger._print_cert_details(cert)
        except ValueError:
            try:
                # Try parsing as CSR
                csr = x509.load_pem_x509_csr(pem_bytes)
                DebugLogger._print_csr_details(csr)
            except ValueError:
                print("      [!] Could not parse PEM as Cert or CSR.")

    @staticmethod
    def _print_cert_details(cert):
        print("      🔎 DECODED CERTIFICATE DETAILS")
        print("      ------------------------------")
        print(f"      Subject:      {DebugLogger._parse_x509_name(cert.subject)}")
        print(f"      Issuer:       {DebugLogger._parse_x509_name(cert.issuer)}")
        print(f"      Serial Num:   {cert.serial_number} (0x{cert.serial_number:x})")
        print(f"      Not Before:   {cert.not_valid_before_utc}")
        print(f"      Not After:    {cert.not_valid_after_utc}")
        print(f"      Sig Algo:     {cert.signature_algorithm_oid._name}")
        print("      Extensions:")
        for ext in cert.extensions:
            crit = " (Critical)" if ext.critical else ""
            val = str(ext.value).replace("<", "").replace(">", "")
            # Clean up representation for readability
            if isinstance(ext.value, x509.KeyUsage):
                usages = [k for k, v in ext.value.__dict__.items() if v and k.startswith('_') is False]
                val = ", ".join(usages)
            elif isinstance(ext.value, x509.ExtendedKeyUsage):
                val = ", ".join([u._name for u in ext.value])
            elif isinstance(ext.value, x509.SubjectAlternativeName):
                val = ", ".join([str(n.value) for n in ext.value])
            
            print(f"       - {ext.oid._name}: {val}{crit}")
        print("      ------------------------------")

    @staticmethod
    def _print_csr_details(csr):
        print("      🔎 DECODED CSR DETAILS")
        print("      ----------------------")
        print(f"      Subject:      {DebugLogger._parse_x509_name(csr.subject)}")
        print(f"      Sig Algo:     {csr.signature_algorithm_oid._name}")
        print("      Extensions (Requested):")
        for ext in csr.extensions:
            crit = " (Critical)" if ext.critical else ""
            print(f"       - {ext.oid._name}{crit}")
        
        if not csr.is_signature_valid:
            print("      [!] WARNING: CSR Signature Invalid")
        print("      ----------------------")

    @staticmethod
    def inspect_request(actor, method, url, headers=None, body=None, cert_used=None):
        print(f"\n      🔵 {actor} -> IdP REQUEST")
        print(f"      METHOD: {method} {url}")
        
        if cert_used:
            print(f"      🔐 mTLS CERT PRESENT: {cert_used}")
        else:
            print(f"      🔓 mTLS CERT: NONE (Standard TLS)")
            
        if headers:
            safe_headers = headers.copy()
            if 'Authorization' in safe_headers:
                token_preview = safe_headers['Authorization'][:20] + "..."
                safe_headers['Authorization'] = token_preview
            print(f"      HEADERS: {json.dumps(safe_headers)}")
            
        if body:
            print(f"      PAYLOAD:")
            print(textwrap.indent(json.dumps(body, indent=2), '        '))

    @staticmethod
    def inspect_response(actor, response):
        icon = "🟢" if response.status_code < 400 else "🔴"
        print(f"\n      {icon} IdP -> {actor} RESPONSE ({response.status_code})")
        try:
            data = response.json()
            if 'access_token' in data:
                data['access_token'] = f"{data['access_token'][:25]}...[truncated]"
            if 'refresh_token' in data:
                data['refresh_token'] = "..."
            print(textwrap.indent(json.dumps(data, indent=2), '        '))
        except:
            print(f"      {response.text}")

# ==========================================
#  CLASS: APP (The Client)
# ==========================================
class SampleServiceProvider:
    def __init__(self, client_name, org_name):
        self.client_name = client_name
        self.org_name = org_name
        self.dn_str = f"CN={client_name},O={org_name},C=US"
        self.private_key = None
        self.certificate = None 
        self.client_id = None
        self.session = requests.Session()
        self.session.trust_env = False

    def generate_identity_and_csr(self):
        print(f"      [App] Generating RSA Keys...")
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        
        print(f"      [App] Generating Certificate Signing Request (CSR)...")
        csr = x509.CertificateSigningRequestBuilder().subject_name(x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, u"US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, self.org_name),
            x509.NameAttribute(NameOID.COMMON_NAME, self.client_name),
        ])).sign(self.private_key, hashes.SHA256())
        
        DebugLogger.inspect_pem("APP CSR (To be sent to CA)", csr.public_bytes(serialization.Encoding.PEM))
        return csr

    def install_certificate(self, cert_pem, ca_cert_path):
        self.certificate = x509.load_pem_x509_certificate(cert_pem)
        self.session.verify = ca_cert_path
        print("      [App] Certificate Received & Installed.")

    def register_via_dcr(self, registration_url, initial_access_token):
        headers = {"Authorization": f"Bearer {initial_access_token}"}
        payload = {
            "client_name": self.client_name,
            "redirect_uris": ["https://127.0.0.1/callback"],
            "grant_types": ["client_credentials"],
            "token_endpoint_auth_method": "tls_client_auth",
            "tls_client_auth_subject_dn": self.dn_str
        }
        
        DebugLogger.inspect_request("APP", "POST", registration_url, headers, payload)
        
        r = self.session.post(registration_url, headers=headers, json=payload)
        DebugLogger.inspect_response("APP", r)
        r.raise_for_status()
        self.client_id = r.json()['client_id']
        return self.client_id

    def authenticate(self, token_url):
        cert_path = os.path.join(CERT_DIR, f"{self.client_name}.crt.temp")
        key_path = os.path.join(CERT_DIR, f"{self.client_name}.key.temp")
        
        pem_bytes = self.certificate.public_bytes(serialization.Encoding.PEM)
        with open(cert_path, "wb") as f: f.write(pem_bytes)
        
        with open(key_path, "wb") as f: 
            f.write(self.private_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()))

        DebugLogger.inspect_pem("CLIENT CERTIFICATE (USED FOR AUTH)", pem_bytes)

        data = {"grant_type": "client_credentials", "client_id": self.client_id}
        
        DebugLogger.inspect_request("APP", "POST", token_url, body=data, cert_used=self.dn_str)

        try:
            r = self.session.post(token_url, data=data, cert=(cert_path, key_path))
            DebugLogger.inspect_response("APP", r)
            if r.status_code == 200:
                print("\n" + "="*60)
                print(f"      ✅ DEMO COMPLETED SUCCESSFULLY")
                print("="*60)
            else:
                print(f"      ❌ Auth Failed.")
        finally:
            if os.path.exists(cert_path): os.remove(cert_path)
            if os.path.exists(key_path): os.remove(key_path)

# ==========================================
#  CLASS: MANAGER (The Infrastructure)
# ==========================================
class DemoManager:
    def __init__(self):
        self.session = requests.Session()
        self.session.trust_env = False
        self.ca_key = None
        self.ca_cert = None

    def log(self, step, msg):
        print(f"\n[{step}/9] {msg}")

    def clean_environment(self):
        self.log(1, "Cleaning environment...")
        subprocess.run(["docker", "compose", "-f", COMPOSE_FILE, "down", "-v", "--remove-orphans"], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        if os.path.exists(CERT_DIR): shutil.rmtree(CERT_DIR)
        os.makedirs(CERT_DIR)

    def generate_root_ca(self):
        self.log(2, "Generating Root CA...")
        self.ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        ca_subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, u"Demo Root CA")])
        ski = x509.SubjectKeyIdentifier.from_public_key(self.ca_key.public_key())
        ku = x509.KeyUsage(digital_signature=False, content_commitment=False, key_encipherment=False, data_encipherment=False, key_agreement=False, key_cert_sign=True, crl_sign=True, encipher_only=False, decipher_only=False)
        self.ca_cert = x509.CertificateBuilder().subject_name(ca_subject).issuer_name(ca_subject).public_key(self.ca_key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(datetime.now(timezone.utc)).not_valid_after(datetime.now(timezone.utc) + timedelta(days=1)).add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True).add_extension(ski, critical=False).add_extension(ku, critical=True).sign(self.ca_key, hashes.SHA256())
        with open(os.path.join(CERT_DIR, "ca.crt.pem"), "wb") as f: f.write(self.ca_cert.public_bytes(serialization.Encoding.PEM))
        self.session.verify = os.path.join(CERT_DIR, "ca.crt.pem")

    def generate_server_cert(self):
        self.log(3, "Generating Server Cert (localhost)...")
        srv_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        srv_subject = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, u"localhost")])
        aki = x509.AuthorityKeyIdentifier.from_issuer_public_key(self.ca_key.public_key())
        eku = x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH])
        srv_cert = x509.CertificateBuilder().subject_name(srv_subject).issuer_name(self.ca_cert.subject).public_key(srv_key.public_key()).serial_number(x509.random_serial_number()).not_valid_before(datetime.now(timezone.utc)).not_valid_after(datetime.now(timezone.utc) + timedelta(days=1)).add_extension(x509.SubjectAlternativeName([x509.DNSName(u"localhost"), x509.IPAddress(ipaddress.ip_address("127.0.0.1"))]), critical=False).add_extension(aki, critical=False).add_extension(eku, critical=False).sign(self.ca_key, hashes.SHA256())
        with open(os.path.join(CERT_DIR, "server.key.pem"), "wb") as f: f.write(srv_key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()))
        with open(os.path.join(CERT_DIR, "server.crt.pem"), "wb") as f: f.write(srv_cert.public_bytes(serialization.Encoding.PEM))

    def start_infrastructure(self):
        self.log(4, "Starting Keycloak Infrastructure...")
        with open(COMPOSE_FILE, "w") as f: f.write(DOCKER_COMPOSE_TEMPLATE.format(admin_user=ADMIN_USER, admin_pass=ADMIN_PASS, cert_dir=CERT_DIR, port=KC_PORT))
        subprocess.run(["docker", "compose", "-f", COMPOSE_FILE, "up", "-d"], check=True)
        print("      Waiting for startup (scans logs)...")
        timeout, start = 90, time.time()
        while (time.time() - start) < timeout:
            logs = subprocess.run(["docker", "logs", "mtls_keycloak"], capture_output=True, text=True).stdout
            if "started in" in logs:
                print("      ✓ Keycloak Ready.")
                time.sleep(3)
                return
            time.sleep(2)
        sys.exit(1)

    def get_initial_access_token(self):
        self.log(5, "Admin: Generating Initial Access Token...")
        # 1. Login
        token_url = f"{KC_URL}/realms/master/protocol/openid-connect/token"
        body = {"username": ADMIN_USER, "password": ADMIN_PASS, "grant_type": "password", "client_id": "admin-cli"}
        DebugLogger.inspect_request("ADMIN", "POST", token_url, body=body)
        r = self.session.post(token_url, data=body)
        r.raise_for_status()
        admin_token = r.json()['access_token']
        DebugLogger.inspect_response("ADMIN", r)

        # 2. Get IAT
        iat_url = f"{KC_URL}/admin/realms/{REALM}/clients-initial-access"
        iat_body = {"count": 1, "expiration": 0}
        DebugLogger.inspect_request("ADMIN", "POST", iat_url, headers={"Authorization": f"Bearer {admin_token}"}, body=iat_body)
        r = self.session.post(iat_url, headers={"Authorization": f"Bearer {admin_token}"}, json=iat_body)
        DebugLogger.inspect_response("ADMIN", r)
        return r.json()['token']

    def sign_client_csr(self, csr):
        self.log(7, "CA: Signing App CSR...")
        # Show what the CA received
        DebugLogger.inspect_pem("CA RECEIVED CSR", csr.public_bytes(serialization.Encoding.PEM))
        
        aki = x509.AuthorityKeyIdentifier.from_issuer_public_key(self.ca_key.public_key())
        ski = x509.SubjectKeyIdentifier.from_public_key(csr.public_key())
        eku = x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH])
        
        cert = x509.CertificateBuilder().subject_name(csr.subject).issuer_name(self.ca_cert.subject).public_key(csr.public_key()).serial_number(x509.random_serial_number()).not_valid_before(datetime.now(timezone.utc)).not_valid_after(datetime.now(timezone.utc) + timedelta(days=1)).add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True).add_extension(aki, critical=False).add_extension(ski, critical=False).add_extension(eku, critical=False).sign(self.ca_key, hashes.SHA256())
        
        cert_pem = cert.public_bytes(serialization.Encoding.PEM)
        DebugLogger.inspect_pem("CA ISSUED CERTIFICATE", cert_pem)
        return cert_pem

# ==========================================
#  MAIN CHRONOLOGICAL FLOW
# ==========================================
if __name__ == "__main__":
    manager = DemoManager()
    
    # --- PHASE 1: INFRASTRUCTURE ---
    manager.clean_environment()     # Step 1
    manager.generate_root_ca()      # Step 2
    manager.generate_server_cert()  # Step 3
    manager.start_infrastructure()  # Step 4
    iat = manager.get_initial_access_token() # Step 5

    # --- PHASE 2: APPLICATION SETUP ---
    app = SampleServiceProvider(client_name="my-python-service", org_name="DevOps Inc")
    
    manager.log(6, "App: Generating Identity...")
    app_csr = app.generate_identity_and_csr() # Step 6

    # --- PHASE 3: CERTIFICATE AUTHORITY INTERACTION ---
    signed_cert_pem = manager.sign_client_csr(app_csr) # Step 7
    app.install_certificate(signed_cert_pem, ca_cert_path=os.path.join(CERT_DIR, "ca.crt.pem"))
    
    # --- PHASE 4: OAUTH 2.0 PROTOCOL ---
    manager.log(8, "App: Registering (Dynamic Client Registration)...")
    app.register_via_dcr(f"{KC_URL}/realms/{REALM}/clients-registrations/openid-connect", iat) # Step 8
    
    manager.log(9, "App: Authenticating (mTLS Token Exchange)...")
    app.authenticate(f"{KC_URL}/realms/{REALM}/protocol/openid-connect/token") # Step 9
    
    print("\n[*] Demo Finished. Use 'docker compose down -v' to clean up.")

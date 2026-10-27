# Network Destination & SSRF Egress Policy

**Project:** DERA — Database Engineering & Reverse Analysis  
**Repository:** [https://github.com/krishanth7/dera](https://github.com/krishanth7/dera)  
**Milestone:** Phase 5.6 — Read-Only Enforcement, Timeouts & Safety  
**Auditor:** Principal Application Security Architect & DevSecOps Engineering Team  

---

## 1. Threat Overview & Invariants

Server-Side Request Forgery (SSRF) occurs when an application is coerced into establishing network connections to internal or prohibited destinations on behalf of an attacker. In database inspection tools, SSRF vectors can target:
- **Cloud Metadata Endpoints:** `169.254.169.254` (AWS, GCP, Azure), `169.254.170.2` (AWS ECS task metadata).
- **Loopback Interfaces:** `127.0.0.1`, `::1`, `localhost` targeting internal administrative daemons.
- **Internal Administrative Ports:** Port 22 (SSH), 2375 (Docker), 10250 (Kubernetes Kubelet), 445 (SMB).
- **Private Subnets:** RFC 1918 subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) in shared SaaS deployments.

DERA enforces strict, fail-closed destination policies implemented in [`dera_connectors.security.destinations`](../../packages/connectors/src/dera_connectors/security/destinations.py).

---

## 2. Blocked Network Ranges & Hostnames

The following destinations are rejected unconditionally across all database adapters:

```text
Prohibited Hostnames:
  - localhost
  - metadata.google.internal
  - metadata.google
  - metadata
  - instance-data
  - 169.254.169.254
  - 169.254.170.2

Prohibited CIDRs:
  - 0.0.0.0/8 (Current network)
  - 127.0.0.0/8 (IPv4 Loopback)
  - 169.254.0.0/16 (RFC 3927 Link-local / Cloud Metadata)
  - 192.0.2.0/24 (TEST-NET-1)
  - 198.51.100.0/24 (TEST-NET-2)
  - 203.0.113.0/24 (TEST-NET-3)
  - 224.0.0.0/4 (Multicast)
  - 240.0.0.0/4 (Reserved / Future use)
  - ::1/128 (IPv6 Loopback)
  - ::/128 (IPv6 Unspecified)
  - fe80::/10 (IPv6 Link-local)
  - ff00::/8 (IPv6 Multicast)
```

In multi-tenant cloud environments where `allow_private_networks = False`, RFC 1918 (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) and IPv6 ULA (`fc00::/7`) addresses are also blocked by default.

---

## 3. Restricted Service Ports

Database connections must target legitimate database service ports. Connections to the following administrative or plain-text service ports are blocked:

```text
Prohibited Ports:
  - 21 (FTP)
  - 22 (SSH)
  - 23 (Telnet)
  - 25 (SMTP)
  - 53 (DNS)
  - 110 (POP3)
  - 135, 137, 138, 139 (NetBIOS / RPC)
  - 143 (IMAP)
  - 445 (SMB)
  - 2375, 2376 (Docker daemon)
  - 10250, 10255 (Kubelet API)
```

Target ports must also satisfy `1 <= port <= 65535`.

---

## 4. DNS Rebinding Defense & Destination Pinning

In a DNS rebinding attack, an attacker configures a domain name with a low TTL (time-to-live) that resolves to a benign public IP during pre-flight validation, but shifts to an internal IP (e.g. `169.254.169.254` or `127.0.0.1`) when the database connection is actually opened.

DERA counteracts this via two mechanisms:
1. **Multi-Answer Validation:** [`resolve_and_validate_destination`](../../packages/connectors/src/dera_connectors/security/destinations.py) queries DNS and validates *every* IP address in the DNS response. If any resolved IP is in a forbidden range, the host is rejected.
2. **Destination Pinning:** [`verify_destination_pinning`](../../packages/connectors/src/dera_connectors/security/destinations.py) verifies that the IP address used during socket connection matches the pre-flight validated address list, raising `DNSRebindingViolationError` upon drift.

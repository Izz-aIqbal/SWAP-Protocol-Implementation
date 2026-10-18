# SWAP (Simple Web Access Protocol) Implementation

A custom binary application-layer network protocol designed to serve web resources over TCP with high compactness, predictable parsing, and explicit status signaling.

---

## Executive Summary

The Simple Web Access Protocol (SWAP) is an alternative to verbose text-based protocols like HTTP, optimized for low overhead, precise header semantics, and educational clarity[cite: 6]. This project implements a complete client-server architecture using a fixed 12-byte binary header framing model, explicit network byte order (Big-Endian) serialization, flexible content-type mapping, and persistent TCP connection handling[cite: 6].

---

## Core Technical Specifications

* **Transport Layer:** TCP (reliable, ordered, connection-oriented socket communication)[cite: 6].
* **Default Port:** `8080`[cite: 6].
* **Header Architecture:** Fixed 12-byte binary structure[cite: 6].
* **Payload Structure:** Variable-length byte sequence governed by an explicit 32-bit unsigned length indicator[cite: 6].
* **Connection Lifecycle:** Stateful connection loops supporting persistent multi-request sessions[cite: 6].

---

## Message Types and Protocol Semantics

Message types are encoded as a single byte to immediately dictate processing logic[cite: 6]. Client request types use lower values, while server responses utilize the high-bit set[cite: 6].

| Hex Code | Symbol | Direction | Functional Meaning |
| :--- | :--- | :--- | :--- |
| `0x01` | `SWAP_GET` | Client $\rightarrow$ Server | Request resource path (payload contains target path)[cite: 6]. |
| `0x02` | `SWAP_POST` | Client $\rightarrow$ Server | Submit data for server-side processing[cite: 6]. |
| `0x80` | `SWAP_OK` | Server $\rightarrow$ Client | Success response; payload contains resource or confirmation message[cite: 6]. |
| `0x81` | `SWAP_NOT_FOUND` | Server $\rightarrow$ Client | Error response indicating requested resource does not exist[cite: 6]. |
| `0x82` | `SWAP_BAD_REQUEST` | Server $\rightarrow$ Client | Error response indicating a malformed header or invalid request[cite: 6]. |

---

## Message Header Format (12 Bytes Total)

All multi-byte numeric fields are serialized using **Network Byte Order (Big-Endian)**[cite: 6].

* **Bytes 0–1 (Magic Number):** `0xABCD` (Constant protocol identifier used to quickly validate incoming traffic)[cite: 6].
* **Byte 2 (Version):** `0x01` (Protocol version for backward and forward compatibility)[cite: 6].
* **Byte 3 (Type):** 1-byte message command or status code (`SWAP_GET`, `SWAP_OK`, etc.)[cite: 6].
* **Bytes 4–5 (Content Type):** 2-byte code indicating the payload format[cite: 6].
* **Bytes 6–9 (Payload Length):** Unsigned 32-bit integer (`uint32`) specifying the exact byte count of the following payload[cite: 6].
* **Bytes 10–11 (Options / Status):** 2-byte reserved field utilized for flags (e.g., authentication requirements, compression, or sequence IDs)[cite: 6].

---

## Content Type Codes

The 2-byte Content Type field informs the receiver how to parse or save the incoming payload[cite: 6].

| Hex Code | Code Symbol | Description / File Formats |
| :--- | :--- | :--- |
| `0x0001` | `SWAP_CT_TEXT` | Plain text (`.txt`)[cite: 6] |
| `0x0002` | `SWAP_CT_HTML` | HTML document (`.html`, `.htm`)[cite: 6] |
| `0x0003` | `SWAP_CT_JPEG` | JPEG image (`.jpg`, `.jpeg`)[cite: 6] |
| `0x0004` | `SWAP_CT_PNG` | PNG image (`.png`)[cite: 6] |
| `0x0005` | `SWAP_CT_JSON` | JSON structured data (`.json`)[cite: 6] |
| `0x0006` | `SWAP_CT_BINARY` | Generic binary stream (`.bin`, `.dat`)[cite: 6] |

---

## System Architecture and Processing Flow

### 1. Client-Server Interactions
* **Client Workflow:** Establishes a TCP connection, constructs resource paths (e.g., `/index.html`), packs the 12-byte header, transmits the header followed by the payload, and awaits a structured response[cite: 6].
* **Server Workflow:** Listens on port 8080, accepts connections, reads exactly 12 bytes to unpack and validate headers, reads the precise payload length, evaluates the request type, and loops to handle subsequent requests on the same persistent socket[cite: 6].

### 2. Error Handling and Reliability
* **TCP Integration:** Relies on TCP for ordered delivery and reliable transport-layer retransmissions[cite: 6].
* **Application Validation:** Rejects invalid magic numbers, version mismatches, or payloads exceeding safety limits (e.g., 50 MB max limit) with `SWAP_BAD_REQUEST`[cite: 6].
* **Partial Reads:** Implements strict loop reads (`recv` tracking) to prevent packet fragmentation issues[cite: 6].

---

## Example Packet Structure

**`SWAP_GET` Request for `/index.html`:**
* **Header Fields:** Magic = `0xABCD`, Version = `0x01`, Type = `0x01`, Content Type = `0x0002`, Payload Length = `11` (`0x0000000B`), Options = `0x0000`[cite: 6].
* **Binary Header Hex (Big-Endian):** `AB CD 01 01 00 02 00 00 00 0B 00 00`[cite: 6]
* **Payload ASCII (`/index.html`):** `2F 69 6E 64 65 78 2E 68 74 6D 6C`[cite: 6]

---

## Security Considerations and Future Extensions

* **Transport Security:** Production environments should encapsulate SWAP inside a TLS wrapper (`ssl.wrap_socket`) to encrypt data streams[cite: 6].
* **Path Sanitization:** Servers must restrict lookup directories to prevent traversal exploits (e.g., handling `../` sequences)[cite: 6].
* **Protocol Enhancements:** Future revisions support custom extensions such as chunked transfer coding for large files, directory listing handlers (`SWAP_LIST`), and native compression flags[cite: 6].

---

## Repository Structure

```text
.
├── src/
│   ├── client.py
│   ├── server.py
│   ├── protocol.py
│   └── utils.py
├── tests/
│   └── test_protocol.py
├── resources/
│   └── index.html
├── README.md
└── requirements.txt

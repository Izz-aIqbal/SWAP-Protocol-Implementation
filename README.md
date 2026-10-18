# SWAP (Simple Web Application Protocol) Implementation

A client-server network application implementing a custom application-layer binary protocol (SWAP) over TCP sockets using Python.

---

## Overview

The Simple Web Application Protocol (SWAP) is a lightweight, binary application-layer protocol designed to handle request-response communications over TCP. This repository contains a modular Python implementation featuring binary header serialization/deserialization, structured message types, content-type negotiation, and comprehensive file transfer operations (GET and POST).

---

## Key Features

* **Binary Header Framing:** Uses a fixed-size 12-byte big-endian header structured using Python's `struct` module (`!HBBHIH`).
* **Message Types:** Supports standard client requests (`SWAP_GET`, `SWAP_POST`) and server response status codes (`SWAP_OK`, `SWAP_NOT_FOUND`, `SWAP_BAD_REQUEST`).
* **Content-Type Handling:** Maps numerical content-type codes to standard MIME types (Text, HTML, JPEG, PNG, JSON, Binary).
* **Modular Project Architecture:** Clear separation of concerns across protocol specification, networking utilities, client logic, and server request handling.
* **Automated Testing:** Includes test suites and unit tests for protocol encoding/decoding validation.

---

## Protocol Specification

### Fixed Header Layout (12 Bytes, Big-Endian)

| Field | Size | Type | Description |
|---|---|---|---|
| Magic Number | 2 Bytes | `0xABCD` | Protocol Identifier |
| Version | 1 Byte | `0x01` | Protocol Version |
| Message Type | 1 Byte | `uint8` | Operation / Status Code |
| Content-Type | 2 Bytes | `uint16` | Data Format Identifier |
| Content-Length| 4 Bytes | `uint32` | Payload Size in Bytes |
| Reserved | 2 Bytes | `uint16` | Reserved for Future Use |

### Message Types

* `0x01` — **SWAP_GET:** Client request to retrieve content.
* `0x02` — **SWAP_POST:** Client request to send/upload content.
* `0x80` — **SWAP_OK:** Server response indicating success.
* `0x81` — **SWAP_NOT_FOUND:** Server response indicating resource non-existence.
* `0x82` — **SWAP_BAD_REQUEST:** Server response indicating malformed requests.

### Content-Type Codes

* `0x0001` — Text (`text/plain`)
* `0x0002` — HTML (`text/html`)
* `0x0003` — JPEG (`image/jpeg`)
* `0x0004` — PNG (`image/png`)
* `0x0005` — JSON (`application/json`)
* `0x0006` — Binary (`application/octet-stream`)

---

## Directory Structure

```text
CN_SWAP_IMPLEMENTATION/
├── logs/
├── resources/
│   ├── uploads/
│   ├── index.html
│   ├── sample.txt
│   └── test.json
├── src/
│   ├── client.py
│   ├── protocol.py
│   ├── server.py
│   └── utils.py
├── tests/
│   └── test_protocol.py
├── demo.py
├── requirements.txt
└── README.md

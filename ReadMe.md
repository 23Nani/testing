# Quantum-Resistant LWE Encryption Suite

## Overview

This is a **post-quantum cryptographic web application** that implements **Learning With Errors (LWE)** encryption - a NIST-standardized algorithm designed to secure data against both classical and quantum computer attacks. The application provides an educational and practical implementation of polynomial ring-based LWE encryption with interactive visualizations, performance benchmarking, and multiple security levels.

The core security relies on the mathematical hardness of solving "noisy" linear equations in polynomial rings, rather than traditional approaches like integer factorization (RSA) or discrete logarithms (ECC), which are vulnerable to quantum attacks.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Technology Stack**: Bootstrap 5 with custom CSS, vanilla JavaScript for interactivity, MathJax for mathematical notation rendering

**Page Structure**: Multi-page application with three main sections:
- Main dashboard (`index.html`) - Key generation and encryption/decryption interface
- Educational section (`education.html`) - Mathematical explanations with LaTeX rendering
- Benchmark page (`benchmark.html`) - Performance comparison across security levels

**Design Pattern**: Template inheritance using Jinja2 base template (`base.html`) with consistent navigation and styling. Client-side JavaScript files (`main.js`, `benchmark.js`) handle asynchronous API calls and dynamic UI updates.

**State Management**: Session-based state tracking for generated keys and cryptographic instances, with client-side flags (`keysGenerated`, `ciphertextGenerated`) to manage UI flow.

### Backend Architecture

**Framework**: Flask web application with RESTful API endpoints

**Core Cryptographic Engine** (`lwe_crypto.py`):
- `PolynomialRing` class: Implements modular polynomial arithmetic over R_q = Z_q[x]/(x^n+1)
- `LWECrypto` class: Handles key generation, encryption, and decryption using ring-LWE
- Discrete Gaussian error sampling for cryptographic noise

**Security Levels**: Three predefined parameter sets:
- **Toy** (n=16, q=97): Educational purposes only
- **Medium** (n=256, q=4093): Demonstration security
- **Strong** (n=512, q=12289): NIST-level parameters

**API Endpoints**:
- `/api/generate_keys` - Creates public/private key pairs
- `/api/encrypt` - Encrypts plaintext messages, returns hex-encoded ciphertext for sharing
- `/api/decrypt` - Decrypts ciphertext (from session or pasted hex format)
- `/api/benchmark` - Performance testing across security levels

**Hex Encoding/Decoding**: Ciphertext can be encoded as hex strings (format: `n:q:u_hex:v_hex`) for easy copying and sharing. Users can paste hex-encoded ciphertext to decrypt messages from others.

**Design Rationale**: Separate cryptographic logic from web logic for modularity and testability. Session-based key storage (noted for production replacement with proper key management systems).

### Data Storage Solutions

**Current Implementation**: In-memory session storage using Flask sessions for cryptographic instances and keys

**Storage Structure**:
- Session secret key from environment variable (`SESSION_SECRET`)
- Crypto instances dictionary for managing multiple user sessions
- NumPy arrays serialized via custom JSON encoder for API responses

**Production Considerations**: The codebase explicitly notes that proper key management systems should replace session storage in production environments. This could include:
- Hardware Security Modules (HSMs)
- Key Management Services (KMS)
- Encrypted database storage with key derivation functions

### Authentication and Authorization Mechanisms

**Current State**: No authentication system implemented - this is a demonstration/educational application

**Session Management**: Flask session cookies for maintaining cryptographic state across requests, with configurable secret key

**Security Notes**: The application includes warnings about educational vs. production-ready security levels, indicating awareness of real-world security requirements

### External Dependencies

**Python Libraries**:
- **Flask**: Web framework for routing and request handling
- **NumPy**: High-performance numerical operations for polynomial arithmetic
- **SciPy**: Statistical distributions for error sampling (discrete Gaussian)

**Frontend Libraries**:
- **Bootstrap 5**: UI framework and responsive design
- **Bootstrap Icons**: Icon set for visual elements
- **MathJax 3**: LaTeX mathematical notation rendering
- **Chart.js**: Performance visualization (referenced in benchmark functionality)

**Mathematical Dependencies**:
- Discrete Gaussian distribution sampling for cryptographic noise
- Modular arithmetic operations (mod q)
- Polynomial multiplication in quotient rings

**Rationale for Choices**:
- NumPy selected for efficient array operations critical to polynomial arithmetic performance
- SciPy's statistical functions provide cryptographically sound error distributions
- Flask chosen for simplicity and rapid development of educational tool
- MathJax enables clear presentation of complex mathematical concepts
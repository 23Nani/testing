# Quantum-Resistant LWE Encryption Suite

## Overview

A post-quantum cryptographic web application implementing Learning With Errors (LWE) encryption, a NIST-standardized algorithm designed to resist attacks from both classical and quantum computers. The application provides an educational interface for generating cryptographic keys, encrypting/decrypting messages, and benchmarking performance across different security levels.

The core security mechanism relies on the mathematical hardness of solving "noisy" linear equations in polynomial rings, making it resistant to quantum computing attacks that would break traditional RSA and ECC encryption.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture

**Technology Stack**: Bootstrap 5 for responsive UI components, vanilla JavaScript for client-side logic, MathJax for rendering mathematical LaTeX notation in educational content.

**Design Pattern**: Multi-page application using Jinja2 template inheritance with a base template (`base.html`) providing consistent navigation and styling across three main sections:
- Main dashboard (encryption/decryption interface)
- Educational section (mathematical explanations with LaTeX rendering)
- Performance benchmark page (security level comparisons)

**State Management**: Client-side state flags (`keysGenerated`, `ciphertextGenerated`) control UI flow and enable/disable action buttons. Asynchronous API calls update UI dynamically without page reloads.

**Rationale**: Template-based approach chosen for simplicity and SEO-friendliness over SPA frameworks. Bootstrap provides professional UI without custom CSS overhead. Vanilla JavaScript keeps dependencies minimal for educational clarity.

### Backend Architecture

**Framework**: Flask web application with RESTful JSON API endpoints.

**Core Cryptographic Module** (`lwe_crypto.py`):
- `PolynomialRing` class: Implements modular polynomial arithmetic over the ring R_q = Z_q[x]/(x^n+1)
- `LWECrypto` class: Handles key generation, encryption, and decryption using ring-LWE scheme
- Discrete Gaussian error sampling for cryptographic noise generation

**Security Parameter Sets**: Three predefined configurations balancing security vs. performance:
- **Toy** (n=16, q=97, σ=1.5): Educational demonstrations only, not cryptographically secure
- **Medium** (n=256, q=4093, σ=3.2): Moderate security suitable for demonstrations
- **Strong** (n=512, q=12289, σ=3.2): NIST-level parameters for production-grade security

**Session Management**: Flask sessions store generated keys and crypto instances server-side (noted for replacement with proper key management system in production deployments).

**API Endpoints**:
- `/api/generate_keys` (POST): Generates public/private key pairs based on selected security level
- `/api/encrypt` (POST): Encrypts plaintext messages, returns hex-encoded ciphertext for portability
- `/api/decrypt` (POST): Decrypts ciphertext from session storage or pasted hex format
- `/api/benchmark` (POST): Executes performance tests across all security levels

**Hex Encoding Format**: Ciphertext serialization uses custom format `n:q:u_hex:v_hex` enabling users to copy/paste encrypted messages between different sessions or users. This addresses the real-world use case of sharing encrypted data.

**Design Rationale**: Separation of cryptographic logic (`lwe_crypto.py`) from web application logic (`app.py`) enables independent testing and potential reuse in CLI or library contexts. NumPy arrays used for efficient polynomial arithmetic. Session-based storage chosen for development simplicity with clear documentation that production systems require proper key management infrastructure.

### Data Storage

**Session-Based Storage**: Cryptographic keys and instances stored in Flask server-side sessions using encrypted cookies.

**In-Memory Storage**: Dictionary `crypto_instances` maintains temporary crypto objects during request lifecycle.

**Rationale**: Session storage adequate for educational/demonstration purposes. Production deployment would require:
- Hardware Security Module (HSM) for private key storage
- Database-backed key management system
- Key rotation and lifecycle policies

### Authentication & Authorization

**Current Implementation**: No authentication system - open access for educational purposes.

**Production Considerations**: Real deployment would require:
- User authentication (OAuth2, JWT, or session-based)
- Role-based access control for key management
- Audit logging for cryptographic operations

**Rationale**: Omitted for educational clarity. The architecture separates crypto operations from web logic, making authentication integration straightforward when needed.

## External Dependencies

### Python Libraries
- **Flask**: Web framework for HTTP routing and session management
- **NumPy**: Numerical computing for polynomial arithmetic and array operations
- **SciPy**: Statistical functions for discrete Gaussian error distribution sampling

### Frontend Libraries (CDN-hosted)
- **Bootstrap 5**: UI component framework and responsive grid system
- **Bootstrap Icons**: Icon font for UI elements
- **MathJax 3**: JavaScript library for rendering LaTeX mathematical notation in educational content
- **Chart.js**: Charting library for visualizing benchmark performance comparisons (referenced in benchmark.js)

### Security Considerations
- **No database**: Application is stateless except for session storage
- **No external APIs**: Fully self-contained cryptographic operations
- **No file system dependencies**: All operations in-memory

### Environment Variables
- `SESSION_SECRET`: Flask session encryption key (defaults to insecure development key with production warning)

**Rationale**: Minimal external dependencies reduce attack surface and deployment complexity. CDN-hosted frontend libraries enable offline development fallbacks if needed. Pure Python implementation of LWE crypto avoids compiled extension dependencies that complicate deployment.
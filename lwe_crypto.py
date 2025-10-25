"""
Quantum-Resistant LWE (Learning With Errors) Cryptographic Implementation
Implements polynomial ring-based LWE encryption over R_q = Z_q[x]/(x^n+1)
"""

import numpy as np
from scipy.stats import norm
from typing import Tuple, Dict
import time

# Security parameter presets
SECURITY_PARAMS = {
    'toy': {
        'n': 16,           # Polynomial degree
        'q': 97,           # Modulus (small prime)
        'sigma': 1.5,      # Error distribution standard deviation
        'description': 'Educational only - NOT secure'
    },
    'medium': {
        'n': 256,
        'q': 4093,
        'sigma': 3.2,
        'description': 'Moderate security for demonstrations'
    },
    'strong': {
        'n': 512,
        'q': 12289,
        'sigma': 3.2,
        'description': 'High security - NIST-level parameters'
    }
}


class PolynomialRing:
    """Polynomial ring R_q = Z_q[x]/(x^n+1) with modular arithmetic"""
    
    def __init__(self, n: int, q: int):
        self.n = n
        self.q = q
    
    def add(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """Add two polynomials in the ring"""
        return (a + b) % self.q
    
    def subtract(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """Subtract two polynomials in the ring"""
        return (a - b) % self.q
    
    def multiply(self, a: np.ndarray, b: np.ndarray) -> np.ndarray:
        """Multiply two polynomials in R_q = Z_q[x]/(x^n+1)"""
        # Standard polynomial multiplication
        result = np.zeros(2 * self.n, dtype=np.int64)
        for i in range(self.n):
            for j in range(self.n):
                result[i + j] += a[i] * b[j]
        
        # Reduce modulo (x^n + 1)
        # x^n = -1, so x^(n+k) = -x^k
        reduced = np.zeros(self.n, dtype=np.int64)
        for i in range(self.n):
            reduced[i] = result[i] - result[i + self.n]
        
        return reduced % self.q
    
    def random_polynomial(self) -> np.ndarray:
        """Generate random polynomial with coefficients in Z_q"""
        return np.random.randint(0, self.q, size=self.n, dtype=np.int64)
    
    def small_polynomial(self) -> np.ndarray:
        """Generate small polynomial with coefficients in {-1, 0, 1}"""
        return np.random.randint(-1, 2, size=self.n, dtype=np.int64)


class LWECrypto:
    """LWE Encryption System"""
    
    def __init__(self, security_level: str = 'toy'):
        params = SECURITY_PARAMS[security_level]
        self.n = params['n']
        self.q = params['q']
        self.sigma = params['sigma']
        self.security_level = security_level
        self.ring = PolynomialRing(self.n, self.q)
    
    def sample_error(self) -> np.ndarray:
        """Sample error from discrete Gaussian distribution"""
        # Discrete Gaussian approximation - keep errors small (centered around 0)
        errors = np.round(np.random.normal(0, self.sigma, self.n))
        return errors.astype(np.int64)
    
    def generate_keypair(self) -> Tuple[Dict, Dict]:
        """Generate LWE public/private key pair"""
        start_time = time.time()
        
        # Private key: small polynomial s
        s = self.ring.small_polynomial()
        
        # Public key: (a, b = a*s + e)
        a = self.ring.random_polynomial()
        e = self.sample_error()
        b = self.ring.add(self.ring.multiply(a, s), e)
        
        keygen_time = time.time() - start_time
        
        private_key = {
            's': s,
            'n': self.n,
            'q': self.q
        }
        
        public_key = {
            'a': a,
            'b': b,
            'n': self.n,
            'q': self.q,
            'keygen_time': keygen_time
        }
        
        return public_key, private_key
    
    def encode_message(self, message: str) -> np.ndarray:
        """Encode text message into polynomial coefficients using bit encoding"""
        # Convert message to bytes
        msg_bytes = message.encode('utf-8')
        
        # Encode each bit as 0 or q/2 for noise tolerance
        # Each byte gives us 8 bits, so we can encode len(msg_bytes)*8 bits
        coeffs = np.zeros(self.n, dtype=np.int64)
        half_q = self.q // 2
        
        bit_index = 0
        for byte in msg_bytes:
            if bit_index >= self.n:
                break
            # Extract each bit from the byte (MSB first)
            for bit_pos in range(7, -1, -1):
                if bit_index >= self.n:
                    break
                bit = (byte >> bit_pos) & 1
                # Encode bit as 0 or q/2
                coeffs[bit_index] = bit * half_q
                bit_index += 1
        
        return coeffs
    
    def decode_message(self, polynomial: np.ndarray) -> str:
        """Decode polynomial coefficients back to text message using bit decoding"""
        # Decode bits from coefficients (values near 0 or q/2)
        half_q = self.q // 2
        
        # Collect bits
        bits = []
        for coeff in polynomial:
            # Center the coefficient in [-q/2, q/2)
            c = int(coeff) % self.q
            if c > half_q:
                c -= self.q
            
            # Round to nearest of {0, half_q, -half_q}
            # Compute distances to 0 and to ±half_q
            dist_to_zero = abs(c)
            dist_to_half = min(abs(c - half_q), abs(c + half_q))
            
            # If closer to 0, bit is 0; if closer to ±half_q, bit is 1
            if dist_to_zero < dist_to_half:
                bit = 0
            else:
                bit = 1
            bits.append(bit)
        
        # Convert bits back to bytes
        msg_bytes = []
        for i in range(0, len(bits), 8):
            if i + 8 > len(bits):
                break
            # Reconstruct byte from 8 bits (MSB first)
            byte_val = 0
            for j in range(8):
                byte_val = (byte_val << 1) | bits[i + j]
            
            # Stop at null terminator
            if byte_val == 0 and len(msg_bytes) > 0:
                break
            msg_bytes.append(byte_val)
        
        try:
            return bytes(msg_bytes).decode('utf-8', errors='ignore')
        except Exception:
            return ""
    
    def encrypt(self, message: str, public_key: Dict) -> Tuple[Dict, Dict]:
        """Encrypt message using LWE public key"""
        start_time = time.time()
        
        a = public_key['a']
        b = public_key['b']
        
        # Encode message into coefficients mapped to 0..q-1
        m = self.encode_message(message)
        
        # Generate random polynomials for encryption
        r = self.ring.small_polynomial()  # Random small polynomial
        e1 = self.sample_error()
        e2 = self.sample_error()
        
        # Compute ciphertext: (u, v) = (a*r + e1, b*r + e2 + m*⌊q/2⌋)
        u = self.ring.add(self.ring.multiply(a, r), e1)
        
        # Add the encoded message directly into v (mod q)
        # m already lives in 0..q-1
        br = self.ring.multiply(b, r)
        br_e2 = self.ring.add(br, e2)
        v = self.ring.add(br_e2, m % self.q)
        
        encrypt_time = time.time() - start_time
        
        ciphertext = {
            'u': u,
            'v': v,
            'n': self.n,
            'q': self.q,
            'encrypt_time': encrypt_time
        }
        
        # Return visualization data for educational purposes
        viz_data = {
            'message_poly': m,
            'random_r': r,
            'error_e1': e1,
            'error_e2': e2,
            'u': u,
            'v': v
        }
        
        return ciphertext, viz_data
    
    def decrypt(self, ciphertext: Dict, private_key: Dict) -> str:
        """Decrypt LWE ciphertext using private key"""
        u = ciphertext['u']
        v = ciphertext['v']
        s = private_key['s']
        
        # Compute v - u*s = b*r + e2 + m - (a*s + e)*r - e1*s
        #                  = a*s*r + e*r + e2 + m - a*s*r - e*r - e1*s
        #                  ≈ m + small_noise
        us = self.ring.multiply(u, s)
        m_noisy = self.ring.subtract(v, us)
        
        # Decode the noisy message polynomial back to text
        message = self.decode_message(m_noisy)
        
        return message
    
    def get_params_info(self) -> Dict:
        """Get current security parameters and their meaning"""
        params = SECURITY_PARAMS[self.security_level]
        return {
            'security_level': self.security_level,
            'n': self.n,
            'q': self.q,
            'sigma': self.sigma,
            'description': params['description'],
            'ring_size': f"Z_{self.q}[x]/(x^{self.n}+1)",
            'estimated_security': self._estimate_security_bits()
        }
    
    def _estimate_security_bits(self) -> int:
        """Rough estimate of security level in bits"""
        # Simplified security estimate based on LWE hardness
        # Real security analysis is much more complex
        if self.security_level == 'toy':
            return 0  # Not secure
        elif self.security_level == 'medium':
            return 80  # Approximate
        else:
            return 128  # NIST level 1

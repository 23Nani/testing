"""
Flask Web Application for Quantum-Resistant LWE Encryption Suite
"""

from flask import Flask, render_template, request, jsonify, session
from lwe_crypto import LWECrypto, SECURITY_PARAMS
from typing import Dict
import numpy as np
import json
import time
import os
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')

# Store crypto instances and keys in session
# In production, use proper key management
crypto_instances = {}


def ciphertext_to_hex(ciphertext: Dict) -> str:
    """Convert ciphertext to hex string for easy copying"""
    u_bytes = ciphertext['u'].tobytes() if isinstance(ciphertext['u'], np.ndarray) else np.array(ciphertext['u'], dtype=np.int64).tobytes()
    v_bytes = ciphertext['v'].tobytes() if isinstance(ciphertext['v'], np.ndarray) else np.array(ciphertext['v'], dtype=np.int64).tobytes()
    n = ciphertext['n']
    q = ciphertext['q']
    
    # Format: n:q:u_hex:v_hex
    hex_str = f"{n}:{q}:{u_bytes.hex()}:{v_bytes.hex()}"
    return hex_str


def hex_to_ciphertext(hex_str: str) -> Dict:
    """Convert hex string back to ciphertext"""
    parts = hex_str.strip().split(':')
    if len(parts) != 4:
        raise ValueError('Invalid hex format. Expected format: n:q:u_hex:v_hex')
    
    n = int(parts[0])
    q = int(parts[1])
    u_bytes = bytes.fromhex(parts[2])
    v_bytes = bytes.fromhex(parts[3])
    
    u = np.frombuffer(u_bytes, dtype=np.int64)
    v = np.frombuffer(v_bytes, dtype=np.int64)
    
    return {
        'u': u,
        'v': v,
        'n': n,
        'q': q
    }


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for NumPy types"""
    def default(self, o):
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        return super(NumpyEncoder, self).default(o)


@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html', security_params=SECURITY_PARAMS)


@app.route('/education')
def education():
    """Educational dashboard"""
    return render_template('education.html')


@app.route('/benchmark')
def benchmark():
    """Performance benchmark page"""
    return render_template('benchmark.html')


@app.route('/api/generate_keys', methods=['POST'])
def generate_keys():
    """Generate LWE key pair"""
    try:
        data = request.json or {}
        security_level = data.get('security_level', 'toy')
        
        # Create crypto instance
        crypto = LWECrypto(security_level)
        session_id = str(uuid.uuid4())
        
        # Generate keys
        public_key, private_key = crypto.generate_keypair()
        
        # Store everything server-side
        crypto_instances[session_id] = {
            'crypto': crypto,
            'public_key': {
                'a': public_key['a'].tolist(),
                'b': public_key['b'].tolist(),
                'n': public_key['n'],
                'q': public_key['q'],
                'keygen_time': public_key['keygen_time']
            },
            'private_key': {
                's': private_key['s'].tolist(),
                'n': private_key['n'],
                'q': private_key['q']
            }
        }
        
        # Only store session_id in cookie
        session['session_id'] = session_id
        
        # Get params info
        params_info = crypto.get_params_info()
        
        return jsonify({
            'success': True,
            'params': params_info,
            'keygen_time': public_key['keygen_time'],
            'public_key_preview': {
                'a_sample': public_key['a'][:5].tolist(),
                'b_sample': public_key['b'][:5].tolist()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/encrypt', methods=['POST'])
def encrypt_message():
    """Encrypt a message"""
    try:
        data = request.json or {}
        message = data.get('message', '')
        
        if not message:
            return jsonify({'success': False, 'error': 'Message cannot be empty'}), 400
        
        session_id = session.get('session_id')
        if not session_id or session_id not in crypto_instances:
            return jsonify({'success': False, 'error': 'Please generate keys first'}), 400
        
        # Get crypto instance and keys from server-side storage
        session_data = crypto_instances[session_id]
        crypto = session_data['crypto']
        pk_data = session_data['public_key']
        
        # Reconstruct public key from server-side data
        public_key = {
            'a': np.array(pk_data['a'], dtype=np.int64),
            'b': np.array(pk_data['b'], dtype=np.int64),
            'n': pk_data['n'],
            'q': pk_data['q']
        }
        
        # Encrypt
        ciphertext, viz_data = crypto.encrypt(message, public_key)
        
        # Convert to hex for easy copying
        hex_ciphertext = ciphertext_to_hex(ciphertext)
        
        # Store ciphertext server-side
        crypto_instances[session_id]['ciphertext'] = {
            'u': ciphertext['u'].tolist(),
            'v': ciphertext['v'].tolist(),
            'n': ciphertext['n'],
            'q': ciphertext['q']
        }
        
        return jsonify({
            'success': True,
            'ciphertext': {
                'u_sample': ciphertext['u'][:8].tolist(),
                'v_sample': ciphertext['v'][:8].tolist(),
                'u_size': len(ciphertext['u']),
                'v_size': len(ciphertext['v'])
            },
            'hex_ciphertext': hex_ciphertext,
            'encrypt_time': ciphertext['encrypt_time'],
            'visualization': {
                'message_poly': viz_data['message_poly'][:8].tolist(),
                'errors': {
                    'e1': viz_data['error_e1'][:8].tolist(),
                    'e2': viz_data['error_e2'][:8].tolist()
                },
                'random_r': viz_data['random_r'][:8].tolist()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/decrypt', methods=['POST'])
def decrypt_message():
    """Decrypt a ciphertext"""
    try:
        data = request.json or {}
        hex_input = data.get('hex_ciphertext', '').strip()
        
        session_id = session.get('session_id')
        if not session_id or session_id not in crypto_instances:
            return jsonify({'success': False, 'error': 'Please generate keys first'}), 400
        
        # Get crypto instance and keys from server-side storage
        session_data = crypto_instances[session_id]
        crypto = session_data['crypto']
        sk_data = session_data['private_key']
        
        # Determine ciphertext source: hex input or server-side storage
        if hex_input:
            # Decrypt from pasted hex
            ciphertext = hex_to_ciphertext(hex_input)
        else:
            # Decrypt from server-side storage
            ct_data = session_data.get('ciphertext')
            if not ct_data:
                return jsonify({'success': False, 'error': 'No ciphertext to decrypt. Please encrypt a message first or paste a hex ciphertext.'}), 400
            
            ciphertext = {
                'u': np.array(ct_data['u'], dtype=np.int64),
                'v': np.array(ct_data['v'], dtype=np.int64),
                'n': ct_data['n'],
                'q': ct_data['q']
            }
        
        private_key = {
            's': np.array(sk_data['s'], dtype=np.int64),
            'n': sk_data['n'],
            'q': sk_data['q']
        }
        
        # Decrypt
        start_time = time.time()
        message = crypto.decrypt(ciphertext, private_key)
        decrypt_time = time.time() - start_time
        
        return jsonify({
            'success': True,
            'message': message,
            'decrypt_time': decrypt_time
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/benchmark', methods=['POST'])
def run_benchmark():
    """Run performance benchmarks"""
    try:
        data = request.json or {}
        test_message = data.get('message', 'Quantum-resistant encryption test!')
        
        results = {}
        
        # Benchmark each security level
        for level in ['toy', 'medium', 'strong']:
            crypto = LWECrypto(level)
            
            # Key generation
            start = time.time()
            public_key, private_key = crypto.generate_keypair()
            keygen_time = time.time() - start
            
            # Encryption
            start = time.time()
            ciphertext, _ = crypto.encrypt(test_message, public_key)
            encrypt_time = time.time() - start
            
            # Decryption
            start = time.time()
            decrypted = crypto.decrypt(ciphertext, private_key)
            decrypt_time = time.time() - start
            
            # Calculate ciphertext expansion
            original_size = len(test_message.encode('utf-8'))
            ciphertext_size = len(ciphertext['u']) + len(ciphertext['v'])
            expansion_ratio = ciphertext_size / original_size if original_size > 0 else 0
            
            results[level] = {
                'keygen_time': round(keygen_time * 1000, 3),  # ms
                'encrypt_time': round(encrypt_time * 1000, 3),  # ms
                'decrypt_time': round(decrypt_time * 1000, 3),  # ms
                'total_time': round((keygen_time + encrypt_time + decrypt_time) * 1000, 3),
                'expansion_ratio': round(expansion_ratio, 2),
                'success': decrypted == test_message,
                'n': crypto.n,
                'q': crypto.q
            }
        
        return jsonify({
            'success': True,
            'results': results,
            'message': test_message,
            'message_length': len(test_message)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/api/params_info/<level>')
def get_params_info(level):
    """Get security parameters info"""
    if level not in SECURITY_PARAMS:
        return jsonify({'success': False, 'error': 'Invalid security level'}), 400
    
    crypto = LWECrypto(level)
    info = crypto.get_params_info()
    
    return jsonify({
        'success': True,
        'params': info
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

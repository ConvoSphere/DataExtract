#!/bin/bash

# SSL-Zertifikate für Development/Testing generieren

set -e

echo "🔐 Generating SSL certificates for development..."

# Verzeichnis erstellen
mkdir -p ssl

# Self-signed Zertifikat generieren
openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes \
    -subj "/C=DE/ST=Test/L=Test/O=FileExtractor/OU=Development/CN=localhost"

# Berechtigungen setzen
chmod 600 ssl/key.pem
chmod 644 ssl/cert.pem

echo "✅ SSL certificates generated successfully!"
echo "📁 Certificate: ssl/cert.pem"
echo "🔑 Private key: ssl/key.pem"
echo ""
echo "⚠️  Note: These are self-signed certificates for development only!"
echo "   For production, use certificates from a trusted CA."

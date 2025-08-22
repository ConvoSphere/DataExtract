# Security Implementation Guide

## Übersicht

Dieses Dokument beschreibt die implementierten Sicherheitsmaßnahmen für den File Extractor Microservice.

## 🔒 Implementierte Security Features

### 1. **API Key Management**
- ✅ **Externe Secret-Verwaltung**: API-Keys werden über Umgebungsvariablen geladen
- ✅ **Format**: `API_KEY_<NAME>=<KEY>:<PERMISSIONS>:<RATE_LIMIT>`
- ✅ **Beispiel**: `API_KEY_CLIENT1=abc123def456:read,write:100`
- ✅ **Fallback**: Nur in Development-Modus, wenn keine Keys konfiguriert sind

### 2. **Input Validation**
- ✅ **Datei-Validierung**: Umfassende Validierung aller Uploads
- ✅ **MIME-Type Check**: Erlaubte und gefährliche MIME-Types
- ✅ **Datei-Signatur**: Magic Bytes Validierung
- ✅ **Malware-Scan**: Basic Heuristiken für verdächtige Inhalte
- ✅ **Datei-Integrität**: SHA-256 Hash-Berechnung

### 3. **Rate Limiting**
- ✅ **Redis-basiert**: Skalierbare Rate-Limiting-Implementierung
- ✅ **Per-User**: Individuelle Limits pro API-Key
- ✅ **Configurable**: Anpassbare Limits und Windows
- ✅ **Headers**: Retry-After Header bei Limit-Überschreitung

### 4. **CORS Security**
- ✅ **Restrictive Origins**: Keine wildcard (*) Origins in Produktion
- ✅ **Configurable**: Anpassbare CORS-Einstellungen
- ✅ **Credentials**: Kontrollierte Credential-Behandlung
- ✅ **Methods**: Explizite HTTP-Methoden

### 5. **Security Headers**
- ✅ **Content Security Policy**: Restriktive CSP-Regeln
- ✅ **X-Frame-Options**: DENY für Clickjacking-Schutz
- ✅ **X-Content-Type-Options**: nosniff für MIME-Sniffing-Schutz
- ✅ **X-XSS-Protection**: XSS-Schutz für ältere Browser
- ✅ **Strict-Transport-Security**: HSTS für HTTPS
- ✅ **Referrer Policy**: Kontrollierte Referrer-Weitergabe
- ✅ **Permissions Policy**: Feature-Policy für Browser-Features

### 6. **Input Sanitization**
- ✅ **URL Sanitization**: Entfernung gefährlicher Zeichen
- ✅ **Header Sanitization**: Bereinigung von Request-Headers
- ✅ **String Sanitization**: Allgemeine String-Bereinigung

### 7. **Audit Logging**
- ✅ **Request Logging**: Vollständige Request-Auditierung
- ✅ **Response Logging**: Response-Status und -Größe
- ✅ **Security Events**: Spezielle Logging für Security-Events
- ✅ **Structured Logging**: JSON-basiertes Logging

### 8. **Graceful Shutdown**
- ✅ **Health Status**: Automatische Health-Status-Änderung
- ✅ **Connection Cleanup**: Sauberes Schließen von Verbindungen
- ✅ **Resource Cleanup**: Bereinigung temporärer Dateien
- ✅ **In-flight Requests**: Warten auf abgeschlossene Requests

## 🛡️ Security Scanning

### Automatisierte Security-Checks

```bash
# Vollständiger Security-Scan
./security-scan.sh
```

### Integrierte Tools

1. **Bandit**: Python Code Security Analysis
2. **Safety**: Dependency Vulnerability Scanner
3. **Trivy**: Container Security Scanner
4. **Semgrep**: SAST (Static Application Security Testing)
5. **detect-secrets**: Secret Detection in Code
6. **pip-licenses**: License Compliance

### CI/CD Integration

Security-Scanning ist in die GitHub Actions integriert:

```yaml
- name: Run comprehensive security scan
  run: |
    chmod +x security-scan.sh
    ./security-scan.sh
```

## 🔧 Konfiguration

### Environment Variables

```bash
# API Keys (Format: API_KEY_<NAME>=<KEY>:<PERMISSIONS>:<RATE_LIMIT>)
API_KEY_CLIENT1=abc123def456:read,write:100
API_KEY_CLIENT2=xyz789uvw012:read,write,admin:1000
API_KEY_MONITORING=mon123key456:read:50

# Security Headers
SECURITY_HEADERS_ENABLED=true
CONTENT_SECURITY_POLICY="default-src 'self'"
X_FRAME_OPTIONS=DENY
X_CONTENT_TYPE_OPTIONS=nosniff

# CORS (Produktions-sicher)
CORS_ORIGINS=["https://your-frontend-domain.com"]
CORS_ALLOW_CREDENTIALS=false
CORS_ALLOW_METHODS=["GET", "POST", "PUT", "DELETE", "OPTIONS"]

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=100
RATE_LIMIT_WINDOW=60

# File Validation
FILE_VALIDATION_ENABLED=true
MALWARE_SCAN_ENABLED=true
FILE_SIGNATURE_VALIDATION=true
```

### Production Configuration

Kopiere `.env.production.example` zu `.env.production` und passe die Werte an:

```bash
cp .env.production.example .env.production
# Bearbeite .env.production mit deinen Produktionswerten
```

## 🚨 Security Best Practices

### 1. **API Key Management**
- Verwende starke, zufällige API-Keys
- Rotiere API-Keys regelmäßig
- Verwende unterschiedliche Keys für verschiedene Clients
- Implementiere Key-Revocation-Mechanismen

### 2. **File Upload Security**
- Validiere alle Uploads umfassend
- Scanne auf Malware
- Begrenze Dateigrößen
- Verwende sichere temporäre Verzeichnisse

### 3. **Network Security**
- Verwende HTTPS in Produktion
- Implementiere mTLS für Service-to-Service Kommunikation
- Verwende Network Policies in Kubernetes
- Implementiere Service Mesh Security

### 4. **Monitoring & Alerting**
- Überwache Security-Events
- Implementiere Alerting für verdächtige Aktivitäten
- Logge alle Security-relevanten Events
- Überwache Rate-Limiting-Violations

### 5. **Regular Security Updates**
- Führe regelmäßige Security-Scans durch
- Update Dependencies regelmäßig
- Überwache Security-Advisories
- Implementiere automatische Vulnerability-Scans

## 🔍 Security Monitoring

### Logs überwachen

```bash
# Security-Events überwachen
docker logs file_extractor_api | grep -i "security\|auth\|validation"

# Rate-Limiting-Violations
docker logs file_extractor_api | grep -i "rate limit"

# File-Validation-Fehler
docker logs file_extractor_api | grep -i "validation\|malware\|suspicious"
```

### Metrics überwachen

```promql
# Failed Authentication Attempts
rate(auth_failures_total[5m])

# Rate Limiting Violations
rate(rate_limit_violations_total[5m])

# File Validation Failures
rate(file_validation_failures_total[5m])

# Suspicious Requests
rate(suspicious_requests_total[5m])
```

## 🚨 Incident Response

### Security Incident Checklist

1. **Identifizierung**
   - Logs analysieren
   - Metrics überprüfen
   - Alerts überprüfen

2. **Containment**
   - Betroffene API-Keys deaktivieren
   - Rate-Limiting verschärfen
   - Temporäre Blockierung verdächtiger IPs

3. **Eradication**
   - Root Cause identifizieren
   - Security-Patches anwenden
   - Konfiguration anpassen

4. **Recovery**
   - Services neu starten
   - Monitoring verstärken
   - Post-Incident Review

### Emergency Contacts

```bash
# Security Team kontaktieren
# Incident Response Plan folgen
# Compliance-Team informieren
```

## 📋 Security Checklist

### Pre-Deployment
- [ ] Security-Scan durchgeführt
- [ ] API-Keys konfiguriert
- [ ] CORS-Einstellungen angepasst
- [ ] Rate-Limiting konfiguriert
- [ ] Security Headers aktiviert
- [ ] File-Validation aktiviert

### Post-Deployment
- [ ] Health Checks funktionieren
- [ ] Security Headers sind gesetzt
- [ ] Rate-Limiting funktioniert
- [ ] File-Validation funktioniert
- [ ] Logs werden generiert
- [ ] Monitoring ist aktiv

### Regular Maintenance
- [ ] Dependencies aktualisiert
- [ ] Security-Scans durchgeführt
- [ ] Logs überprüft
- [ ] Metrics analysiert
- [ ] API-Keys rotiert
- [ ] Konfiguration überprüft

## 🔗 Weitere Ressourcen

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CIS Controls](https://www.cisecurity.org/controls/)

## 📞 Support

Bei Security-Fragen oder -Incidents:

1. **Logs prüfen**: Strukturiertes JSON-Logging mit Security-Events
2. **Metrics überwachen**: Security-spezifische Metriken
3. **Alerts konfigurieren**: Automatische Benachrichtigungen
4. **Documentation**: Vollständige API-Dokumentation unter `/docs`
5. **Security Team**: Kontaktiere das Security-Team für kritische Issues

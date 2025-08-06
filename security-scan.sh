#!/bin/bash

# Security Scanning Script für den File Extractor Microservice
# Führt verschiedene Security-Checks durch

set -e

echo "🔒 Starting Security Scan..."

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funktionen
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 1. Dependency Security Scan
log_info "Scanning dependencies for vulnerabilities..."
if command -v safety &> /dev/null; then
    safety check --json --output safety-report.json || {
        log_warn "Safety found vulnerabilities. Check safety-report.json"
    }
else
    log_warn "Safety not installed. Install with: pip install safety"
fi

# 2. Bandit Security Scan
log_info "Running Bandit security scan..."
if command -v bandit &> /dev/null; then
    bandit -r app/ -f json -o bandit-report.json || {
        log_warn "Bandit found security issues. Check bandit-report.json"
    }
else
    log_warn "Bandit not installed. Install with: pip install bandit"
fi

# 3. Container Security Scan
log_info "Scanning Docker image for vulnerabilities..."
if command -v trivy &> /dev/null; then
    # Build image first
    docker build -t file-extractor:security-scan .
    
    # Scan with Trivy
    trivy image --format json --output trivy-report.json file-extractor:security-scan || {
        log_warn "Trivy found vulnerabilities. Check trivy-report.json"
    }
else
    log_warn "Trivy not installed. Install from: https://aquasecurity.github.io/trivy/"
fi

# 4. Secret Detection
log_info "Scanning for secrets in code..."
if command -v detect-secrets &> /dev/null; then
    detect-secrets scan --baseline .secrets.baseline || {
        log_warn "Potential secrets detected. Check .secrets.baseline"
    }
else
    log_warn "detect-secrets not installed. Install with: pip install detect-secrets"
fi

# 5. SAST Scan (Semgrep)
log_info "Running SAST scan with Semgrep..."
if command -v semgrep &> /dev/null; then
    semgrep scan --config auto --json --output semgrep-report.json || {
        log_warn "Semgrep found issues. Check semgrep-report.json"
    }
else
    log_warn "Semgrep not installed. Install with: pip install semgrep"
fi

# 6. License Compliance
log_info "Checking license compliance..."
if command -v pip-licenses &> /dev/null; then
    pip-licenses --format=json --output-file licenses-report.json
    log_info "License report generated: licenses-report.json"
else
    log_warn "pip-licenses not installed. Install with: pip install pip-licenses"
fi

# 7. Code Quality Security Checks
log_info "Running code quality security checks..."

# Check for hardcoded secrets
if grep -r "password\|secret\|key\|token" app/ --exclude-dir=__pycache__ | grep -v "TODO\|FIXME\|XXX" | grep -v "example\|test\|dummy"; then
    log_warn "Potential hardcoded secrets found in code"
fi

# Check for dangerous imports
if grep -r "import os\|import subprocess\|import sys" app/ --include="*.py" | grep -v "from app.core.config import settings"; then
    log_warn "Potentially dangerous imports found"
fi

# Check for eval/exec usage
if grep -r "eval\|exec" app/ --include="*.py"; then
    log_error "DANGEROUS: eval/exec found in code!"
    exit 1
fi

# 8. Configuration Security
log_info "Checking configuration security..."

# Check for debug mode in production
if grep -r "debug.*=.*True" app/ --include="*.py"; then
    log_warn "Debug mode enabled in code"
fi

# Check for permissive CORS
if grep -r "cors_origins.*\*" app/ --include="*.py"; then
    log_warn "Permissive CORS configuration found"
fi

# 9. Generate Security Report
log_info "Generating security report..."

cat > security-report.md << EOF
# Security Scan Report

Generated: $(date)

## Summary
- Dependencies: $(if [ -f safety-report.json ]; then echo "✅ Scanned"; else echo "❌ Not scanned"; fi)
- Code Security: $(if [ -f bandit-report.json ]; then echo "✅ Scanned"; else echo "❌ Not scanned"; fi)
- Container Security: $(if [ -f trivy-report.json ]; then echo "✅ Scanned"; else echo "❌ Not scanned"; fi)
- Secrets: $(if [ -f .secrets.baseline ]; then echo "✅ Scanned"; else echo "❌ Not scanned"; fi)
- SAST: $(if [ -f semgrep-report.json ]; then echo "✅ Scanned"; else echo "❌ Not scanned"; fi)

## Recommendations
1. Review all generated reports
2. Fix high and critical vulnerabilities
3. Update dependencies regularly
4. Implement secret management
5. Use least privilege principle

## Files Generated
- safety-report.json: Dependency vulnerabilities
- bandit-report.json: Code security issues
- trivy-report.json: Container vulnerabilities
- semgrep-report.json: SAST findings
- licenses-report.json: License compliance
- .secrets.baseline: Secret detection baseline
EOF

log_info "Security scan completed!"
log_info "Check security-report.md for summary"
log_info "Review individual reports for detailed findings"

# Exit with error if critical issues found
if [ -f bandit-report.json ] && grep -q '"severity": "HIGH"' bandit-report.json; then
    log_error "Critical security issues found!"
    exit 1
fi

if [ -f trivy-report.json ] && grep -q '"Severity": "CRITICAL"' trivy-report.json; then
    log_error "Critical container vulnerabilities found!"
    exit 1
fi

log_info "✅ Security scan passed!"
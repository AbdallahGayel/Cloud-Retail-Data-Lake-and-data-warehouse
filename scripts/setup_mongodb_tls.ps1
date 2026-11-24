<#
.SYNOPSIS
    Configures self-signed TLS on a local Windows MongoDB 8.x instance so Microsoft Fabric
    On-Premises Data Gateway can connect over TLS (preferTLS).

.DESCRIPTION
    1. Generates a self-signed X.509 certificate for localhost and 127.0.0.1 using OpenSSL.
    2. Installs the certificate into Cert:\LocalMachine\Root (Windows Trusted Root CA).
    3. Backs up mongod.cfg and enables net.tls (mode: preferTLS).
    4. Restarts the MongoDB Windows service.

    Run in an elevated PowerShell (Administrator) session.

.EXAMPLE
    .\scripts\setup_mongodb_tls.ps1
    .\scripts\setup_mongodb_tls.ps1 -MongoBinDir "C:\Program Files\MongoDB\Server\8.3\bin"
#>
[CmdletBinding()]
param(
    [string]$MongoBinDir = "C:\Program Files\MongoDB\Server\8.3\bin",
    [string]$OpenSslPath = "C:\Program Files\Git\usr\bin\openssl.exe",
    [string]$ServiceName = "MongoDB"
)

$ErrorActionPreference = "Stop"

$cfg = Join-Path $MongoBinDir "mongod.cfg"
if (-not (Test-Path $OpenSslPath)) { throw "OpenSSL not found at $OpenSslPath" }
if (-not (Test-Path $cfg))         { throw "mongod.cfg not found at $cfg" }

$cnfPath = Join-Path $env:TEMP "mongo_ssl.cnf"
@"
[req]
distinguished_name = req_distinguished_name
x509_extensions = v3_req
prompt = no

[req_distinguished_name]
CN = localhost

[v3_req]
basicConstraints = CA:TRUE
keyUsage = critical, digitalSignature, keyCertSign, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
IP.1 = 127.0.0.1
"@ | Set-Content $cnfPath -Encoding ascii

$keyPath = Join-Path $MongoBinDir "mongodb.key"
$crtPath = Join-Path $MongoBinDir "mongodb.crt"
$pemPath = Join-Path $MongoBinDir "mongodb.pem"

Write-Host "1) Generating self-signed TLS certificate for localhost & 127.0.0.1..."
& $OpenSslPath req -x509 -nodes -days 825 -newkey rsa:2048 -keyout $keyPath -out $crtPath -config $cnfPath

Get-Content $crtPath, $keyPath | Set-Content $pemPath -Encoding ascii

Write-Host "2) Installing certificate into Windows LocalMachine Trusted Root..."
Import-Certificate -FilePath $crtPath -CertStoreLocation "Cert:\LocalMachine\Root" | Out-Null

Write-Host "3) Updating mongod.cfg with net.tls (mode: preferTLS)..."
Copy-Item $cfg "$cfg.pre_tls.bak" -Force
$raw = Get-Content $cfg -Raw
if ($raw -notmatch 'certificateKeyFile:') {
    $raw = $raw -replace 'bindIp:\s*127\.0\.0\.1', "bindIp: 127.0.0.1`r`n  tls:`r`n    mode: preferTLS`r`n    certificateKeyFile: $pemPath"
    $raw | Set-Content $cfg -Encoding ascii
}

Write-Host "4) Restarting $ServiceName service..."
Restart-Service $ServiceName
Get-Service $ServiceName
Write-Host "DONE! Now test the MongoDB connection in Microsoft Fabric (Server: localhost:27017 or 127.0.0.1:27017)."

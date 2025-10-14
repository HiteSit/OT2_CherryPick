# Caddy Reverse Proxy HTTPS Setup for MCP Server

## Architecture Overview

```
Claude Desktop (Windows) → HTTPS (port 443) → Caddy (WSL2) → HTTP (port 8000) → FastMCP Server (WSL2)
                          encrypted            reverse proxy      local           MCP tools
```

**Why this architecture:**
- **FastMCP server stays simple:** HTTP only on localhost:8000, no SSL certificate management
- **Caddy handles complexity:** HTTPS termination, automatic certificate generation, trust store installation
- **Claude Desktop requirement met:** HTTPS connection with browser-trusted certificate
- **WSL2 networking advantage:** Modern WSL2 allows Windows to access localhost services in WSL2
- **Security:** Bearer token transmitted over encrypted HTTPS, preventing network interception
- **Scalability:** Later can expose to LAN/internet by changing Caddyfile domain

## System Environment

- **OS:** Ubuntu 20.04.6 LTS in WSL2
- **WSL IP Address:** 172.25.191.149 (local network)
- **Python Environment:** pixi-managed local environment
- **MCP Server:** FastMCP-based at src/ot2_cherrypick_mcp/server.py

## Implementation Steps

### Step 1: Install Caddy in WSL2

Caddy will be installed system-wide using the official Debian repository.

```bash
# Install prerequisites
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl

# Add Caddy's official GPG key
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | \
  sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg

# Add Caddy repository to sources
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | \
  sudo tee /etc/apt/sources.list.d/caddy-stable.list

# Update package list and install Caddy
sudo apt update
sudo apt install caddy

# Verify installation
caddy version
```

**Expected output:** `v2.x.x ...` (version 2.6.0+ required for bearer auth features)

**WSL2 Considerations:**
- Ubuntu 20.04 in WSL2 may not have systemd enabled by default
- We'll run Caddy manually with `caddy run` rather than as a systemd service
- If systemd is available, can later configure as a service for auto-start

### Step 2: Create Caddyfile Configuration

**Location:** `/mnt/d/Amadteus_Main/OpenTron/OT2_CherryPick/Caddyfile`

**Content:**
```caddy
{
    # Global options block
    # Enable Caddy's local Certificate Authority for localhost certificates
    local_certs
    
    # Optional: Set custom admin endpoint (default is localhost:2019)
    # admin off  # Uncomment to disable admin API
}

# Site block for localhost
localhost {
    # Use Caddy's internal CA to generate trusted certificate
    # This will be automatically trusted after installing Caddy's root CA
    tls internal
    
    # Reverse proxy configuration
    reverse_proxy localhost:8000 {
        # Optional: Preserve original Host header
        # header_up Host {upstream_hostport}
        
        # Optional: Add custom headers
        # header_up X-Real-IP {remote_host}
        
        # Health check configuration (optional)
        # health_uri /health
        # health_interval 10s
        # health_timeout 5s
    }
    
    # Optional: Logging for debugging
    log {
        output file /tmp/caddy-access.log
        format json
    }
}
```

**Configuration Explanation:**
- `local_certs` directive enables Caddy's internal CA for non-public domains
- `localhost` automatically implies port 443 (HTTPS) with `tls internal`
- `tls internal` generates a certificate signed by Caddy's local CA
- `reverse_proxy localhost:8000` forwards all HTTPS requests to HTTP backend
- Logging is optional but helpful for troubleshooting connections

**Alternative Configuration (for network access):**
```caddy
{
    local_certs
}

# Use WSL IP address instead of localhost for LAN access
172.25.191.149 {
    tls internal
    reverse_proxy localhost:8000
}
```

### Step 3: Install Caddy's Root CA Certificate

Caddy generates its own Certificate Authority (CA) to sign certificates for localhost and internal domains. This CA must be trusted by both Linux (WSL2) and Windows systems.

#### 3a. Linux Trust Store (WSL2)

**Automatic installation (first run):**
```bash
cd /mnt/d/Amadteus_Main/OpenTron/OT2_CherryPick

# First run attempts automatic installation
sudo caddy start --config Caddyfile

# If prompted, enter sudo password to install root CA
```

Caddy will:
1. Generate a unique root CA certificate at `~/.local/share/caddy/pki/authorities/local/root.crt`
2. Attempt to install into system trust store (`/usr/local/share/ca-certificates/`)
3. Run `update-ca-certificates` to update the trust store

**Manual installation (if automatic fails):**
```bash
# Explicitly trust Caddy's root CA
sudo caddy trust

# Verify installation
ls /usr/local/share/ca-certificates/ | grep -i caddy
```

**Verify Linux trust:**
```bash
# Check if Caddy's CA is in trust store
openssl x509 -in ~/.local/share/caddy/pki/authorities/local/root.crt -noout -subject

# Test HTTPS connection from Linux
curl https://localhost
```

#### 3b. Windows Trust Store (for Claude Desktop)

Claude Desktop runs on Windows and needs the certificate in Windows trust store.

**Export Caddy's root certificate:**
```bash
# Copy certificate to Windows-accessible location
cp ~/.local/share/caddy/pki/authorities/local/root.crt \
   /mnt/c/Users/YOUR_USERNAME/Desktop/caddy-root.crt
```

**Import to Windows (GUI method):**
1. Navigate to Desktop and locate `caddy-root.crt`
2. Double-click the certificate file
3. Click "Install Certificate..."
4. Select "Local Machine" (requires admin) → Next
5. Choose "Place all certificates in the following store"
6. Click "Browse" → Select "Trusted Root Certification Authorities"
7. Click "Next" → "Finish"
8. Confirm security warning with "Yes"

**Import to Windows (PowerShell method):**
```powershell
# Run PowerShell as Administrator
Import-Certificate -FilePath "C:\Users\YOUR_USERNAME\Desktop\caddy-root.crt" `
  -CertStoreLocation Cert:\LocalMachine\Root
```

**Verify Windows trust:**
1. Win + R → `certmgr.msc` → Enter
2. Navigate to "Trusted Root Certification Authorities" → "Certificates"
3. Look for "Caddy Local Authority" in the list
4. Double-click to view certificate details

### Step 4: Create Startup Scripts

These scripts automate the process of starting both the MCP server and Caddy proxy.

#### Script 1: `start_mcp_server.sh`

**Purpose:** Start FastMCP server in HTTP mode on localhost:8000

**Location:** `/mnt/d/Amadteus_Main/OpenTron/OT2_CherryPick/start_mcp_server.sh`

```bash
#!/bin/bash
# Start the FastMCP server in HTTP/SSE mode for Caddy reverse proxy

set -e  # Exit on error

cd /mnt/d/Amadteus_Main/OpenTron/OT2_CherryPick

# Configure MCP server for HTTP transport
export MCP_TRANSPORT=sse        # Server-Sent Events (preferred) or "http"
export MCP_HOST=127.0.0.1       # Listen on localhost only (behind Caddy)
export MCP_PORT=8000            # Backend port for Caddy to proxy to
export MCP_BEARER_TOKEN=dev_token_change_me  # TODO: Change in production

echo "=========================================="
echo "Starting OT-2 MCP Server (HTTP Mode)"
echo "=========================================="
echo "Transport: $MCP_TRANSPORT"
echo "Listening: http://$MCP_HOST:$MCP_PORT"
echo "Bearer Token: ${MCP_BEARER_TOKEN:0:10}..."
echo "=========================================="
echo ""

# Start MCP server with pixi environment
pixi run ot2-mcp-server
```

#### Script 2: `start_caddy_proxy.sh`

**Purpose:** Start Caddy reverse proxy with HTTPS on port 443

**Location:** `/mnt/d/Amadteus_Main/OpenTron/OT2_CherryPick/start_caddy_proxy.sh`

```bash
#!/bin/bash
# Start Caddy reverse proxy for HTTPS access to MCP server

set -e  # Exit on error

cd /mnt/d/Amadteus_Main/OpenTron/OT2_CherryPick

echo "=========================================="
echo "Starting Caddy Reverse Proxy"
echo "=========================================="
echo "Frontend: https://localhost (port 443)"
echo "Backend: http://localhost:8000"
echo "Config: $(pwd)/Caddyfile"
echo "=========================================="
echo ""
echo "Note: Requires sudo for port 443 binding"
echo "Press Ctrl+C to stop Caddy"
echo ""

# Start Caddy (requires sudo for port 443)
sudo caddy run --config Caddyfile --adapter caddyfile
```

#### Script 3: `start_all.sh`

**Purpose:** Start both MCP server and Caddy in proper sequence

**Location:** `/mnt/d/Amadteus_Main/OpenTron/OT2_CherryPick/start_all.sh`

```bash
#!/bin/bash
# Start both MCP server and Caddy reverse proxy

set -e  # Exit on error

cd /mnt/d/Amadteus_Main/OpenTron/OT2_CherryPick

echo "=========================================="
echo "Starting MCP Server + Caddy Reverse Proxy"
echo "=========================================="
echo ""

# Start MCP server in background
echo "[1/2] Starting FastMCP server..."
./start_mcp_server.sh &
MCP_PID=$!
echo "      FastMCP server started (PID: $MCP_PID)"
echo ""

# Wait for MCP server to initialize
echo "      Waiting for MCP server to be ready..."
sleep 3

# Check if MCP server is responding
if curl -s -f http://localhost:8000 > /dev/null 2>&1; then
    echo "      ✓ MCP server is responding"
else
    echo "      ⚠ MCP server may not be ready (continuing anyway)"
fi
echo ""

# Start Caddy proxy (runs in foreground)
echo "[2/2] Starting Caddy reverse proxy..."
echo "      Access via: https://localhost"
echo ""
sudo caddy run --config Caddyfile --adapter caddyfile

# Cleanup on exit
trap "echo 'Stopping MCP server...'; kill $MCP_PID 2>/dev/null" EXIT
```

**Make scripts executable:**
```bash
cd /mnt/d/Amadteus_Main/OpenTron/OT2_CherryPick
chmod +x start_mcp_server.sh start_caddy_proxy.sh start_all.sh
```

### Step 5: Testing Procedures

Systematic testing to verify each layer works correctly.

#### Test 1: FastMCP Server (HTTP Mode)

**Purpose:** Verify FastMCP server works in HTTP mode

```bash
# Terminal 1: Start MCP server
cd /mnt/d/Amadteus_Main/OpenTron/OT2_CherryPick
./start_mcp_server.sh

# Terminal 2: Test HTTP endpoint
curl -v http://localhost:8000

# Expected: HTTP 200 response or valid error (depending on MCP protocol)
# Should see FastMCP server logs in Terminal 1
```

#### Test 2: Caddy Reverse Proxy (HTTPS)

**Purpose:** Verify Caddy can proxy to MCP server with HTTPS

```bash
# Terminal 1: Start MCP server
./start_mcp_server.sh

# Terminal 2: Start Caddy
./start_caddy_proxy.sh

# Terminal 3: Test HTTPS endpoint
curl -v https://localhost

# Expected: 
# - HTTPS 200 response
# - Certificate should be trusted (no SSL errors)
# - Caddy logs showing proxied request
# - MCP server logs showing received request
```

**Verify certificate:**
```bash
# Check certificate details
openssl s_client -connect localhost:443 -servername localhost < /dev/null

# Look for:
# - Issuer: Caddy Local Authority
# - Verify return code: 0 (ok)
```

#### Test 3: Claude Desktop Connection

**Purpose:** End-to-end test with actual Claude Desktop client

**Claude Desktop Configuration:**
1. Open Claude Desktop
2. Settings → Developer → Model Context Protocol
3. Click "Add Server" or "Add Remote Connector"
4. Enter configuration:

```json
{
  "name": "OT-2 Cherry Pick (HTTPS)",
  "url": "https://localhost",
  "auth": {
    "type": "bearer",
    "token": "dev_token_change_me"
  }
}
```

5. Save configuration
6. Restart Claude Desktop if needed

**Verification:**
- Claude Desktop should show the connector as "Connected" (green indicator)
- Try using an MCP tool: "List available tools for OT-2 cherry-pick"
- Check Caddy logs for incoming HTTPS requests
- Check MCP server logs for tool invocations

### Step 6: Documentation Updates

#### Create: `docs/caddy_setup.md`

Detailed documentation for future reference and troubleshooting.

**Structure:**
```markdown
# Caddy Reverse Proxy Setup for HTTPS Access

## Overview
- Why HTTPS is required
- Architecture diagram
- Component responsibilities

## Prerequisites
- Caddy installed
- Certificates trusted
- Firewall rules (if needed)

## Installation
- Step-by-step Caddy installation
- Certificate trust setup (Linux + Windows)
- Configuration file explanation

## Usage
- Starting/stopping services
- Testing connections
- Updating bearer tokens

## Troubleshooting
- Certificate trust issues
- Port binding errors
- WSL networking problems
- Caddy logs interpretation

## Security Considerations
- Bearer token management
- Certificate renewal
- Firewall configuration
- Network exposure risks
```

#### Update: `README.md`

Add new section about HTTPS access:

```markdown
## Remote Access via HTTPS (Caddy Reverse Proxy)

For Claude Desktop connectivity, the MCP server can be accessed over HTTPS through a Caddy reverse proxy.

### Quick Start

```bash
# Start both MCP server and Caddy proxy
./start_all.sh
```

### Claude Desktop Configuration

Add this remote connector in Claude Desktop settings:

```json
{
  "name": "OT-2 Cherry Pick",
  "url": "https://localhost",
  "auth": {
    "type": "bearer",
    "token": "dev_token_change_me"
  }
}
```

### Manual Startup

```bash
# Terminal 1: Start MCP server
./start_mcp_server.sh

# Terminal 2: Start Caddy proxy
./start_caddy_proxy.sh
```

### First-Time Setup

See `docs/caddy_setup.md` for:
- Caddy installation instructions
- Certificate trust configuration
- Troubleshooting guide

### Network Access (Optional)

To allow connections from other computers:
1. Update `Caddyfile` to use WSL IP address or hostname
2. Configure Windows firewall to allow port 443
3. Update bearer token to strong secret value

See `docs/caddy_setup.md` for detailed network setup.
```

#### Update: `CLAUDE.md`

Add Caddy integration to MCP Server Architecture section:

```markdown
### Remote Access (Caddy Reverse Proxy)

For HTTPS access required by Claude Desktop, a Caddy reverse proxy is used:

```
Claude Desktop → HTTPS (port 443) → Caddy → HTTP (port 8000) → FastMCP Server
```

**Startup scripts:**
- `start_mcp_server.sh` - Start FastMCP in HTTP mode
- `start_caddy_proxy.sh` - Start Caddy HTTPS proxy
- `start_all.sh` - Start both services together

**Configuration:**
- `Caddyfile` - Caddy reverse proxy configuration
- Uses Caddy's internal CA for trusted localhost certificates
- Bearer token authentication preserved through proxy

**Certificate trust:**
- Caddy generates local CA certificate at `~/.local/share/caddy/pki/authorities/local/root.crt`
- Must be installed in both Linux and Windows trust stores
- See `docs/caddy_setup.md` for installation instructions

**Running with HTTPS:**
```bash
# Start services
./start_all.sh

# Access via Claude Desktop with https://localhost
```
```

### Step 7: Network Access Configuration (Future)

For access from computers beyond the Windows host.

#### Caddyfile Modifications

**Option A: Use WSL IP address**
```caddy
{
    local_certs
}

# Replace localhost with WSL IP
172.25.191.149 {
    tls internal
    reverse_proxy localhost:8000
}
```

**Option B: Use custom hostname**
```caddy
{
    local_certs
}

# Custom hostname (requires DNS or hosts file entry)
ot2-mcp.local {
    tls internal
    reverse_proxy localhost:8000
}
```

**Option C: Public domain with Let's Encrypt**
```caddy
# Automatic HTTPS with Let's Encrypt (requires public domain)
your-domain.com {
    reverse_proxy localhost:8000
}
```

#### Windows Firewall Configuration

Allow inbound HTTPS connections:

```powershell
# PowerShell as Administrator
New-NetFirewallRule -DisplayName "Caddy HTTPS (MCP)" `
  -Direction Inbound `
  -Protocol TCP `
  -LocalPort 443 `
  -Action Allow `
  -Profile Private
```

Or via GUI:
1. Windows Security → Firewall & network protection
2. Advanced settings → Inbound Rules
3. New Rule → Port → TCP 443
4. Allow the connection
5. Apply to Private networks
6. Name: "Caddy HTTPS (MCP)"

#### WSL Port Forwarding (if needed)

Modern WSL2 with mirrored networking shouldn't need this, but for older WSL:

```powershell
# PowerShell as Administrator
# Forward Windows port 443 to WSL port 443
netsh interface portproxy add v4tov4 `
  listenaddress=0.0.0.0 `
  listenport=443 `
  connectaddress=172.25.191.149 `
  connectport=443
```

## Potential Issues & Solutions

### Issue 1: Caddy Can't Bind to Port 443

**Error:** `listen tcp :443: bind: permission denied`

**Cause:** Port 443 requires root privileges

**Solutions:**
1. **Run with sudo (simplest):**
   ```bash
   sudo caddy run --config Caddyfile
   ```

2. **Grant capability (persists across restarts):**
   ```bash
   sudo setcap cap_net_bind_service=+ep $(which caddy)
   caddy run --config Caddyfile  # No sudo needed now
   ```

### Issue 2: Certificate Not Trusted in Windows

**Error:** "NET::ERR_CERT_AUTHORITY_INVALID" in Claude Desktop

**Cause:** Caddy's root CA not in Windows trust store

**Solution:**
1. Export certificate from WSL:
   ```bash
   cp ~/.local/share/caddy/pki/authorities/local/root.crt /mnt/c/Users/YOUR_USERNAME/Desktop/
   ```

2. Import to Windows:
   - Double-click certificate on Desktop
   - Install Certificate → Local Machine → Trusted Root Certification Authorities

3. Restart Claude Desktop

### Issue 3: WSL Localhost Not Accessible from Windows

**Error:** Connection timeout or refused from Windows to `https://localhost`

**Cause:** WSL networking not configured correctly

**Solution:**
1. **Check WSL version:**
   ```bash
   wsl --version
   ```
   Need WSL 2.0.0+ for automatic localhost forwarding

2. **Enable mirrored networking (newer WSL):**
   Create/edit `C:\Users\YOUR_USERNAME\.wslconfig`:
   ```ini
   [wsl2]
   networkingMode=mirrored
   ```

3. **Restart WSL:**
   ```powershell
   wsl --shutdown
   ```

4. **Alternative: Use WSL IP directly:**
   Update Caddyfile to use `172.25.191.149` instead of `localhost`

### Issue 4: FastMCP Doesn't Accept run() Parameters

**Error:** `TypeError: run() got unexpected keyword argument 'transport'`

**Cause:** FastMCP API may differ from assumed parameters

**Solution:**
1. Check FastMCP documentation:
   ```bash
   python -c "from fastmcp import FastMCP; help(FastMCP.run)"
   ```

2. Adjust `server.py` to match actual API:
   ```python
   # Example alternative approaches
   app.run(mode="http", host=host, port=port)
   # or
   app.run_http(host=host, port=port, auth=bearer_token)
   # or
   app.run()  # May read from environment variables
   ```

3. Consult FastMCP documentation at https://gofastmcp.com/

### Issue 5: Bearer Token Not Working

**Error:** Authentication failed / 401 Unauthorized from Claude Desktop

**Possible Causes & Solutions:**

1. **Token mismatch:**
   - Verify `MCP_BEARER_TOKEN` env var matches Claude Desktop config
   - Check for typos, trailing spaces

2. **FastMCP not enforcing auth:**
   - Test with wrong token: `curl -H "Authorization: Bearer wrong_token" https://localhost`
   - Should get 401 Unauthorized (if not, auth isn't enforced)

3. **Caddy not passing Authorization header:**
   - Check Caddy logs for header presence
   - May need explicit header forwarding in Caddyfile

### Issue 6: "Connection Refused" on Port 8000

**Error:** Caddy logs show "dial tcp 127.0.0.1:8000: connect: connection refused"

**Cause:** MCP server not running or crashed

**Solution:**
1. Check if MCP server is running:
   ```bash
   ps aux | grep ot2-mcp-server
   netstat -tuln | grep 8000
   ```

2. Check MCP server logs for errors

3. Test MCP server directly:
   ```bash
   curl http://localhost:8000
   ```

4. Restart MCP server:
   ```bash
   ./start_mcp_server.sh
   ```

## Security Considerations

### Bearer Token Management

**Development:** `dev_token_change_me` is acceptable for localhost testing

**Production/Network Access:**
- Generate strong token: `openssl rand -base64 32`
- Store in environment variable, not in code
- Rotate regularly (e.g., monthly)
- Use different tokens per deployment

**Example production token generation:**
```bash
# Generate strong bearer token
export MCP_BEARER_TOKEN=$(openssl rand -base64 32)
echo "Save this token: $MCP_BEARER_TOKEN"

# Save to .env file (add to .gitignore!)
echo "MCP_BEARER_TOKEN=$MCP_BEARER_TOKEN" >> .env
```

### Certificate Management

**Localhost certificates (Caddy internal CA):**
- Auto-renewed by Caddy
- Valid for 1 year, renewed at 2/3 lifetime
- Root CA private key at `~/.local/share/caddy/pki/authorities/local/root.key`
- Protect this file (contains CA signing key)

**Public domain certificates (Let's Encrypt):**
- Auto-renewed by Caddy every 60 days
- Requires ports 80 and 443 open to internet
- Stores certificates in `~/.local/share/caddy/certificates/`

### Firewall Configuration

**Localhost only (default):**
- No firewall changes needed
- Only accessible from Windows host

**LAN access:**
- Allow TCP 443 inbound on Windows Firewall
- Restrict to "Private" network profile
- Consider IP-based restrictions

**Internet access:**
- Use proper domain with Let's Encrypt certificates
- Implement rate limiting in Caddyfile
- Consider VPN or IP whitelist
- Monitor access logs regularly

### Network Exposure Risks

**Low risk (localhost):**
- Only Windows host can connect
- Bearer token still provides basic authentication

**Medium risk (LAN):**
- Other devices on local network can connect
- Use strong bearer token
- Monitor for unusual access patterns

**High risk (internet):**
- Anyone can attempt connections
- MUST use strong bearer token
- Consider additional authentication (OAuth, mutual TLS)
- Implement rate limiting and abuse prevention
- Monitor logs actively

## Files Summary

After implementation, these files will exist:

1. **Caddyfile** - Caddy reverse proxy configuration
2. **start_mcp_server.sh** - FastMCP server startup script
3. **start_caddy_proxy.sh** - Caddy startup script
4. **start_all.sh** - Combined startup script
5. **docs/caddy_setup.md** - Detailed setup documentation
6. **README.md** (updated) - HTTPS section added
7. **CLAUDE.md** (updated) - Caddy integration documented

## Next Steps After Implementation

1. **Test thoroughly:**
   - Local HTTPS access
   - Claude Desktop integration
   - Bearer token authentication
   - Certificate trust verification

2. **Update bearer token:**
   - Replace `dev_token_change_me` with strong token
   - Store securely (not in git)

3. **Document for team:**
   - Share setup instructions
   - Provide troubleshooting guide
   - Document bearer token rotation process

4. **Monitor in production:**
   - Check Caddy access logs: `/tmp/caddy-access.log`
   - Monitor MCP server logs
   - Watch for authentication failures

5. **Plan for scale (if needed):**
   - Move from localhost to LAN access
   - Consider proper domain + Let's Encrypt
   - Implement monitoring and alerting
   - Set up automated certificate renewal verification

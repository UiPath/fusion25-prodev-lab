# Required software 

## Table of Contents
- [Common Prerequisites](#common-prerequisites)
- [UiPath Cloud Configuration](#uipath-cloud-configuration)
- [Anthropic Configuration](#anthropic-configuration)
- [macOS Prerequisites](#macos-prerequisites)
- [Windows Prerequisites](#windows-prerequisites)

## Common Prerequisites

### Required Software
1. **UV Package Manager**
   - Fast Python package installer and resolver (handles Python installation)
   - Installation options:
     - Using pip (if Python exists): `pip install uv`
     - Using pipx: `pipx install uv`
     - Download from: https://github.com/astral-sh/uv
   - Verify installation: `uv --version`

2. **Git**
   - For version control and cloning the repository
   - Check version: `git --version`

3. **Node.js and npm** (For MCP Server integration)
   - Required for running the MCP remote client
   - Node.js v14.0 or higher required
   - Download from: https://nodejs.org/
   - Check versions: `node --version` and `npm --version`

4. **Cursor** (AI-Powered Code Editor)
   - Modern AI-enhanced code editor
   - Download from: https://cursor.sh/
   - Check version: `cursor --version`

### Optional Software
6. **Claude Desktop App** (Optional but recommended)
   - Download from: https://claude.ai/download
   - Used for testing the agent via MCP Server integration

## UiPath Cloud Configuration

### 1. UiPath Account Setup

1. **Create UiPath Account**:
   - Sign up at: https://staging.uipath.com/

2. **Generate Personal Access Token (PAT)**:
   - In the top right corner, click on the icon to open your user menu
   - Go to Preferences > Personal Access Tokens
   - Click "Generate Token"
   - Name: "Company Agent Token"
   - Expiration: Set appropriate duration
   - Scope: Select "Orchestrator API Access (All)"
   - **Important**: Save the token securely - it won't be shown again

## Anthropic Configuration

If you want to follow along with your own anthropic account, you will need an API Key from your account. Ensure you have sufficient credits or billing set up and monitor the usage. 

## macOS Prerequisites

### System Requirements
- macOS 11 (Big Sur) or later

### macOS-Specific Configuration

- **Terminal Access**: Ensure Terminal has Full Disk Access in System Preferences > Security & Privacy

- **SSL Certificates**: macOS may require additional certificates for HTTPS requests:
  ```bash
  uv pip install --upgrade certifi
  ```

  If the SSL Certificates validation still fails with error `https.ConnectError: [SSL: CERTIFY_VERIFY_FAILED]`, the problem could be caused by a proxy, and trusting the proxy CA might help:
  ``` bash
  # example for mitmproxy
  export SSL_CERT_FILE=~/.mitmproxy/mitmproxy-ca-cert.pem
  ```

## Windows Prerequisites

### System Requirements
- Windows 10 version 1903 or later / Windows 11
- PowerShell 5.1 or later

### Windows-Specific Configuration

- **Execution Policy**: May need to allow script execution:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```
- **Long Path Support**: Enable for deep directory structures:
  ```powershell
  New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
  ```

### Python Dependencies
The project uses UV for dependency management. Core dependencies include:
- `uipath-langchain>=0.0.106` - UiPath integration for LangChain
- `langchain-anthropic>=0.3.8` - Anthropic Claude integration
- `langchain-openai` - OpenAI GPT integration
- `ipykernel` - Jupyter notebook support
- `jupyter` - Jupyter notebook environment
- `pexpect` - Process spawning for authentication

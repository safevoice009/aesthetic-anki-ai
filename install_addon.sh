#!/usr/bin/env bash
set -e

# Identify paths
ADDON_NAME="aesthetic_anki_ai"
WORKSPACE_ADDON_DIR="/media/sucharithpop/01DCEAE1E7161EC0/dev/tresd/apps/aesthetic-anki-ai"
ANKI_ADDONS_DIR="/home/sucharithpop/.var/app/net.ankiweb.Anki/data/Anki2/addons21"
TARGET_LINK="${ANKI_ADDONS_DIR}/${ADDON_NAME}"

echo "========================================="
echo "   Aesthetic Anki AI Installer"
echo "========================================="

# Ensure target addons directory exists
if [ ! -d "${ANKI_ADDONS_DIR}" ]; then
    echo "Creating Flatpak Anki add-ons folder..."
    mkdir -p "${ANKI_ADDONS_DIR}"
fi

# Remove existing link/directory if present
if [ -e "${TARGET_LINK}" ] || [ -L "${TARGET_LINK}" ]; then
    echo "Removing existing add-on link or directory at target..."
    rm -rf "${TARGET_LINK}"
fi

# Create symlink
echo "Creating symlink..."
ln -s "${WORKSPACE_ADDON_DIR}" "${TARGET_LINK}"

echo "SUCCESS: Add-on successfully symlinked!"
echo "Target: ${TARGET_LINK} -> ${WORKSPACE_ADDON_DIR}"
echo "========================================="
echo "Please restart Anki if it is currently running."

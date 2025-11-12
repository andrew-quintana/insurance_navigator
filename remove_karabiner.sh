#!/bin/bash
# Complete Karabiner Removal Script
# This script removes all instances of Karabiner from your Mac
# Some commands require sudo/admin privileges

set -e

echo "=== Karabiner Removal Script ==="
echo ""
echo "This script will:"
echo "1. Stop all Karabiner processes"
echo "2. Remove applications from /Applications"
echo "3. Remove system extensions"
echo "4. Remove application support files"
echo "5. Remove configuration and preference files"
echo ""
read -p "Press Enter to continue or Ctrl+C to cancel..."

# Step 1: Stop Karabiner processes (user-level)
echo ""
echo "Step 1: Stopping Karabiner processes..."
pkill -f "Karabiner-Menu" || true
pkill -f "Karabiner-NotificationWindow" || true
pkill -f "karabiner_console_user_server" || true
pkill -f "Karabiner-Elements" || true
pkill -f "Karabiner-EventViewer" || true
echo "User processes stopped (some root processes may still be running)"

# Step 2: Remove applications (requires sudo)
echo ""
echo "Step 2: Removing applications (requires admin password)..."
sudo rm -rf "/Applications/Karabiner-Elements.app"
sudo rm -rf "/Applications/Karabiner-EventViewer.app"
sudo rm -rf "/Applications/.Karabiner-VirtualHIDDevice-Manager.app"
echo "Applications removed"

# Step 3: Remove system extensions (requires sudo)
echo ""
echo "Step 3: Removing system extensions (requires admin password)..."
# First, unload the system extension if possible
sudo systemextensionsctl uninstall org.pqrs.Karabiner-DriverKit-VirtualHIDDevice 2>/dev/null || true
# Remove the extension files
sudo rm -rf "/Library/SystemExtensions/D3B48CB3-066F-4AE2-BE6A-B3EC0B162967/org.pqrs.Karabiner-DriverKit-VirtualHIDDevice.dext"
sudo rm -rf "/Library/SystemExtensions/D3B48CB3-066F-4AE2-BE6A-B3EC0B162967"
echo "System extensions removed"

# Step 4: Remove application support files (requires sudo)
echo ""
echo "Step 4: Removing application support files (requires admin password)..."
sudo rm -rf "/Library/Application Support/org.pqrs/Karabiner-Elements"
sudo rm -rf "/Library/Application Support/org.pqrs/Karabiner-DriverKit-VirtualHIDDevice"
# Check if org.pqrs directory is empty and remove it
if [ -d "/Library/Application Support/org.pqrs" ]; then
    if [ -z "$(ls -A '/Library/Application Support/org.pqrs')" ]; then
        sudo rmdir "/Library/Application Support/org.pqrs"
    fi
fi
echo "Application support files removed"

# Step 5: Remove user preference files (already done, but included for completeness)
echo ""
echo "Step 5: Removing user preference files..."
rm -f ~/Library/Preferences/org.pqrs.Karabiner-Elements.Settings.plist
rm -f ~/Library/Preferences/org.pqrs.Karabiner-Updater.plist
rm -rf ~/Library/WebKit/org.pqrs.Karabiner-Updater
echo "Preference files removed"

# Step 6: Remove any cached files
echo ""
echo "Step 6: Removing cached files..."
rm -rf ~/Library/Caches/org.pqrs.Karabiner-Elements 2>/dev/null || true
rm -rf ~/Library/Caches/org.pqrs.Karabiner-Updater 2>/dev/null || true
echo "Cache files removed"

# Step 7: Remove any saved application state
echo ""
echo "Step 7: Removing saved application state..."
rm -rf ~/Library/Saved\ Application\ State/org.pqrs.Karabiner-Elements.savedState 2>/dev/null || true
rm -rf ~/Library/Saved\ Application\ State/org.pqrs.Karabiner-EventViewer.savedState 2>/dev/null || true
echo "Saved state removed"

# Step 8: Check for and remove any launch agents/daemons
echo ""
echo "Step 8: Checking for launch agents/daemons..."
rm -f ~/Library/LaunchAgents/org.pqrs.karabiner.* 2>/dev/null || true
sudo rm -f /Library/LaunchAgents/org.pqrs.karabiner.* 2>/dev/null || true
sudo rm -f /Library/LaunchDaemons/org.pqrs.karabiner.* 2>/dev/null || true
echo "Launch agents/daemons removed"

# Final verification
echo ""
echo "=== Removal Complete ==="
echo ""
echo "Verifying removal..."
echo ""
echo "Checking for remaining applications:"
ls -la /Applications/ | grep -i karabiner || echo "✓ No applications found"
echo ""
echo "Checking for remaining processes:"
ps aux | grep -i karabiner | grep -v grep || echo "✓ No processes found"
echo ""
echo "Checking for remaining files:"
find ~/Library -iname "*karabiner*" 2>/dev/null | head -5 || echo "✓ No user files found"
echo ""
echo "=== IMPORTANT NOTES ==="
echo "1. You may need to restart your Mac to fully remove system extensions"
echo "2. If you see any remaining processes, restart your Mac"
echo "3. Check System Settings > Privacy & Security > System Extensions to verify removal"
echo ""
echo "Removal script completed!"



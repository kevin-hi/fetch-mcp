#!/bin/bash
# Install web-fetch skill and hooks to ensure Claude uses mcp__fetch__fetch

set -e

echo "Installing web-fetch skill and hooks..."

# Create directories
mkdir -p ~/.claude/skills/web-fetch
mkdir -p ~/.claude/hooks

# Copy skill
cp skill/SKILL.md ~/.claude/skills/web-fetch/
echo "✓ Installed skill to ~/.claude/skills/web-fetch/SKILL.md"

# Copy hooks (optional)
if [ -f ~/.claude/hooks/hooks.json ]; then
    echo "⚠️  hooks.json already exists. Merge manually or backup first."
    echo "   New hooks are in: hooks/hooks.json"
else
    cp hooks/hooks.json ~/.claude/hooks/
    echo "✓ Installed hooks to ~/.claude/hooks/hooks.json"
fi

echo ""
echo "✓ Installation complete!"
echo ""
echo "Next steps:"
echo "  1. Restart Claude Code (if running)"
echo "  2. Test with: 'Fetch https://camelcamelcamel.com/product/B0FHMY11JH'"
echo ""
echo "Claude will now automatically use mcp__fetch__fetch for web requests."

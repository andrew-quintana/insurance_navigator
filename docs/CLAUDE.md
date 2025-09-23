# Claude Code Rules

## Date and Time Documentation
When documenting dates or times in any file, always use CLI commands to get the current date and time instead of hardcoding them.

### Commands to use:
- `date` - Get current date and time
- `date +"%Y-%m-%d"` - Get date in YYYY-MM-DD format
- `date +"%Y-%m-%d %H:%M:%S"` - Get full timestamp
- `date +"%Y-%m-%d %H:%M:%S %Z"` - Get timestamp with timezone

### Examples:
```bash
# Instead of writing "Created on 2025-09-21"
echo "Created on $(date +"%Y-%m-%d")"

# Instead of writing "Last updated: 2025-09-21 10:30:00"
echo "Last updated: $(date +"%Y-%m-%d %H:%M:%S")"
```

This ensures timestamps are always accurate and current when documentation is generated.
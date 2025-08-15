# Documentation Serial Number System

This directory contains templates for generating PRD, RFC, and TODO documents using an **agnostic serial number system** that automatically determines the next available document number.

## How It Works

### 1. Serial Number Determination

The system automatically determines the next available serial number by:

1. **Explicit Specification**: If you specify a serial number in the prompt, it will be used
2. **Auto-Detection**: If no serial is specified, the system scans existing files to find the next available number
3. **Default**: If no existing files are found, it starts with 001

### 2. File Naming Convention

Documents follow this pattern:
- `PRD{serial}.md` - Product Requirements Document
- `RFC{serial}.md` - Request for Comments (Technical Design)
- `TODO{serial}.md` - Implementation Task List

Where `{serial}` is a three-digit number (001, 002, 003, etc.)

### 3. Phase Documentation

For TODO documents with phases, phase-specific files follow this pattern:
- `@TODO{serial}_phase1_notes.md`
- `@TODO{serial}_phase1_decisions.md`
- `@TODO{serial}_phase1_handoff.md`

## Usage Examples

### Example 1: Auto-Detection (Recommended)

```
**DOCUMENT SERIAL NUMBER:**
- Serial number to use: [Leave blank for auto-detection]
```

The system will:
1. Scan `docs/initiatives/**/` for existing files
2. Find the highest existing serial number
3. Use the next available number

### Example 2: Explicit Specification

```
**DOCUMENT SERIAL NUMBER:**
- Serial number to use: 005
```

The system will use 005 regardless of existing files.

### Example 3: Sequential Generation

When generating all three documents for a project:

1. **PRD005.md** - First, generate the Product Requirements Document
2. **RFC005.md** - Then, generate the Technical Design using PRD005.md as context
3. **TODO005.md** - Finally, generate the Implementation Tasks using both PRD005.md and RFC005.md

## Benefits

- **No Manual Numbering**: Automatically finds the next available serial
- **Parallel Development**: Multiple teams can work on different serials simultaneously
- **Version Control**: Clear progression and iteration tracking
- **Reference Stability**: Links between documents remain valid
- **Flexibility**: Can override auto-detection when needed

## File Structure

```
docs/initiatives/
├── 0templates/                    # Template files
│   ├── PRD_generation_prompt.md
│   ├── RFC_generation_prompt.md
│   ├── TODO_generation_prompt.md
│   └── README_serial_number_system.md
├── project-a/                     # Example project
│   ├── PRD001.md
│   ├── RFC001.md
│   └── TODO001.md
├── project-b/                     # Another project
│   ├── PRD002.md
│   ├── RFC002.md
│   └── TODO002.md
└── project-c/                     # Third project
    ├── PRD003.md
    ├── RFC003.md
    └── TODO003.md
```

## Best Practices

1. **Use Auto-Detection**: Let the system find the next available number automatically
2. **Consistent Naming**: Always use the same serial number across all three document types for a project
3. **Phase Documentation**: Save phase-specific files with the same serial number for easy reference
4. **Directory Organization**: Keep related documents in the same project directory
5. **Clear References**: When referencing documents, always include the serial number

## Troubleshooting

### Issue: Serial Number Conflicts
- **Cause**: Multiple documents with the same serial number
- **Solution**: Use explicit serial numbers or reorganize existing files

### Issue: Broken References
- **Cause**: Documents referencing non-existent serial numbers
- **Solution**: Ensure all referenced documents exist before generating dependent documents

### Issue: Auto-Detection Not Working
- **Cause**: File pattern mismatch or permission issues
- **Solution**: Check file naming conventions and directory permissions

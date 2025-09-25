# Virtual Environment Quick Reference

## 🚀 Quick Commands

```bash
# Check current status
./scripts/manage-venv.sh status

# Activate current project's venv
source .venv/bin/activate

# Deactivate
deactivate

# Install dependencies
./scripts/manage-venv.sh install

# Create new venv for current project
./scripts/manage-venv.sh create
```

## 📁 Project Structure

```
project/
├── .venv/              # Virtual environment (gitignored)
├── requirements.txt    # Production dependencies
├── requirements-dev.txt # Dev dependencies
└── activate_venv.sh    # Auto-generated activation script
```

## ✅ Best Practices

- ✅ Always use virtual environments
- ✅ Never install packages globally
- ✅ Keep `.venv` in project root
- ✅ Activate before working
- ✅ Use separate requirements files

## 🔧 Troubleshooting

```bash
# Check if venv is active
echo $VIRTUAL_ENV

# List all venvs
./scripts/manage-venv.sh list

# Recreate venv
rm -rf .venv
./scripts/manage-venv.sh create
```

## 📚 Full Documentation

See: `docs/development/VIRTUAL_ENVIRONMENT_BEST_PRACTICES.md`

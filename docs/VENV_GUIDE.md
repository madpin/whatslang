# Virtual Environment Best Practices

This project now enforces the use of virtual environments to ensure clean, isolated dependency management.

## 🎯 Quick Start Workflow

### For New Users

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/whatslang.git
cd whatslang

# 2. Create virtual environment
make venv

# 3. Activate it
source .venv/bin/activate    # Linux/Mac
# or
.venv\Scripts\activate       # Windows

# 4. Install dependencies
make install                 # or: make install-dev

# 5. Setup environment
make setup-env               # Creates .env from template
# Edit .env with your credentials

# 6. Run the service
python run.py
```

## 🔍 What Changed?

### Makefile Enhancements

The `make install` and `make install-dev` commands now:

1. ✅ **Check for active virtual environment** before installing
2. ✅ **Provide clear error messages** if no venv is detected
3. ✅ **Guide users** on how to create and activate venv
4. ✅ **Upgrade pip** before installing dependencies
5. ✅ **Confirm successful installation**

### New `make venv` Command

Creates a virtual environment automatically:

```bash
make venv
```

This will:
- Create `.venv` directory
- Show activation instructions
- Prevent overwriting existing venv

## 🚫 What Happens Without Virtual Environment?

If you try to run `make install` without an active virtual environment:

```bash
$ make install

❌ ERROR: No virtual environment detected!

Please create and activate a virtual environment first:

  python -m venv .venv
  source .venv/bin/activate    # On Linux/Mac
  # or
  .venv\Scripts\activate      # On Windows

Then run 'make install' or 'make install-dev' again.

make: *** [check-venv] Error 1
```

## ✅ Why Use Virtual Environments?

### Benefits

1. **Isolation** - Dependencies don't conflict with other projects
2. **Reproducibility** - Consistent environment across machines
3. **Safety** - Won't pollute global Python installation
4. **Version Control** - Different projects can use different package versions
5. **Clean Removal** - Just delete `.venv` folder to start fresh

### Example Scenario

Without venv:
```bash
# Project A needs Django 4.0
pip install django==4.0

# Project B needs Django 3.2 (conflicts!)
pip install django==3.2  # ❌ Overwrites previous version
```

With venv:
```bash
# Project A
cd project-a
source .venv/bin/activate
pip install django==4.0   # ✅ Isolated

# Project B
cd project-b
source .venv/bin/activate
pip install django==3.2   # ✅ Isolated, no conflict
```

## 📋 Common Commands

### Creating Virtual Environment

```bash
# Option 1: Using Makefile (recommended)
make venv

# Option 2: Manually
python3 -m venv .venv
```

### Activating Virtual Environment

```bash
# Linux/Mac
source .venv/bin/activate

# Windows (Command Prompt)
.venv\Scripts\activate.bat

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### Installing Dependencies

```bash
# After activating venv:

# Production dependencies
make install

# Development dependencies (includes testing tools)
make install-dev

# Or manually
pip install -r requirements.txt
```

### Deactivating Virtual Environment

```bash
deactivate
```

### Checking if Virtual Environment is Active

```bash
# Should show path to .venv
echo $VIRTUAL_ENV    # Linux/Mac
echo %VIRTUAL_ENV%   # Windows

# Or check Python location
which python         # Linux/Mac - should show .venv/bin/python
where python         # Windows - should show .venv\Scripts\python.exe
```

## 🔧 Troubleshooting

### "make venv" says virtual environment already exists

Solution:
```bash
# Remove existing venv
rm -rf .venv

# Create fresh one
make venv
```

### Virtual environment activation doesn't work on Windows PowerShell

Error: `cannot be loaded because running scripts is disabled`

Solution:
```powershell
# Run PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then try again
.venv\Scripts\Activate.ps1
```

### Forgot to activate virtual environment

If you see the error from `make install`, just:
```bash
source .venv/bin/activate
make install
```

### Want to use a different Python version

```bash
# Specify Python version
python3.11 -m venv .venv

# Or
/usr/bin/python3.12 -m venv .venv
```

## 🎓 Best Practices

### DO ✅

- Create venv before installing dependencies
- Activate venv before working on the project
- Use `make install` instead of `pip install` directly
- Keep venv in `.venv` folder (already in .gitignore)
- Document required Python version in README

### DON'T ❌

- Don't commit `.venv` folder to Git (already gitignored)
- Don't install packages globally for project work
- Don't share virtual environment across projects
- Don't forget to activate venv before running commands

## 📚 Additional Resources

- [Python venv documentation](https://docs.python.org/3/library/venv.html)
- [Real Python: Virtual Environments Guide](https://realpython.com/python-virtual-environments-a-primer/)
- [pip documentation](https://pip.pypa.io/en/stable/)

## 🔄 Updating Dependencies

When dependencies change:

```bash
# Activate venv
source .venv/bin/activate

# Pull latest changes
git pull

# Update dependencies
make install

# Or manually
pip install -r requirements.txt --upgrade
```

## 🗑️ Starting Fresh

To completely reset your virtual environment:

```bash
# Deactivate if active
deactivate

# Remove virtual environment
rm -rf .venv

# Create new one
make venv
source .venv/bin/activate

# Install dependencies
make install
```

---

**Remember:** Always activate your virtual environment before working on the project! 🔐


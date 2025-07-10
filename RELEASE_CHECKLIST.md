# Release Checklist for Blood on the Clocktower AI

## Pre-Release Checks (MANDATORY - DO NOT SKIP)

### 1. Code Quality Checks
- [ ] **Black formatting**: `black --check src/`
- [ ] **isort import sorting**: `isort --profile black --check-only src/`
- [ ] **flake8 linting**: `flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics`
- [ ] **Basic syntax check**: `python -m py_compile src/**/*.py`

### 2. Dependency Management
- [ ] **Check new imports**: Verify all new imports are in requirements.txt or build_windows.py hiddenimports
- [ ] **Test import safety**: Run `python -c "from src.speech.audio_dependencies import *"` 
- [ ] **Verify optional dependencies**: Ensure graceful fallbacks for missing packages

### 3. Local Testing
- [ ] **Unit tests pass**: `pytest tests/ -v`
- [ ] **Import tests**: `python tests/test_basic_imports.py`
- [ ] **Main module runs**: `python -m src.gui.main_window` (should start without errors)

### 4. Build Configuration
- [ ] **PyInstaller dependencies updated**: Check build_windows.py hiddenimports for new modules
- [ ] **Requirements.txt updated**: All new dependencies listed with versions
- [ ] **CI dependencies aligned**: .github/workflows/ci.yml has correct package lists

### 5. Git Hygiene
- [ ] **All changes committed**: `git status` shows clean working tree
- [ ] **Meaningful commit message**: Describes what changed and why
- [ ] **Version tag meaningful**: Follows semantic versioning

## Release Process

### Step 1: Run All Pre-Release Checks
```bash
# Format and check code
black src/
isort --profile black src/
flake8 src/ --count --select=E9,F63,F7,F82 --show-source --statistics

# Test imports and basic functionality
pytest tests/ -v
python -c "from src.speech.audio_dependencies import check_continuous_listening_support; print('✓ Audio deps OK')"
python -c "from src.gui.main_window import main; print('✓ Main window OK')"
```

### Step 2: Commit and Push
```bash
git add -A
git commit -m "Descriptive commit message"
git push origin main
```

### Step 3: Wait and Verify CI Tests Pass
- [ ] **Check GitHub Actions**: All tests pass on both Python 3.11 and 3.12
- [ ] **No skipped jobs**: build-windows and release jobs should run
- [ ] **Fix any failures**: Do NOT create release tag until CI is green

### Step 4: Create Release Tag
```bash
git tag vX.Y.Z -m "Release description"
git push origin vX.Y.Z
```

### Step 5: Monitor Release Build
- [ ] **Windows build succeeds**: Check build-windows job completes
- [ ] **Release created**: Check GitHub releases page
- [ ] **Assets uploaded**: Windows executable should be attached
- [ ] **Test download**: Verify the .zip file downloads and extracts

## Post-Release Verification

### Step 6: Quality Assurance
- [ ] **Download and test**: Actually download and run the Windows executable
- [ ] **Check file size**: Executable should be reasonable size (not 0 bytes, not 500MB+)
- [ ] **Verify functionality**: Test key features work in built version
- [ ] **Update README**: If major features added, update documentation

## Common Issues and Solutions

### Black Formatting Errors
**Problem**: Black formatting fails in CI
**Solution**: Always run `black src/` locally before committing
**Prevention**: Add to pre-commit hooks

### Import Errors
**Problem**: New modules not found in CI or Windows build
**Solution**: Add to hiddenimports in build_windows.py AND requirements.txt
**Prevention**: Test imports in fresh environment

### Dependency Conflicts
**Problem**: CI fails due to heavy dependencies (torch, librosa, etc.)
**Solution**: Keep CI dependencies light, full deps only for Windows build
**Prevention**: Use optional imports with try/except

### Release Job Fails
**Problem**: Release job fails but tests pass
**Solution**: Check permissions, artifact availability, and gh CLI usage
**Prevention**: Test release process with pre-release tags

### Windows Build Timeouts
**Problem**: PyInstaller times out or crashes
**Solution**: Reduce dependencies, exclude problematic packages
**Prevention**: Monitor build times and optimize regularly

## Emergency Procedures

### If Release is Broken
1. **Stop**: Do not create more tags until fixed
2. **Identify**: Check specific error in GitHub Actions logs
3. **Fix**: Apply minimal fix to resolve issue
4. **Test**: Run full checklist again
5. **Re-release**: Create new patch version (vX.Y.Z+1)

### If CI is Red
1. **Do not release**: Never tag when CI is failing
2. **Check logs**: GitHub Actions → Failed job → View logs
3. **Fix locally**: Reproduce and fix the exact error
4. **Verify**: Run same commands locally that failed in CI
5. **Push fix**: Only push when local tests pass

## Automation Ideas (Future)
- [ ] Pre-commit hooks for black/isort/flake8
- [ ] Automated dependency scanning
- [ ] Release candidate builds for testing
- [ ] Automated smoke tests on built executable

---

**Remember**: It's better to spend 10 minutes on this checklist than 2 hours debugging CI failures!

Last Updated: 2025-07-10
Next Review: When we encounter new failure patterns
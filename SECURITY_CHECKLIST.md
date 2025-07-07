# 🔐 Security Checklist for GitHub Push

## ✅ Pre-Push Verification

Before pushing to GitHub, run these commands to ensure no sensitive data is exposed:

### 1. Check for Environment Files
```bash
find . -name ".env*" -type f
```
**Expected output:** Only `.env.example` files should be found, no actual `.env` files.

### 2. Check for API Keys in Code
```bash
grep -r "sk-" . --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=.git
grep -r "pk_" . --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=.git
grep -r "AIza" . --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=.git
```
**Expected output:** No actual API keys should be found in source code.

### 3. Check for Log Files
```bash
find . -name "*.log" -type f
```
**Expected output:** Only log files in `node_modules` should be found.

### 4. Check for Upload Directories
```bash
ls -la backend/uploads/ 2>/dev/null || echo "uploads directory not found (good)"
ls -la backend/filled_forms/ 2>/dev/null || echo "filled_forms directory not found (good)"
```
**Expected output:** Directories should not exist or be empty.

### 5. Check Git Status
```bash
git status
```
**Expected output:** No `.env`, `uploads/`, `venv/`, `node_modules/`, or log files should be staged.

### 6. Check What Will Be Committed
```bash
git diff --cached --name-only
```
**Expected output:** Should not include any sensitive files.

## 🚨 Critical Files That Should NEVER Be Committed

- [ ] `.env` files (contain actual API keys)
- [ ] `backend/uploads/` directory (contains user files)
- [ ] `backend/filled_forms/` directory (contains processed forms)
- [ ] `venv/` directory (Python virtual environment)
- [ ] `node_modules/` directory (Node.js dependencies)
- [ ] `*.log` files (contain potentially sensitive logs)
- [ ] `server.log` and `server_output.log`
- [ ] Any files with API keys hardcoded

## ✅ Files That SHOULD Be Committed

- [ ] `.env.example` files (template for environment setup)
- [ ] `requirements.txt` (Python dependencies)
- [ ] `package.json` and `package-lock.json` (Node.js dependencies)
- [ ] Source code files (`.py`, `.tsx`, `.js`, etc.)
- [ ] Configuration files (`.json`, `.config.js`, etc.)
- [ ] Documentation files (`.md`, `.txt`, etc.)
- [ ] `.gitignore` (ensures sensitive files are ignored)

## 🔧 If You Find Sensitive Data

1. **Remove from Git tracking:**
   ```bash
   git rm --cached <sensitive_file>
   ```

2. **Add to .gitignore:**
   ```bash
   echo "<sensitive_file>" >> .gitignore
   ```

3. **Create example file:**
   ```bash
   cp <sensitive_file> <sensitive_file>.example
   # Edit .example file to remove actual secrets
   ```

4. **Commit the changes:**
   ```bash
   git add .gitignore <sensitive_file>.example
   git commit -m "Add .gitignore and example files"
   ```

## 🛡️ Additional Security Measures

1. **Use environment variables** for all sensitive data
2. **Rotate API keys** regularly
3. **Use GitHub Secrets** for CI/CD pipelines
4. **Enable branch protection** on main branch
5. **Review commits** before pushing
6. **Use .env.example** files to document required variables

## 📞 Emergency Contacts

If you accidentally commit sensitive data:

1. **Immediately revoke the exposed API keys**
2. **Create new API keys**
3. **Update your local .env file**
4. **Consider the repository compromised**
5. **Create a new repository if necessary**

## ✅ Final Verification

Run this command to verify everything is secure:

```bash
# Complete security check
echo "🔍 Security Check Results:" && \
echo "1. Environment files:" && find . -name ".env*" -type f && \
echo "2. API keys in code:" && (grep -r "sk-" . --exclude-dir=node_modules --exclude-dir=venv --exclude-dir=.git 2>/dev/null || echo "No OpenAI keys found") && \
echo "3. Log files:" && find . -name "*.log" -type f | grep -v node_modules && \
echo "4. Git status:" && git status --porcelain | head -10 && \
echo "✅ Security check complete!"
```

**If all checks pass, you're ready to push safely! 🚀** 
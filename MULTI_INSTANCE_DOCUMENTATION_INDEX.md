# Multi-Instance OpenAlgo - Documentation Index

Complete guide to all documentation files for running multiple OpenAlgo instances.

## 📋 Quick Navigation

### For First-Time Setup
1. Start with: **`QUICK_START_MULTI_INSTANCE.md`**
2. Then read: **`MULTI_INSTANCE_SETUP.md`**
3. Use for verification: **`SETUP_VERIFICATION_CHECKLIST.md`**

### For FivePaisa Instance
1. Start with: **`FIVEPAISA_SETUP_SUMMARY.md`**
2. Then read: **`FIVEPAISA_INSTANCE_CONFIG.md`**
3. Reference: **`FIVEPAISA_BATCH_FILE_CREATED.md`**

### For Technical Details
- **`MULTI_INSTANCE_SESSION_FIX.md`** - Why the fix was needed and how it works
- **`CHANGES_SUMMARY.md`** - Complete list of code changes

---

## 📚 Documentation Files

### 1. **QUICK_START_MULTI_INSTANCE.md**
**Purpose:** Quick reference guide for setting up multiple instances

**Contains:**
- TL;DR setup instructions
- Common mistakes and how to avoid them
- Key configuration values
- Quick troubleshooting
- File update checklist

**Read this if:** You want to get started quickly without reading everything

**Time to read:** 5-10 minutes

---

### 2. **MULTI_INSTANCE_SETUP.md**
**Purpose:** Complete, detailed setup guide for multi-instance deployments

**Contains:**
- Step-by-step setup instructions
- Port configuration examples
- Batch file usage
- How the system works
- Detailed troubleshooting section
- Configuration checklist
- Important notes and best practices

**Read this if:** You want detailed instructions and comprehensive troubleshooting

**Time to read:** 20-30 minutes

---

### 3. **MULTI_INSTANCE_SESSION_FIX.md**
**Purpose:** Technical explanation of the session isolation fix

**Contains:**
- Problem description
- Root cause analysis
- Solution explanation
- Before/after diagrams
- How it works now
- Testing instructions
- Verification steps
- Files modified

**Read this if:** You want to understand the technical details of why sessions were conflicting

**Time to read:** 15-20 minutes

---

### 4. **SETUP_VERIFICATION_CHECKLIST.md**
**Purpose:** Comprehensive checklist to verify your setup is correct

**Contains:**
- Pre-setup verification
- Configuration checklist for each instance
- Port uniqueness verification
- Database uniqueness verification
- Security key verification
- Batch file verification
- Pre-startup verification
- Startup verification
- Functional verification
- Cookie domain verification
- Troubleshooting verification
- Final verification
- Success criteria

**Read this if:** You want to verify your setup is correct before running instances

**Time to read:** 30-40 minutes (to complete all checks)

---

### 5. **FIVEPAISA_SETUP_SUMMARY.md**
**Purpose:** Quick summary for setting up the FivePaisa instance

**Contains:**
- Quick start guide
- All three instances summary
- Running all three simultaneously
- Configuration checklist
- Port summary
- Critical requirements
- Batch file details
- Troubleshooting
- Files created/modified
- Next steps
- Success criteria

**Read this if:** You just created the FivePaisa instance and want a quick overview

**Time to read:** 10-15 minutes

---

### 6. **FIVEPAISA_INSTANCE_CONFIG.md**
**Purpose:** Detailed configuration guide for the FivePaisa instance

**Contains:**
- Step-by-step setup for FivePaisa
- Configuration verification
- Port number verification
- Running all three instances
- Accessing all instances
- Troubleshooting specific to FivePaisa
- Important notes
- Batch file details
- Next steps

**Read this if:** You need detailed FivePaisa-specific configuration instructions

**Time to read:** 15-20 minutes

---

### 7. **FIVEPAISA_BATCH_FILE_CREATED.md**
**Purpose:** Documentation about the FivePaisa batch file

**Contains:**
- Summary of what was created
- File details
- What the batch file does
- How to use it
- Configuration checklist
- Port configuration table
- Important notes
- Troubleshooting
- Files modified/created
- Next steps
- Related documentation

**Read this if:** You want to understand what the batch file does

**Time to read:** 10-15 minutes

---

### 8. **CHANGES_SUMMARY.md**
**Purpose:** Detailed summary of all code changes made

**Contains:**
- Problem description
- Root causes
- Solution overview
- Files modified (with code snippets)
- How it works (before/after)
- Configuration requirements
- Testing instructions
- Backward compatibility
- Important notes
- Files affected

**Read this if:** You want to understand what code was changed and why

**Time to read:** 20-30 minutes

---

### 9. **MULTI_INSTANCE_DOCUMENTATION_INDEX.md**
**Purpose:** This file - navigation guide for all documentation

**Contains:**
- Quick navigation
- Documentation file descriptions
- Reading recommendations
- Batch files summary
- Configuration summary
- Instance summary
- Troubleshooting guide

**Read this if:** You're looking for a specific document or don't know where to start

**Time to read:** 10-15 minutes

---

## 🚀 Batch Files

### run_instance1.bat
**Purpose:** Start OpenAlgo Instance 1 (IndMoney)

**Configuration:**
- FLASK_PORT: 5003
- WEBSOCKET_PORT: 8767
- DATABASE: sqlite:///db/openalgo_indmoney.db
- ENV FILE: .env.indmoney

**Usage:**
```bash
run_instance1.bat
```

**Access:** http://127.0.0.1:5003

---

### run_instance2.bat
**Purpose:** Start OpenAlgo Instance 2 (Zerodha)

**Configuration:**
- FLASK_PORT: 5004
- WEBSOCKET_PORT: 8768
- DATABASE: sqlite:///db/openalgo_zerodha.db
- ENV FILE: .env.zerodha

**Usage:**
```bash
run_instance2.bat
```

**Access:** http://127.0.0.1:5004

---

### run_instance3.bat
**Purpose:** Start OpenAlgo Instance 3 (FivePaisa)

**Configuration:**
- FLASK_PORT: 5005
- WEBSOCKET_PORT: 8769
- DATABASE: sqlite:///db/openalgo_fivepaisa.db
- ENV FILE: .env.fivepaisa

**Usage:**
```bash
run_instance3.bat
```

**Access:** http://127.0.0.1:5005

---

## ⚙️ Configuration Summary

### Instance 1 - IndMoney
```
FLASK_PORT=5003
HOST_SERVER=http://127.0.0.1:5003
WEBSOCKET_PORT=8767
WEBSOCKET_URL=ws://127.0.0.1:8767
DATABASE_URL=sqlite:///db/openalgo_indmoney.db
```

### Instance 2 - Zerodha
```
FLASK_PORT=5004
HOST_SERVER=http://127.0.0.1:5004
WEBSOCKET_PORT=8768
WEBSOCKET_URL=ws://127.0.0.1:8768
DATABASE_URL=sqlite:///db/openalgo_zerodha.db
```

### Instance 3 - FivePaisa
```
FLASK_PORT=5005
HOST_SERVER=http://127.0.0.1:5005
WEBSOCKET_PORT=8769
WEBSOCKET_URL=ws://127.0.0.1:8769
DATABASE_URL=sqlite:///db/openalgo_fivepaisa.db
```

---

## 📊 Instance Summary

| Instance | Broker | Port | WebSocket | Database | Batch File |
|----------|--------|------|-----------|----------|-----------|
| 1 | IndMoney | 5003 | 8767 | openalgo_indmoney.db | run_instance1.bat |
| 2 | Zerodha | 5004 | 8768 | openalgo_zerodha.db | run_instance2.bat |
| 3 | FivePaisa | 5005 | 8769 | openalgo_fivepaisa.db | run_instance3.bat |

---

## 🔧 Troubleshooting Guide

### Issue: Login redirects to wrong port
**Solution:** Check `MULTI_INSTANCE_SETUP.md` → Troubleshooting → "Login on port 5003 redirects to port 5000"

### Issue: Port already in use
**Solution:** Check `MULTI_INSTANCE_SETUP.md` → Troubleshooting → "Port already in use"

### Issue: Database locked
**Solution:** Check `MULTI_INSTANCE_SETUP.md` → Troubleshooting → "Database locked error"

### Issue: Session conflicts between instances
**Solution:** Check `MULTI_INSTANCE_SESSION_FIX.md` → How It Works Now

### Issue: FivePaisa-specific problems
**Solution:** Check `FIVEPAISA_INSTANCE_CONFIG.md` → Troubleshooting

### General troubleshooting
**Solution:** Check `SETUP_VERIFICATION_CHECKLIST.md` → Troubleshooting Verification

---

## 📖 Reading Recommendations

### For Complete Beginners
1. `QUICK_START_MULTI_INSTANCE.md` (5-10 min)
2. `MULTI_INSTANCE_SETUP.md` (20-30 min)
3. `SETUP_VERIFICATION_CHECKLIST.md` (30-40 min to complete)

**Total time:** 1-1.5 hours

### For Experienced Users
1. `QUICK_START_MULTI_INSTANCE.md` (5-10 min)
2. `SETUP_VERIFICATION_CHECKLIST.md` (10-15 min to skim)

**Total time:** 15-25 minutes

### For Technical Understanding
1. `MULTI_INSTANCE_SESSION_FIX.md` (15-20 min)
2. `CHANGES_SUMMARY.md` (20-30 min)

**Total time:** 35-50 minutes

### For FivePaisa Setup
1. `FIVEPAISA_SETUP_SUMMARY.md` (10-15 min)
2. `FIVEPAISA_INSTANCE_CONFIG.md` (15-20 min)

**Total time:** 25-35 minutes

---

## ✅ Critical Checklist

Before running instances, verify:

- [ ] `HOST_SERVER` matches `FLASK_PORT` in each `.env` file
- [ ] `WEBSOCKET_URL` matches `WEBSOCKET_PORT` in each `.env` file
- [ ] Each instance uses unique FLASK_PORT
- [ ] Each instance uses unique WEBSOCKET_PORT
- [ ] Each instance uses unique DATABASE_URL
- [ ] Each instance has unique APP_KEY
- [ ] Each instance has unique API_KEY_PEPPER
- [ ] All required variables are present in each `.env` file
- [ ] Browser cookies for `127.0.0.1` are cleared
- [ ] Batch files exist and are executable

---

## 🎯 Success Criteria

Your setup is successful if:

✅ All three instances start without errors
✅ Each instance is accessible on its own port
✅ Sessions are isolated between instances
✅ Logging out on one instance doesn't affect others
✅ Each broker is connected and working
✅ WebSocket connections work on all instances

---

## 📞 Support

For issues or questions:

1. **Quick answers:** Check `QUICK_START_MULTI_INSTANCE.md` common mistakes
2. **Detailed help:** Check `MULTI_INSTANCE_SETUP.md` troubleshooting
3. **Verification:** Use `SETUP_VERIFICATION_CHECKLIST.md`
4. **Technical details:** Read `MULTI_INSTANCE_SESSION_FIX.md`
5. **FivePaisa specific:** Check `FIVEPAISA_INSTANCE_CONFIG.md`

---

## 📝 File Organization

```
OpenAlgo Root Directory
├── run_instance1.bat                          (Start IndMoney)
├── run_instance2.bat                          (Start Zerodha)
├── run_instance3.bat                          (Start FivePaisa)
├── .env.indmoney                              (IndMoney config)
├── .env.zerodha                               (Zerodha config)
├── .env.fivepaisa                             (FivePaisa config)
├── QUICK_START_MULTI_INSTANCE.md              (Quick reference)
├── MULTI_INSTANCE_SETUP.md                    (Complete guide)
├── MULTI_INSTANCE_SESSION_FIX.md              (Technical details)
├── SETUP_VERIFICATION_CHECKLIST.md            (Verification)
├── FIVEPAISA_SETUP_SUMMARY.md                 (FivePaisa overview)
├── FIVEPAISA_INSTANCE_CONFIG.md               (FivePaisa guide)
├── FIVEPAISA_BATCH_FILE_CREATED.md            (Batch file docs)
├── CHANGES_SUMMARY.md                         (Code changes)
└── MULTI_INSTANCE_DOCUMENTATION_INDEX.md      (This file)
```

---

**Last Updated:** 2026-09-30
**Status:** ✅ Complete and ready to use

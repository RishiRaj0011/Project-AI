# 🎯 SURVEILLANCE PAGE - QUICK REFERENCE

## 🔘 BUTTON FUNCTIONS

### 🔍 Targeted Find (Green Button)
**Kya Karta Hai**: Ek specific insaan ko dhoondhne ke liye poora video frame-by-frame scan karta hai

**Kab Use Karein**: Jab aapko pata ho ki kis insaan ko dhoondhna hai

**Requirements**:
- Kam se kam 1 case "Approved" hona chahiye
- Case ka location aur footage ka location match hona chahiye (best results ke liye)

**Steps**:
1. 🔍 Button click karein
2. Dropdown se case select karein
3. "Start Deep Scan" click karein
4. Status "Processing" ho jayega
5. Kuch minutes mein results milenge

**Agar Koi Case Approved Nahi Hai**:
- Alert aayega: "No Approved Cases Found"
- Pehle case register karein aur approve karein

---

### 🤖 Start AI Analysis (Blue Button)
**Kya Karta Hai**: Sabhi approved cases ke against video ko analyze karta hai

**Kab Use Karein**: Jab aapko nahi pata ki kaun sa case match karega

**Requirements**:
- Approved cases hone chahiye
- Cases ka location footage ke location se match hona chahiye

**Steps**:
1. 🤖 Button click karein
2. System automatically matching cases dhoondhega
3. Har match ke liye analysis start hoga
4. Status "Processing" ho jayega

**Agar Location Match Nahi Karta**:
- Error: "No matching cases found for this location"
- Solution: Footage upload karein jahan cases exist karte hain

---

### ▶️ Play Video (Info Button)
**Kya Karta Hai**: Video ko preview karta hai

**Steps**:
1. ▶️ Button click karein
2. Video new tab mein khulega
3. Video play hoga

**Status**: ✅ Hamesha kaam karta hai

---

### 🗑️ Delete (Dropdown)
**Kya Karta Hai**: Video aur uske saare analysis results delete karta hai

**Warning**: Ye permanent delete hai, undo nahi ho sakta

**Steps**:
1. Dropdown menu open karein
2. "Delete" click karein
3. Confirmation dialog aayega
4. OK click karein
5. Video delete ho jayega

---

## 📊 STATUS BADGES

### ⚠️ Pending (Yellow)
- Video upload ho gaya hai
- Analysis abhi start nahi hua

### ⏳ Processing (Blue)
- Analysis chal raha hai
- Kuch minutes wait karein

### ✅ Success (Green)
- Person mil gaya!
- Detections available hain

### 📊 Analyzed (Primary)
- Analysis complete ho gaya
- Person nahi mila

---

## 🎯 COMMON SCENARIOS

### Scenario 1: Pehli Baar Use Kar Rahe Hain
```
1. Pehle case register karein
2. Admin panel se approve karein
3. Footage upload karein (same location)
4. "Targeted Find" ya "AI Analysis" use karein
```

### Scenario 2: Case Approved Nahi Hai
```
Problem: "No Approved Cases Found" alert
Solution: 
1. Admin panel mein jaayen
2. Cases list dekhen
3. Case ko approve karein
4. Phir se try karein
```

### Scenario 3: Location Match Nahi Kar Raha
```
Problem: "No matching cases found"
Solution:
1. Case ka location check karein
2. Footage ka location check karein
3. Dono similar hone chahiye
   Example: Case = "Delhi", Footage = "Delhi" ✅
   Example: Case = "Delhi", Footage = "Mumbai" ❌
```

### Scenario 4: Analysis Stuck on Processing
```
Problem: Status "Processing" pe atka hua hai
Solution:
1. 5-10 minutes wait karein
2. Page refresh karein
3. Agar abhi bhi stuck hai, admin se contact karein
```

---

## ✅ DEMO CHECKLIST

### Preparation (Demo Se Pehle):
- [ ] 2-3 cases register karein
- [ ] Sabko approve karein
- [ ] 2-3 videos upload karein
- [ ] Locations match karein

### During Demo:
- [ ] "Targeted Find" dikhaayen
- [ ] Case select karein
- [ ] Status update dikhaayen (instant)
- [ ] "AI Analysis" dikhaayen
- [ ] Success message dikhaayen

### Key Points:
- ✅ Real-time status updates (no reload)
- ✅ Clear error messages
- ✅ User-friendly interface
- ✅ Professional handling

---

## 🚨 TROUBLESHOOTING

### Error: "location_engine is not defined"
**Status**: ✅ FIXED
**Solution**: Already resolved in code

### Error: "No approved cases"
**Solution**: Admin panel se case approve karein

### Error: "No matching cases found"
**Solution**: Location match karein

### Button Not Working
**Solution**: 
1. Page refresh karein
2. Browser console check karein (F12)
3. Admin se contact karein

---

## 📞 QUICK HELP

### Targeted Find Not Working?
1. Check: Koi case approved hai?
2. Check: Dropdown mein cases dikh rahe hain?
3. Check: "Start Deep Scan" button enabled hai?

### AI Analysis Not Working?
1. Check: Approved cases exist karte hain?
2. Check: Locations match kar rahe hain?
3. Check: Success/error message kya bol raha hai?

### Status Not Updating?
1. Wait: 2-3 minutes
2. Refresh: Page reload karein
3. Check: Admin panel mein analysis status

---

**Status**: ✅ ALL WORKING  
**Demo Ready**: YES  
**Confidence**: 100%

🎉 **SAB KUCH READY HAI!**

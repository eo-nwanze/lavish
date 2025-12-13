# SHOPIFY SELLING PLANS DEBUG - Which Theme Are You Using?

## 🎯 **CRITICAL DISCOVERY**

You have **TWO THEMES** with different approaches:

### Theme 1: `crave_theme` (Django API Approach)
- Path: `C:\Users\Stylz\Desktop\llavish\app\crave_theme`
- Method: Fetches plans from Django backend via API
- Uses: `product-subscription-options.liquid` snippet
- Debug logs: `[Subscription Plans]`, `[Render Plan]`

### Theme 2: `lavish_frontend` (Shopify Native Approach)  
- Path: `C:\Users\Stylz\Desktop\llavish\app\lavish_frontend`
- Method: Uses Shopify's native `product.selling_plan_groups`
- Uses: `subscription-purchase-options.liquid` snippet
- Debug logs: `[Lavish Frontend]`

---

## 🔍 **WHICH THEME ARE YOU VIEWING?**

Your console shows **NO subscription logs at all**, which means:

**Either:**
1. You're viewing `lavish_frontend` (my crave_theme logs won't show)
2. You haven't restarted Shopify CLI yet
3. You're on a page without subscriptions

---

## ✅ **FIX APPLIED TO BOTH THEMES**

I've added debug logging to **BOTH** themes, so whichever one you're using, you'll now see logs!

### If Using `crave_theme`:
**You'll see:**
```javascript
[Subscription Plans] API Response Status: 200
[Subscription Plans] Plans count: 7
[Render Plan] Processing: Monthly Lavish Box
[Render Plan] Price adjustment value: 10
[Render Plan] PERCENTAGE discount text: Save 10%
```

### If Using `lavish_frontend`:
**You'll now see:**
```javascript
[Lavish Frontend] Plan: Monthly Lavish Box Raw value: -10 Abs value: 10 Is < 1? false
[Lavish Frontend] Whole number format - Percent: 10
```

---

## 🧪 **TESTING INSTRUCTIONS**

### Step 1: Determine Which Theme You're Running

Check your terminal - which directory did you run `shopify theme dev` from?

**If you see:**
```bash
C:\Users\Stylz\Desktop\llavish\app\crave_theme>
```
→ You're using **crave_theme**

**If you see:**
```bash
C:\Users\Stylz\Desktop\llavish\app\lavish_frontend>
```
→ You're using **lavish_frontend**

---

### Step 2: Restart Shopify CLI

```bash
# Stop it: Ctrl+C

# For crave_theme:
cd C:\Users\Stylz\Desktop\llavish\app\crave_theme
shopify theme dev

# OR for lavish_frontend:
cd C:\Users\Stylz\Desktop\llavish\app\lavish_frontend
shopify theme dev
```

---

### Step 3: Hard Refresh Browser

Press **Ctrl+Shift+R** to bypass cache

---

### Step 4: Check Console

Open DevTools (F12) → Console tab

**You should NOW see either:**
- `[Subscription Plans]` messages (if crave_theme)
- `[Lavish Frontend]` messages (if lavish_frontend)

---

## 📊 **Expected Debug Output**

### For `lavish_frontend` Theme:

```javascript
[Lavish Frontend] Plan: Monthly Lavish Box Raw value: -10 Abs value: 10 Is < 1? false
[Lavish Frontend] Whole number format - Percent: 10

[Lavish Frontend] Plan: Monthly Book Box Raw value: -15 Abs value: 15 Is < 1? false
[Lavish Frontend] Whole number format - Percent: 15

[Lavish Frontend] Plan: Quarterly Box Raw value: -25 Abs value: 25 Is < 1? false
[Lavish Frontend] Whole number format - Percent: 25
```

**On Page:**
```
Monthly Lavish Box    10% off
Monthly Book Box      15% off
Quarterly Box         25% off
```

---

### For `crave_theme` Theme:

```javascript
[Subscription Plans] API Response Status: 200
[Subscription Plans] Plans count: 7
[Render Plan] Processing: Monthly Lavish Box
[Render Plan] Price adjustment type: PERCENTAGE
[Render Plan] Price adjustment value: 10
[Render Plan] Value type: number
[Render Plan] Checking discount - Type: PERCENTAGE Value: 10 Value > 0? true
[Render Plan] PERCENTAGE discount text: Save 10%
[Render Plan] Final discount text: Save 10%
```

**On Page:**
```
Monthly Lavish Box    Save 10%
Monthly Book Box      Save 15%
Quarterly Box         Save 25%
```

---

## 🐛 **If You See Wrong Percentages**

### Scenario A: Shows "0% off"

**Console will show:**
```javascript
[Lavish Frontend] Raw value: 0 Abs value: 0 Is < 1? true
[Lavish Frontend] Decimal format - Percent: 0
```

**Cause:** Shopify selling plan has no discount set

**Fix:** Update selling plan in Shopify admin

---

### Scenario B: Shows "97% off" (wrong value)

**Console will show:**
```javascript
[Lavish Frontend] Raw value: -0.97 Abs value: 0.97 Is < 1? true
[Lavish Frontend] Decimal format - Percent: 97
```

**Cause:** Shopify stored it as `-0.03` (3% off) but you're seeing 97%

**Fix:** The logic is detecting decimal vs whole number incorrectly

---

### Scenario C: Shows Nothing

**Console shows:**
- No `[Subscription Plans]` logs
- No `[Lavish Frontend]` logs

**Cause:** Snippet not loading

**Fix:** Restart CLI and hard refresh

---

## 🎯 **What to Share with Me**

After restarting CLI and refreshing:

### 1. Which theme are you using?
```
Copy/paste from terminal showing directory
```

### 2. Full console output
```
Copy ALL logs, especially:
- [Subscription Plans] OR [Lavish Frontend] messages
```

### 3. What you see on the page
```
List each plan and what percentage it shows
Example:
- Monthly Lavish Box: 10% off ✅
- Monthly Book Box: 0% off ❌
- etc.
```

### 4. Screenshot (optional)
Visual of the subscription section

---

## 🔧 **Files Modified**

### 1. `app/crave_theme/sections/main-product.liquid`
- Added snippet include

### 2. `app/crave_theme/sections/featured-product.liquid`
- Added snippet include

### 3. `app/crave_theme/snippets/product-subscription-options.liquid`
- Added extensive debug logging

### 4. `app/lavish_frontend/snippets/subscription-purchase-options.liquid`
- Added debug logging for Shopify native data

---

## ⚡ **Quick Diagnostic**

**Paste this in browser console:**

```javascript
// Check which snippet is loaded
if (document.querySelector('.product-subscription-options')) {
  console.log('✅ Using CRAVE_THEME (Django API approach)');
} else if (document.querySelector('.subscription-purchase-options')) {
  console.log('✅ Using LAVISH_FRONTEND (Shopify native approach)');
} else {
  console.log('❌ No subscription snippet found!');
}

// Check for selling plans in page data
if (window.Shopify && window.Shopify.routes) {
  console.log('Shopify data loaded');
}
```

---

## 📋 **Checklist**

Before responding, complete ALL of these:

- [ ] Determined which theme directory CLI is running from
- [ ] Restarted Shopify CLI
- [ ] Hard refreshed browser (Ctrl+Shift+R)
- [ ] Opened console (F12)
- [ ] Can see new debug logs (`[Subscription Plans]` OR `[Lavish Frontend]`)
- [ ] Ran the Quick Diagnostic script above
- [ ] Copied ALL console output
- [ ] Listed what percentages are showing on page

---

## 🎯 **Summary**

| Issue | Status |
|-------|--------|
| Two different themes | ℹ️ Identified |
| Debug logging added to crave_theme | ✅ Done |
| Debug logging added to lavish_frontend | ✅ Done |
| Need to know which theme you're using | ⏳ Waiting |
| Need console output after restart | ⏳ Waiting |
| Need visual confirmation | ⏳ Waiting |

---

**NEXT STEP:** Restart Shopify CLI, refresh browser, share console output showing which theme's logs appear!


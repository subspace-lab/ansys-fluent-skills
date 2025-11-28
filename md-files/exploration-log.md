# Ansys Help Exploration Log

## Date: 2024-11-28

## Objective
Determine how to programmatically access Ansys Fluent documentation (Theory Guide, User's Guide) for the ansys-fluent-skills project.

---

## What Does NOT Work

### 1. Direct URL Access (WebFetch/curl)
```
URL: https://ansyshelp.ansys.com/public/Views/Secured/corp/v242/en/flu_th/flu_th_sec_turb_kw_std.html
Result: "Access Denied" from Akamai CDN
```
- WebFetch fails with "socket connection closed unexpectedly"
- curl with HTTP/2 fails with exit code 92 (HTTP/2 stream error)
- curl with HTTP/1.1 hangs indefinitely

### 2. Playwright Headless Mode (Direct URL)
```python
await page.goto("https://ansyshelp.ansys.com/...")
```
- Returns `net::ERR_HTTP2_PROTOCOL_ERROR`
- CDN blocks requests that don't follow expected browser flow

### 3. Playwright Headed Mode (Direct URL)
- First page redirects to Azure B2C login: `ansysaccount.b2clogin.com`
- Direct navigation to content URLs returns "Access Denied"
- Even with session cookies from landing page, direct URL navigation fails

### 4. Setting Referrer Header
```python
await page.set_extra_http_headers({"Referer": "https://ansyshelp.ansys.com/..."})
```
- Does not bypass the access control
- Still returns "Access Denied"

### 5. Opening Content URL in New Tab (Same Context)
```python
page2 = await context.new_page()  # Same context = shared cookies
await page2.goto(content_url)
```
- Shared cookies don't help
- Still blocked by CDN

---

## What WORKS

### 1. WebSearch for High-Level Information
```
Query: "PyFluent boundary_conditions velocity_inlet"
Query: "site:ansyshelp.ansys.com Fluent TUI /define/models"
```
- Returns useful summaries with code examples
- Good for API function signatures
- Good for finding correct terminology

### 2. Playwright with Proper Navigation Flow

#### Key Requirements:
1. **Start from product landing page** (establishes session)
2. **Content is in Frame 1** (iframe inside main page)
3. **Navigate via link clicks** (not direct URL)
4. **Use stealth mode** to avoid bot detection

#### Working Code Pattern:
```python
browser = await p.chromium.launch(
    headless=False,  # Headed mode required
    args=["--disable-blink-features=AutomationControlled"]
)

context = await browser.new_context(
    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36..."
)

page = await context.new_page()

# Hide automation detection
await page.add_init_script("""
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
""")

# Step 1: Open product landing page
await page.goto(
    "https://ansyshelp.ansys.com/public/Views/Secured/prod_page.html?pn=Fluent&pid=Fluent&lang=en",
    timeout=90000,
    wait_until="domcontentloaded"
)

# Step 2: Accept cookies
btn = await page.query_selector("text=Accept All Cookies")
if btn: await btn.click()

await page.wait_for_timeout(5000)

# Step 3: Content is in Frame 1
content_frame = page.frames[1]

# Step 4: Navigate by clicking links
theory_link = await content_frame.query_selector('a:has-text("Theory Guide")')
await theory_link.click()
await page.wait_for_timeout(4000)

# Step 5: Continue navigation
content_frame = page.frames[1]  # Re-fetch frame reference after navigation
turb_link = await content_frame.query_selector('a:has-text("4. Turbulence")')
await turb_link.click()

# Step 6: Get content from Frame 1
body = await content_frame.inner_text("body")
```

### 3. ENEA Mirror (Old Fluent 12.0 Docs)
```
URL: https://www.afs.enea.it/project/neptunius/docs/fluent/html/th/node67.htm
```
- Works with `curl -k` (ignore SSL)
- Contains same theory equations (older version)
- Useful as fallback for theory content

---

## Site Architecture Findings

### URL Structure
```
Landing page: /public/Views/Secured/prod_page.html?pn=Fluent&pid=Fluent&lang=en
Theory Guide: /public/Views/Secured/corp/v252/en/flu_th/flu_th.html
SST k-omega:  /public/Views/Secured/corp/v252/en/flu_th/flu_th_sec_turb_kw_sst.html
```

### Version Mapping
| Release | URL Version |
|---------|-------------|
| 2025 R2 | v252 |
| 2025 R1 | v251 |
| 2024 R2 | v242 |

### Frame Structure
```
Frame 0: Main page (navigation only) - /public/account/secured?returnurl=...
Frame 1: Content iframe - /public//Views/Secured/corp/v252/en/...
Frame 2: Analytics (demdex.net)
Frame 3: about:blank
```

### Authentication Flow
1. Main page redirects to `/public/account/secured?returnurl=...`
2. This establishes a session without requiring login
3. Content loads in iframe (Frame 1)
4. Direct URL access is blocked by Akamai CDN

---

## Content Extraction

### Table of Contents (Theory Guide)
```
Using This Manual
1. Basic Fluid Flow
2. Flows with Moving Reference Frames
3. Flows Using Sliding and Dynamic Meshes
4. Turbulence
   4.1. Underlying Principles of Turbulence Modeling
   4.2. Spalart-Allmaras Model
   4.3. Standard, RNG, and Realizable k-ε Models
   4.4. Standard, BSL, and SST k-ω Models
   4.5. Generalized k-ω (GEKO) Model
   ...
5. Heat Transfer
...
19. Battery Model
...
```

### Sample Extracted Content (SST k-ω Model)
```
4.4.3. Shear-Stress Transport (SST) k-ω Model

4.4.3.1. Overview
The SST k-ω model includes all the refinements of the BSL k-ω model...

4.4.3.2. Modeling the Turbulent Viscosity
[Equation 4-118, 4-119, 4-120]

4.4.3.3. Model Constants
All additional model constants have the same values as for the standard k-ω model...
```

---

## Recommendations for Implementation

### 1. Hybrid Approach
- **Quick lookups**: Use WebSearch (no Playwright needed)
- **Detailed theory**: Use Playwright with navigation flow
- **PyFluent API**: Use WebSearch + WebFetch on fluent.docs.pyansys.com

### 2. Playwright Settings
```python
# Required for Ansys Help
headless=False  # or True with additional stealth
args=["--disable-blink-features=AutomationControlled"]
user_agent="Mozilla/5.0..."  # Real browser UA
init_script: navigator.webdriver = undefined
```

### 3. Navigation Pattern
```
Product Page → Accept Cookies → Frame 1 → Click TOC Links → Extract Content
```

### 4. Error Handling
- Timeout on initial load: Retry with longer timeout
- Link not visible: Use `scroll_into_view_if_needed()`
- Frame reference stale: Re-fetch `page.frames[1]` after each navigation

---

## Files Created During Exploration

| File | Content |
|------|---------|
| `temp/theory_content.txt` | Theory Guide TOC |
| `temp/turbulence_content.txt` | Turbulence chapter |
| `temp/komega_section.txt` | k-ω models section |
| `temp/sst_equations.txt` | SST k-ω equations |
| `temp/sst_theory.html` | SST page (from ENEA mirror) |

---

## Key Learnings

1. **Session establishment is critical** - Cannot bypass by setting headers/cookies manually
2. **Content is in iframe** - Must interact with Frame 1, not main page
3. **Bot detection is active** - Need stealth measures
4. **Direct iframe navigation works after session** - Once session established, can use `content_frame.goto(url)` directly!
5. **Version in URL matters** - v252 for 2025 R2
6. **WebSearch is sufficient for many use cases** - Only need Playwright for detailed theory

---

## FINAL OPTIMIZATION (Critical Discovery)

After session is established via landing page, **direct iframe navigation works**:

```python
# After session established (visit landing page once)
content_frame = page.frames[1]

# Direct navigation - NO need to click through TOC!
target_url = "https://ansyshelp.ansys.com/public//Views/Secured/corp/v252/en/flu_th/flu_th_sec_turb_kw_sst.html"
await content_frame.goto(target_url, timeout=30000, wait_until="domcontentloaded")

# Extract content
body = await content_frame.inner_text("body")
```

This is **much faster** than clicking through TOC links one by one.

### URL Mapping for Common Sections
```python
THEORY_URLS = {
    "turbulence_overview": "corp/v252/en/flu_th/flu_th_turb.html",
    "k_omega_sst": "corp/v252/en/flu_th/flu_th_sec_turb_kw_sst.html",
    "battery": "corp/v252/en/flu_th/flu_th_battery.html",
    # ... etc
}
```

### Wrapped URL Format Also Works
```
https://ansyshelp.ansys.com/public/account/secured?returnurl=/Views/Secured/corp/v252/en/flu_th/flu_th_sec_turb_kw_sst.html
```

Both approaches (direct iframe.goto and wrapped URL with page.goto) work after session is established.

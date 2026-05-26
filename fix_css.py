"""Fix corrupted characters and CSS scoping issues in styles.css"""

with open('C:/GIT/web-escritor/styles.css', 'r', encoding='utf-8') as f:
    css = f.read()

original = css

# --- Fix 1: Scope .faq-question::after to details only (fixes double + on button FAQs) ---
old1 = '.faq-question::after{content:\'+\';font-size:1.2rem;color:var(--accent,#c4944d);flex-shrink:0;transition:transform 0.2s}'
new1 = 'details>.faq-question::after{content:\'+\';font-size:1.2rem;color:var(--accent,#c4944d);flex-shrink:0;transition:transform 0.2s}'
assert old1 in css, f"OLD1 not found!"
css = css.replace(old1, new1, 1)

# --- Fix 2: Fix corrupted minus sign in details[open] FAQ (UTF-8 double-encoding of U+2212) ---
# Raw bytes in file: c3 a2 cb 86 e2 80 99 => Python string: â\u02c6\u2019
corrupted_minus = '\u00e2\u02c6\u2019'
old2 = f"details[open]>.faq-question::after{{content:'{corrupted_minus}'}}"
new2 = "details[open]>.faq-question::after{content:'-'}"
assert old2 in css, f"OLD2 not found! Trying alternative..."
css = css.replace(old2, new2, 1)

# --- Fix 3: Fix corrupted em dash in book-finds li::before (UTF-8 double-encoding of U+2014) ---
# Raw bytes: c3 a2 e2 82 ac e2 80 9d => Python string: â\u20ac\u201d
corrupted_emdash = '\u00e2\u20ac\u201d'
old3 = f"book-finds li::before{{content:'{corrupted_emdash}';"
new3 = "book-finds li::before{content:'\\2014';"
assert old3 in css, f"OLD3 not found!"
css = css.replace(old3, new3, 1)

# --- Fix 4: Add justify-content:flex-start to .lore-bento-card--large (removes gap above espejo) ---
old4 = '.lore-bento-card--large{grid-column:span 2;grid-row:span 2;min-height:436px}'
new4 = '.lore-bento-card--large{grid-column:span 2;grid-row:span 2;min-height:436px;justify-content:flex-start}'
assert old4 in css, f"OLD4 not found!"
css = css.replace(old4, new4, 1)

if css != original:
    with open('C:/GIT/web-escritor/styles.css', 'w', encoding='utf-8') as f:
        f.write(css)
    print("styles.css updated successfully")
    print(f"  Fix 1 (FAQ scoping): {old1[:60]}...")
    print(f"  Fix 2 (minus sign):  corrupted -> '-'")
    print(f"  Fix 3 (em dash):     corrupted -> CSS \\2014")
    print(f"  Fix 4 (bento gap):   added justify-content:flex-start to --large")
else:
    print("WARNING: No changes made!")

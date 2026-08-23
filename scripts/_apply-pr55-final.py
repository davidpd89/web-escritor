#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def one(text, old, new, label):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected 1 match, found {n}")
    return text.replace(old, new, 1)

# Worker: validation/privacy only.
p = ROOT / 'cloudflare-worker-subscribe.js'
s = p.read_text(encoding='utf-8')
s = one(s,
''' *   - `listIds`, `attributes`, and `updateEnabled` are never read from the
 *     client at all — listIds comes from env.BREVO_LIST_ID, attributes is
 *     built entirely server-side from the validated source/result, and
 *     updateEnabled is hardcoded to true below.
''',
''' *   - `includeListIds`, `templateId`, `redirectionUrl` and `attributes` are
 *     never accepted from the client. The list/template/redirect come from
 *     server-side configuration and attributes are built from validated enums.
''', 'worker stale comment')
s = one(s,
'''    if (!EMAIL_RE.test(normalizedEmail)) {
      return jsonResponse(origin, 400, { ok: false, message: "Dirección de email no válida." });
    }
''',
'''    if (normalizedEmail.length > 254 || !EMAIL_RE.test(normalizedEmail)) {
      return jsonResponse(origin, 400, { ok: false, message: "Dirección de email no válida." });
    }
''', 'worker email length')
s = one(s,
'''    } catch (err) {
      console.error("Brevo DOI request failed:", err);
      return jsonResponse(origin, 502, {
''',
'''    } catch {
      console.error("Brevo DOI request failed");
      return jsonResponse(origin, 502, {
''', 'worker network log')
s = one(s,
'''    let brevoBodyText = "";
    try {
      brevoBodyText = await brevoRes.text();
    } catch {
      // Best effort only. Upstream details are never forwarded to the browser.
    }
    console.error(`Brevo DOI error ${brevoRes.status}:`, brevoBodyText.slice(0, 500));
''',
'''    // Brevo may echo contact data: never log the provider response body.
    console.error(`Brevo DOI error ${brevoRes.status}`);
''', 'worker upstream log')
p.write_text(s, encoding='utf-8')

# Frontend: local length validation + one in-flight POST per form.
p = ROOT / 'script.js'
s = p.read_text(encoding='utf-8')
s = one(s,
'''// listIds/attributes/templateId/redirectionUrl are never client-controlled.
// client-controlled — the Worker validates `source` against its own
''',
'''// listIds/attributes/templateId/redirectionUrl are never client-controlled.
// The Worker validates `source` against its own
''', 'client comment')
s = one(s,
'''function isValidNewsletterEmail(value) {
  return NEWSLETTER_EMAIL_RE.test(String(value || "").trim());
}
''',
'''function isValidNewsletterEmail(value) {
  const normalized = String(value || "").trim();
  return normalized.length <= 254 && NEWSLETTER_EMAIL_RE.test(normalized);
}
''', 'client email length')
s = one(s,
'''        statusEl.textContent = "";
        submitBtn.disabled = true;
        submitBtn.textContent = "Enviando…";
        try {
''',
'''        if (subscribeForm.dataset.submitting === "true") return;
        subscribeForm.dataset.submitting = "true";
        statusEl.textContent = "";
        submitBtn.disabled = true;
        submitBtn.textContent = "Enviando…";
        try {
''', 'quiz guard')
s = one(s,
'''        } catch (err) {
          statusEl.textContent = newsletterErrorMessage(err.message);
          submitBtn.disabled = false;
          submitBtn.textContent = "Desbloquear mi arquetipo";
        }
''',
'''        } catch (err) {
          delete subscribeForm.dataset.submitting;
          statusEl.textContent = newsletterErrorMessage(err.message);
          submitBtn.disabled = false;
          submitBtn.textContent = "Desbloquear mi arquetipo";
        }
''', 'quiz reset')
s = one(s,
'''        if (statusEl) statusEl.textContent = "";
        submitBtn.disabled = true;
        submitBtn.textContent = "Enviando…";
        try {
''',
'''        if (form.dataset.submitting === "true") return;
        form.dataset.submitting = "true";
        if (statusEl) statusEl.textContent = "";
        submitBtn.disabled = true;
        submitBtn.textContent = "Enviando…";
        try {
''', 'generic guard')
s = one(s,
'''        } catch (err) {
          if (statusEl) statusEl.textContent = newsletterErrorMessage(err.message);
          submitBtn.disabled = false;
          submitBtn.textContent = "Suscribirme";
        }
''',
'''        } catch (err) {
          delete form.dataset.submitting;
          if (statusEl) statusEl.textContent = newsletterErrorMessage(err.message);
          submitBtn.disabled = false;
          submitBtn.textContent = "Suscribirme";
        }
''', 'generic reset')
s = one(s,
'''        okTitle: "Revisa tu correo",
        okBody: "Te hemos enviado un mensaje de confirmación. Abre el enlace para completar la suscripción.",
        dupeTitle: "✓ Ya estás suscrito.",
        dupeBody: "¡Gracias por seguir a David Porto Díaz!"
''',
'''        okTitle: "Revisa tu correo",
        okBody: "Te hemos enviado un mensaje de confirmación. Abre el enlace para completar la suscripción."
''', 'popup copy Noveris')
s = one(s,
'''      okTitle: "Revisa tu correo",
      okBody: "Te hemos enviado un mensaje de confirmación. Abre el enlace para completar la suscripción.",
      dupeTitle: "✓ Ya estás suscrito.",
      dupeBody: "¡Gracias por seguir a David Porto Díaz!"
''',
'''      okTitle: "Revisa tu correo",
      okBody: "Te hemos enviado un mensaje de confirmación. Abre el enlace para completar la suscripción."
''', 'popup copy generic')
s = one(s,
'''    document.getElementById("nl-popup-form").addEventListener("submit", function (e) {
      e.preventDefault();
      scheduleTask(async function () {
''',
'''    document.getElementById("nl-popup-form").addEventListener("submit", function (e) {
      e.preventDefault();
      const popupForm = e.currentTarget;
      scheduleTask(async function () {
''', 'popup capture')
s = one(s,
'''        statusEl.textContent = "";
        submitBtn.disabled = true;
        submitBtn.textContent = "Enviando…";
        try {
          const result = await postNewsletter({
            email: emailEl.value.trim(),
            source: "popup",
            website: honeypotValue(document.getElementById("nl-popup-form"))
''',
'''        if (popupForm.dataset.submitting === "true") return;
        popupForm.dataset.submitting = "true";
        statusEl.textContent = "";
        submitBtn.disabled = true;
        submitBtn.textContent = "Enviando…";
        try {
          const result = await postNewsletter({
            email: emailEl.value.trim(),
            source: "popup",
            website: honeypotValue(popupForm)
''', 'popup guard')
s = one(s,
'''        } catch (err) {
          statusEl.textContent = newsletterErrorMessage(err.message);
          submitBtn.disabled = false;
          submitBtn.textContent = copy.cta;
        }
''',
'''        } catch (err) {
          delete popupForm.dataset.submitting;
          statusEl.textContent = newsletterErrorMessage(err.message);
          submitBtn.disabled = false;
          submitBtn.textContent = copy.cta;
        }
''', 'popup reset')
p.write_text(s, encoding='utf-8')

print('PR55 atomic product patch applied')

# Rol: seguridad (domingos)

Datos: `seguridad.md`, con las cabeceras de seguridad de la portada, el estado de los bots de IA en robots.txt y los ficheros versionados con nombre sensible. La auditoría semanal (`security-weekly-audit.yml`) ya cubre los workflows (zizmor), las dependencias Python (pip-audit) y los secretos de los commits (gitleaks); no repitas lo suyo.

Buscas:
- cabeceras que falten o sean débiles (HSTS, CSP, nosniff, Referrer-Policy, Permissions-Policy) y dónde se fijan (`_headers`, Worker de Cloudflare);
- ficheros que no deberían estar en un repositorio público (credenciales, bases de datos, volcados, perfiles de navegador);
- bloqueos a bots de IA o de buscadores que nos quiten visibilidad sin motivo;
- mejoras gratuitas de Cloudflare o GitHub (reglas, protección de ramas, Dependabot, secret scanning) que falten.

El repositorio es público y las issues también: si hay una credencial expuesta, la issue dice solo el fichero y que hay que revocarla. Nunca copies el valor.

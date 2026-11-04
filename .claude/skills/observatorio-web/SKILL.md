---
name: observatorio-web
description: Revisar cómo va davidportodiaz.com en Google Search Console, Bing, Ahrefs, GoatCounter, Clarity, Amazon Afiliados, Pinterest, Metricool, Brevo y GitHub Actions. Unifica datos verificados, hallazgos y mejoras priorizadas.
---

# Observatorio de davidportodiaz.com

Usar solo cuando el usuario pida una revisión global o invoque `/observatorio-web`; no cargar por defecto en otras tareas. **Modo lectura**: no publicar, cambiar cuentas, comprar, enviar emails, fusionar PR ni editar producción salvo solicitud explícita posterior.

1. Leer `docs/observatorio/README.md` y `docs/observatorio/fuentes.json`, además de las fuentes técnicas ya existentes cuando corresponda. Los estados en el JSON son **históricos/documentados**, no certifican login ni datos actuales. No asumir que un servicio sin evidencia está configurado.
2. Consultar primero GitHub Actions/PR y web pública; esos datos pueden obtenerse sin cuentas privadas. Priorizar siempre salud pública y pérdidas importantes.
3. Si hay herramienta de navegador de Claude Code, comprobar conexión con Edge mediante `/chrome` (o el mecanismo equivalente disponible); aprovechar sesiones autorizadas ya iniciadas, respetando los permisos. Si falta instalación, login, CAPTCHA o acceso, **marcar «sin verificar»** y pedir solo la intervención imprescindible. No ejecutar técnicas para extraer cookies ni crear puertos de depuración ni copiar secretos.
4. Revisar paneles disponibles agrupados: SEO (GSC, Bing, Ahrefs), comportamiento (GoatCounter, Clarity), ventas/comunidad (Amazon, Brevo, Pinterest, Metricool), operaciones (GitHub, Cloudflare, PageSpeed). No es necesario abrir todos si ya se ha detectado un P0; evitar repetir informes redundantes.
5. Para cada hallazgo registrar plataforma, métrica, fecha del dato, periodo comparable, URL/consulta concreta, evidencia observada, hipótesis y confianza. Separar datos observados de recomendaciones. No inferir ventas a partir de clics salientes ni dar por confirmado un acceso basándose en documentación antigua.
6. Cruzar señales: GSC frente a Bing/Ahrefs; tráfico de GoatCounter frente a conversiones verificadas de Amazon/Brevo; Clarity frente a QA de usabilidad; Core Web Vitals reales frente a pruebas de laboratorio. No duplicar trabajo ya cubierto por CI.
7. Entregar informe **corto y accionable**: estado general; 3 hallazgos principales; tabla de P0/P1/P2 con evidencia e impacto; bloque «sin acceso/datos no disponibles»; próximas acciones. Evitar decenas de métricas sin decisión. No proponer cambios SEO por pequeñas variaciones sin muestra.
8. Solo si el usuario lo pide, crear PR de corrección por causa general. Los informes privados pueden quedar en `.local/observatorio/` excluido de Git; jamás versionar pantallas privadas, credenciales ni métricas personales.

# Aviso desde automatizasinhumo (18-11-2026, 2.ª parte)

Corrige dos puntos del aviso anterior (PR #1462, cerrada sin fusionar).

## Harden-Runner: cuidado en repos públicos
- En un repo público, el informe de red de Harden-Runner (`step-security/harden-runner`) lo puede ver cualquiera.
- Ese informe registra cada dominio al que se conecta el trabajo. Si un job visita URLs que identifican algo privado (vistas previas de clientes, ids, tokens en el host), quedan expuestas.
- En automatizasinhumo lo señaló CodeRabbit y se retiró de la fábrica de vistas previas (PR #17 de `automatizasinhumo/automatizasinhumo-web`).
- Si se adopta aquí, solo en jobs que conecten a hosts públicos y genéricos (npm, GitHub, PyPI).

## Cola de Actions: ya no compartida
- `automatizasinhumo-web` se ha trasladado a la organización `automatizasinhumo`, con cupo de Actions propio. Ya no compite con los trabajos de web-escritor.
- Sigue valiendo la recomendación de `cancel-in-progress` en los workflows de PR, por la propia cola de web-escritor.
- Si se traslada un repo a una organización: el traslado cancela los runs en curso y apaga CodeQL (configuración por defecto) y secret scanning. Hay que reactivarlos.

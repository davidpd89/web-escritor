# =============================================================
# WIKIDATA UPDATE SCRIPT — David Porto Díaz
# Ejecutar desde cualquier PC con PowerShell
# BORRAR después de usar
# =============================================================
# INSTRUCCIONES:
#   1. Edita la línea $password abajo con tu contraseña de Wikidata
#   2. Ejecuta: powershell -ExecutionPolicy Bypass -File _wikidata_update.ps1
#   3. Borra el archivo
# =============================================================

$username = "DavidPortoDiaz"
$password = "PON_AQUI_TU_CONTRASEÑA"   # <-- EDITA ESTA LÍNEA

# Si prefieres no editarlo, puedes ejecutar así desde terminal:
#   $env:WD_PASS = "tu_contraseña"; powershell -ExecutionPolicy Bypass -File _wikidata_update.ps1
if ($env:WD_PASS) { $password = $env:WD_PASS }

$baseUrl = "https://www.wikidata.org/w/api.php"

# --- AUTH ---
Write-Host "Autenticando..."
$r1 = Invoke-WebRequest -Uri ($baseUrl + "?action=query&meta=tokens&type=login&format=json") -SessionVariable 'wdSess' -UseBasicParsing
$loginToken = ($r1.Content | ConvertFrom-Json).query.tokens.logintoken

$r2 = Invoke-WebRequest -Uri $baseUrl -Method POST `
    -Body "action=login&lgname=$([uri]::EscapeDataString($username))&lgpassword=$([uri]::EscapeDataString($password))&lgtoken=$([uri]::EscapeDataString($loginToken))&format=json" `
    -WebSession $wdSess -ContentType "application/x-www-form-urlencoded" -UseBasicParsing
$loginResult = ($r2.Content | ConvertFrom-Json).login.result
Write-Host "Login: $loginResult"

if ($loginResult -ne "Success") {
    Write-Host "ERROR: Login fallido. Verifica usuario/contraseña."
    Write-Host ($r2.Content)
    exit 1
}

# Comprobar si está bloqueado
$rInfo = Invoke-WebRequest -Uri ($baseUrl + "?action=query&meta=userinfo&uiprop=blockinfo&format=json") -WebSession $wdSess -UseBasicParsing
$uiInfo = ($rInfo.Content | ConvertFrom-Json).query.userinfo
if ($uiInfo.blockedby) {
    Write-Host "CUENTA BLOQUEADA por $($uiInfo.blockedby): $($uiInfo.blockreason)"
    Write-Host "Expira: $($uiInfo.blockexpiry)"
    Write-Host "→ Conecta desde otra red (4G, sin VPN) e inténtalo de nuevo."
    exit 1
}

$r3 = Invoke-WebRequest -Uri ($baseUrl + "?action=query&meta=tokens&format=json") -WebSession $wdSess -UseBasicParsing
$csrf = ($r3.Content | ConvertFrom-Json).query.tokens.csrftoken
Write-Host "Autenticación OK.`n"

# --- HELPERS ---
function Add-ItemClaim($entity, $property, $itemId) {
    $value = "{`"entity-type`":`"item`",`"numeric-id`":$($itemId.TrimStart('Q')),`"id`":`"$itemId`"}"
    $body = "action=wbcreateclaim&entity=$entity&snaktype=value&property=$property&value=$([uri]::EscapeDataString($value))&token=$([uri]::EscapeDataString($csrf))&format=json&errorformat=plaintext"
    $r = Invoke-WebRequest -Uri $baseUrl -Method POST -Body $body -WebSession $wdSess -ContentType "application/x-www-form-urlencoded" -UseBasicParsing
    $result = $r.Content | ConvertFrom-Json
    if ($result.error) { Write-Host "  ERROR $entity|$property|$itemId : $($result.error.code) — $($result.error.info)" }
    elseif ($result.warnings) { Write-Host "  WARN  $entity|$property|$itemId : $($result.warnings)" }
    else { Write-Host "  OK    $entity|$property|$itemId → $($result.claim.id)" }
}

function Add-StringClaim($entity, $property, $value) {
    $body = "action=wbcreateclaim&entity=$entity&snaktype=value&property=$property&value=$([uri]::EscapeDataString('"' + $value + '"'))&token=$([uri]::EscapeDataString($csrf))&format=json&errorformat=plaintext"
    $r = Invoke-WebRequest -Uri $baseUrl -Method POST -Body $body -WebSession $wdSess -ContentType "application/x-www-form-urlencoded" -UseBasicParsing
    $result = $r.Content | ConvertFrom-Json
    if ($result.error) { Write-Host "  ERROR $entity|$property|`"$value`" : $($result.error.code) — $($result.error.info)" }
    else { Write-Host "  OK    $entity|$property|`"$value`" → $($result.claim.id)" }
}

function New-WDItem($labelEs, $labelEn, $descEs, $descEn, $p31Id) {
    $data = @{
        labels = @{
            es = @{ language = "es"; value = $labelEs }
            en = @{ language = "en"; value = $labelEn }
        }
        descriptions = @{
            es = @{ language = "es"; value = $descEs }
            en = @{ language = "en"; value = $descEn }
        }
        claims = @(
            @{
                mainsnak = @{
                    snaktype = "value"
                    property = "P31"
                    datavalue = @{
                        value = @{ "entity-type" = "item"; id = $p31Id; "numeric-id" = [int]$p31Id.TrimStart('Q') }
                        type = "wikibase-entityid"
                    }
                }
                type = "statement"
                rank = "normal"
            }
        )
    } | ConvertTo-Json -Depth 10 -Compress

    $body = "action=wbeditentity&new=item&data=$([uri]::EscapeDataString($data))&token=$([uri]::EscapeDataString($csrf))&format=json"
    $r = Invoke-WebRequest -Uri $baseUrl -Method POST -Body $body -WebSession $wdSess -ContentType "application/x-www-form-urlencoded" -UseBasicParsing
    $result = $r.Content | ConvertFrom-Json
    if ($result.error) {
        Write-Host "  ERROR creando item '$labelEs': $($result.error.code) — $($result.error.info)"
        return $null
    }
    $newId = $result.entity.id
    Write-Host "  CREADO $newId — $labelEs"
    return $newId
}

# =============================================================
# PASO 1 — Crear item "Premio Letras Como Espada" (Q618779 = award)
# =============================================================
Write-Host "--- Creando item: Premio Letras Como Espada ---"
$premioQ = New-WDItem `
    "Premio Letras Como Espada" `
    "Letras Como Espada Award" `
    "premio literario español de microrrelatos" `
    "Spanish literary award for flash fiction" `
    "Q618779"

if ($premioQ) {
    # Añadir país (P17: Spain Q29)
    Add-ItemClaim $premioQ "P17" "Q29"
    # Añadir idioma (P407: Spanish Q1321)
    Add-ItemClaim $premioQ "P407" "Q1321"
}

# =============================================================
# PASO 2 — Crear item "Libros Indie" (Q2085381 = publisher)
# =============================================================
Write-Host "`n--- Creando item: Libros Indie ---"
$librosindie = New-WDItem `
    "Libros Indie" `
    "Libros Indie" `
    "editorial española independiente" `
    "Spanish independent publisher" `
    "Q2085381"

if ($librosindie) {
    Add-ItemClaim $librosindie "P17" "Q29"   # país: España
    Add-ItemClaim $librosindie "P407" "Q1321" # idioma: español
}

# =============================================================
# PASO 3 — Actualizar Q139678851 (David Porto Díaz — persona)
# =============================================================
Write-Host "`n--- Actualizando Q139678851 (David Porto Díaz) ---"
Add-ItemClaim "Q139678851" "P136" "Q119429258"  # género: portal fantasy
Add-ItemClaim "Q139678851" "P106" "Q482980"     # ocupación: autor (además de escritor)
if ($premioQ) {
    Add-ItemClaim "Q139678851" "P166" $premioQ  # premio recibido: Premio Letras Como Espada
}

# =============================================================
# PASO 4 — Actualizar Q139915381 (Samuel entre mundos — libro)
# =============================================================
Write-Host "`n--- Actualizando Q139915381 (Samuel entre mundos) ---"
Add-ItemClaim "Q139915381" "P136" "Q119429258"              # género: portal fantasy
Add-ItemClaim "Q139915381" "P136" "Q943192"                 # género: fantasía
Add-ItemClaim "Q139915381" "P495" "Q29"                     # país de origen: España
Add-StringClaim "Q139915381" "P212" "979-13-87659-77-6"    # ISBN-13
if ($librosindie) {
    Add-ItemClaim "Q139915381" "P123" $librosindie          # editorial: Libros Indie
}
if ($premioQ) {
    Add-ItemClaim "Q139915381" "P166" $premioQ              # premio recibido
}
# Año de publicación correcto (2025, no 2026 — ya está como 2026 en WD, corregir si hace falta)
# Add-StringClaim "Q139915381" "P577" "+2025-00-00T00:00:00Z"  # descomenta si quieres corregirlo

Write-Host "`n============================================="
Write-Host "SCRIPT COMPLETADO."
Write-Host "Verifica los resultados en:"
Write-Host "  https://www.wikidata.org/wiki/Q139678851"
Write-Host "  https://www.wikidata.org/wiki/Q139915381"
Write-Host "============================================="
Write-Host "RECUERDA: Borra este archivo y cambia la contraseña de Wikidata."

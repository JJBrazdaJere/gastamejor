<#
  GastaMejor - Runner de pruebas (Windows / PowerShell)
  ------------------------------------------------------------
  Levanta un servidor local, abre pruebas.html en Edge headless,
  lee el resultado y devuelve un codigo de salida:
      0 = todas pasaron
      1 = hubo fallos
      2 = no se pudo leer el resultado

  Uso:
      powershell -ExecutionPolicy Bypass -File .\tests\correr-tests.ps1
      powershell -ExecutionPolicy Bypass -File .\tests\correr-tests.ps1 -Puerto 9000

  Nota: tambien podes chequear a mano abriendo pruebas.html en el
  navegador (mismo resultado, con detalle visual).
#>
[CmdletBinding()]
param(
  [int]$Puerto = 8791,
  [string]$Edge = "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
  [int]$PresupuestoMs = 20000
)

$ErrorActionPreference = "Stop"

$raiz = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $raiz "pruebas.html"))) { throw "No se encontro pruebas.html en $raiz" }
if (-not (Test-Path $Edge)) { throw "No se encontro Microsoft Edge en: $Edge" }

function Test-PuertoLibre([int]$p) {
  try {
    $c = New-Object System.Net.Sockets.TcpClient
    $c.Connect("127.0.0.1", $p)
    $c.Close()
    return $false
  } catch {
    return $true
  }
}

$puertoElegido = $null
for ($p = $Puerto; $p -lt ($Puerto + 50); $p++) {
  if (Test-PuertoLibre $p) { $puertoElegido = $p; break }
}
if (-not $puertoElegido) { throw "No hay puerto libre cerca de $Puerto" }

$servidor = Start-Process -FilePath "python" `
  -ArgumentList @("-m", "http.server", $puertoElegido, "--bind", "127.0.0.1") `
  -WorkingDirectory $raiz -PassThru -WindowStyle Hidden

$tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("gm-tests-" + [guid]::NewGuid().ToString("N").Substring(0, 8))
New-Item -ItemType Directory -Path $tmp | Out-Null

try {
  $listo = $false
  for ($i = 0; $i -lt 40; $i++) {
    if (-not (Test-PuertoLibre $puertoElegido)) { $listo = $true; break }
    Start-Sleep -Milliseconds 250
  }
  if (-not $listo) { throw "El servidor local no arranco en el puerto $puertoElegido" }

  $url = "http://127.0.0.1:$puertoElegido/pruebas.html"
  $dump = Join-Path $tmp "dump.txt"

  # Se llama a Edge a traves de cmd para que su salida de error (stderr)
  # no rompa PowerShell 5.1.
  $cmdEdge = '"{0}" --headless=new --disable-gpu --no-first-run --user-data-dir="{1}\perfil" --virtual-time-budget={2} --dump-dom "{3}" > "{4}" 2>nul' -f $Edge, $tmp, $PresupuestoMs, $url, $dump
  & cmd.exe /c $cmdEdge | Out-Null

  $dom = [System.IO.File]::ReadAllText($dump, [System.Text.Encoding]::UTF8)
  $dom = $dom -replace '&amp;', '&' -replace '&lt;', '<' -replace '&gt;', '>' -replace '&quot;', '"' -replace '&#39;', "'"

  $bloque = [regex]::Match($dom, '(?s)<textarea id="salida-txt"[^>]*>(.*?)</textarea>')
  $salida = $bloque.Groups[1].Value

  $m = [regex]::Match($salida, 'RESUMEN\|ok=(\d+)\|fallo=(\d+)\|total=(\d+)')
  if (-not $m.Success) {
    Write-Host "No se pudo leer el resultado de las pruebas." -ForegroundColor Red
    Write-Host "Revisa el volcado en: $dump" -ForegroundColor DarkGray
    exit 2
  }

  $ok = [int]$m.Groups[1].Value
  $fallo = [int]$m.Groups[2].Value
  $total = [int]$m.Groups[3].Value

  Write-Host ""
  Write-Host "  GastaMejor - Pruebas automatizadas" -ForegroundColor Cyan
  Write-Host ("  PASS: {0}    FAIL: {1}    TOTAL: {2}" -f $ok, $fallo, $total) -ForegroundColor White
  Write-Host ""

  if ($fallo -gt 0) {
    foreach ($f in [regex]::Matches($salida, 'FALLO\|([^|]*)\|([^|]*)\|([^\r\n]*)')) {
      Write-Host ("  x  {0} :: {1}" -f $f.Groups[1].Value.Trim(), $f.Groups[2].Value.Trim()) -ForegroundColor Red
      $det = $f.Groups[3].Value.Trim()
      if ($det) { Write-Host ("       {0}" -f $det) -ForegroundColor DarkGray }
    }
    Write-Host ""
    exit 1
  }

  Write-Host "  Todas las pruebas pasaron - OK" -ForegroundColor Green
  Write-Host ""
  exit 0
}
finally {
  if ($servidor -and -not $servidor.HasExited) {
    Stop-Process -Id $servidor.Id -Force -ErrorAction SilentlyContinue
  }
  Start-Sleep -Milliseconds 200
  Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
}

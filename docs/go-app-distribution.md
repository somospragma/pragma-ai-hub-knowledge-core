# SOPP CLI — Go + Distribución

## Por qué Go para este CLI

Go compila a un binario nativo estático por plataforma — sin runtime, sin dependencias.
El pragmático instala un solo ejecutable y listo. Para el daemon de background
(el scheduler), Go tiene soporte nativo para procesos del sistema en las tres plataformas
sin necesitar librerías de terceros. Cobra + Viper son el estándar de la industria
para CLIs en Go.

---

## Stack tecnológico del CLI

| Componente | Librería | Propósito |
|---|---|---|
| Comandos | `cobra` | Estructura de comandos, flags, autocompletado |
| Config | `viper` | Lectura de auth.json, config por workspace |
| HTTP | `net/http` stdlib | Requests al Hub, sin dependencias extra |
| OAuth PKCE | `x/oauth2` | Flujo de autenticación con Cognito |
| Browser | `pkg/browser` | Abrir el browser del OS en el callback de login |
| HMAC verify | `crypto/hmac` stdlib | Verificar firma de archivos del Hub |
| Scheduler | via OS (ver abajo) | launchd · cron · Task Scheduler |
| Filesystem | `os` + `path/filepath` stdlib | Escritura de archivos nativos |
| Stack detect | `filepath.Walk` stdlib + `taxonomy.json` | Detecta stack leyendo señales del workspace contra `~/.pragma-sopp/taxonomy.json` |
| Output | `github.com/charmbracelet/lipgloss` | Colores y formato en terminal |

### Estructura del proyecto

```
sopp-cli/
├── cmd/
│   ├── root.go          ← comando raíz, inicialización de Cobra
│   ├── install.go       ← pragma-sopp install
│   ├── init.go          ← pragma-sopp init
│   ├── sync.go          ← pragma-sopp sync
│   ├── health.go        ← pragma-sopp health
│   └── uninstall.go     ← pragma-sopp uninstall
├── internal/
│   ├── auth/
│   │   ├── cognito.go   ← flujo OAuth2 PKCE
│   │   └── token.go     ← renovación de tokens
│   ├── hub/
│   │   └── client.go    ← cliente HTTP del Hub + verificación HMAC
│   ├── manifest/
│   │   └── manager.go   ← lectura/escritura de manifest.json
│   ├── renderer/
│   │   └── renderer.go  ← lee ides.json y templates de ~/.pragma-sopp/ para formatear assets sin lógica hardcodeada
│   ├── scheduler/
│   │   ├── scheduler.go ← interfaz común
│   │   ├── launchd.go   ← macOS (build tag: darwin)
│   │   ├── cron.go      ← Linux (build tag: linux)
│   │   └── wintask.go   ← Windows (build tag: windows)
│   ├── stack/
│   │   └── detector.go  ← detección de stack por archivos del workspace
│   └── workspace/
│       └── registry.go  ← gestión de workspaces registrados
├── pkg/
│   └── ui/
│       └── output.go    ← helpers de output con colores (lipgloss)
├── main.go
├── go.mod
├── go.sum
└── .goreleaser.yaml     ← config de build y distribución
```

### Build tags para el scheduler

Go permite compilar código específico por plataforma con build tags. Esto es lo que
hace que el scheduler funcione diferente en cada OS sin `if runtime.GOOS`:

```go
// internal/scheduler/launchd.go
//go:build darwin

package scheduler

import "os"

func Register(interval string) error {
    plist := buildPlist(interval)
    path := os.ExpandEnv("$HOME/Library/LaunchAgents/co.pragma.sopp.plist")
    // escribe el .plist y carga con launchctl
}

func IsRegistered() bool {
    // verifica si el plist existe y está cargado
}
```

```go
// internal/scheduler/cron.go
//go:build linux

package scheduler

func Register(interval string) error {
    // agrega entrada a crontab con `crontab -l | crontab -`
}
```

```go
// internal/scheduler/wintask.go
//go:build windows

package scheduler

func Register(interval string) error {
    // invoca schtasks.exe con /RU SYSTEM y /F (force)
}
```

---

## Estrategia de distribución — decisión final

Todo pasa por **GitHub Releases**. GoReleaser compila los binarios en cada tag y los sube ahí.
No hay S3, no hay package managers propios, no hay overhead de mantenimiento.

| Plataforma | Método | Experiencia del pragmático |
|---|---|---|
| macOS | Homebrew tap (apunta a GitHub Releases) | `brew install pragma-sopp-cli` |
| Linux | Descarga directa desde GitHub Releases | Descarga el tar.gz y lo pone en PATH |
| Windows | Descarga directa desde GitHub Releases | Descarga el `.exe` y lo ejecuta |
| Todos | `pragma-sopp-cli update` built-in | Auto-actualización sin ir a ningún lado |

---

### GoReleaser — configuración final

GoReleaser compila los binarios, los sube a GitHub Releases, **y actualiza el Homebrew tap automáticamente**.
El tap es un repo de GitHub (`pragma-org/homebrew-tap`) con una `Formula` que GoReleaser
mantiene en cada release. Tú no tocas ese archivo nunca.

```yaml
# .goreleaser.yaml
version: 2
project_name: pragma-sopp-cli

builds:
  - main: ./main.go
    binary: pragma-sopp-cli
    goos: [darwin, linux, windows]
    goarch: [amd64, arm64]
    ignore:
      - goos: windows
        goarch: arm64
    ldflags:
      - -s -w
      - -X main.version={{.Version}}
      - -X main.hubURL=https://hub.sopp.pragma.com.co
      - -X main.hubAPIKey={{.Env.SOPP_HUB_API_KEY}}

archives:
  - format: tar.gz
    format_overrides:
      - goos: windows
        format: zip
    name_template: "pragma-sopp-cli_{{ .Os }}_{{ .Arch }}"

checksum:
  name_template: "checksums.txt"
  algorithm: sha256

brews:
  - name: pragma-sopp-cli
    repository:
      owner: pragma-org
      name: homebrew-tap          # github.com/pragma-org/homebrew-tap
    homepage: https://github.com/pragma-org/sopp-cli
    description: Solving with AI — SOPP
    commit_author:
      name: pragma-bot
      email: bot@pragma.com.co
```

### Homebrew tap — lo que GoReleaser genera y mantiene

```ruby
class PragmaSoppCli < Formula
  desc "Solving with AI — SOPP"
  homepage "https://github.com/pragma-org/sopp-cli"
  version "1.2.0"

  on_macos do
    on_intel do
      url "https://github.com/pragma-org/sopp-cli/releases/download/v1.2.0/pragma-sopp-cli_darwin_amd64.tar.gz"
      sha256 "e3b0c44298fc1c149afbf4c8996fb924..."
    end
    on_arm do
      url "https://github.com/pragma-org/sopp-cli/releases/download/v1.2.0/pragma-sopp-cli_darwin_arm64.tar.gz"
      sha256 "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3..."
    end
  end

  def install
    bin.install "pragma-sopp-cli"
  end
end
```

### Experiencia por plataforma

**macOS:**
```bash
# Primera vez — una sola vez
brew tap pragma-org/tap

# Instalar
brew install pragma-sopp-cli

# Actualizar cuando haya nueva versión
brew upgrade pragma-sopp-cli
```

**Linux:**
```bash
# Descargar desde GitHub Releases
curl -L https://github.com/pragma-org/sopp-cli/releases/latest/download/pragma-sopp-cli_linux_amd64.tar.gz | tar xz
sudo mv pragma-sopp-cli /usr/local/bin/

# O usar el auto-update del CLI
pragma-sopp-cli update
```

**Windows:**
```
1. Ir a https://github.com/pragma-org/sopp-cli/releases/latest
2. Descargar pragma-sopp-cli_windows_amd64.zip
3. Extraer y agregar al PATH
```

---

### GitHub Action — release automático

```yaml
# .github/workflows/release.yaml
name: Release

on:
  push:
    tags: ['v*']

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-go@v5
        with:
          go-version: stable

      - uses: goreleaser/goreleaser-action@v6
        with:
          version: latest
          args: release --clean
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          HOMEBREW_TAP_TOKEN: ${{ secrets.HOMEBREW_TAP_TOKEN }}
          SOPP_HUB_API_KEY: ${{ secrets.SOPP_HUB_API_KEY }}
```

Cada `git tag v1.x.x` → GoReleaser compila → sube a GitHub Releases → actualiza el tap → listo.

---

## API Key — estrategia de distribución

La API Key **no se descarga del Hub**. Se embebe en el binario en tiempo de compilación via `ldflags`. El secret `SOPP_HUB_API_KEY` vive en Azure DevOps y se pasa a GoReleaser al compilar. Si la key se compromete, el equipo de plataforma la rota en la IaC (Terraform actualiza el Usage Plan de API Gateway), genera un nuevo tag del CLI con la key nueva, y el scheduler de cada pragmático descarga la actualización automáticamente via `pragma-sopp-cli update`.

El Hub client en Go manda la key en cada request sin excepción:

```go
// internal/hub/client.go
func (c *Client) do(req *http.Request) (*http.Response, error) {
    req.Header.Set("x-api-key", c.apiKey)
    if c.accessToken != "" {
        req.Header.Set("Authorization", "Bearer "+c.accessToken)
    }
    return c.http.Do(req)
}
```

El `auth.json` local guarda el `signing_key` (de `GET /config`) pero **no** la API Key — esa está en el binario.

---

---

## Auto-update check en sync

El CLI verifica si hay una versión nueva en cada sync sin bloquear el flujo principal:

```go
// En cmd/sync.go, al inicio, en una goroutine
go func() {
    latest, err := hub.CheckCLIVersion(currentVersion)
    if err != nil { return }
    if latest.IsNewer(currentVersion) {
        ui.PrintUpdateAvailable(latest.Version)
    }
}()
// El sync continúa mientras el check corre en paralelo
```

Output al final del sync si hay actualización disponible:

```
✓ Sync completo · 2 actualizados · versión 2.4.0

💡 Nueva versión del CLI disponible: 1.2.0 → 1.3.0
   macOS:  brew upgrade pragma-sopp-cli
   Otros:  pragma-sopp-cli update
```

---

## Comando update + endpoint en el Hub

El CLI se actualiza a sí mismo desde GitHub Releases:

```
$ pragma-sopp-cli update

Verificando actualizaciones...
  Versión actual:     1.1.0
  Versión disponible: 1.2.0

¿Actualizar? [s/N]
> s

Descargando pragma-sopp-cli 1.2.0 para darwin/arm64...
Verificando checksum SHA-256...  ✓
Reemplazando binario en /usr/local/bin/pragma-sopp-cli...
✓ Actualizado a 1.2.0
```

El Hub expone un endpoint liviano para el check de versión:

```
GET /cli/version
→ 200 { "latest": "1.3.0", "minimum": "1.0.0" }
```

Si la versión del CLI es menor que `minimum`, el sync falla con mensaje claro pidiendo
actualización. Esto permite deprecar versiones viejas de forma controlada sin tocar
nada en el cliente.
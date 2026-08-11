# Locator Confidence Scoring

Cada locator descubierto recibe un score 0-100 que indica qué tan robusto se espera que sea ante cambios de la app. El score se persiste en `.evidence/locators-discovered.json` y se inyecta como comentario en el Page Object cuando es bajo, para que el agente de self-healing en runtime tenga contexto.

## Tabla base

| Estrategia | Condición | Score |
|---|---|---|
| `resource-id` | Único en la pantalla, con package prefix válido | 95–100 |
| `content-desc` | Único en la pantalla, no vacío, ≥3 caracteres | 80–90 |
| `resource-id` | No único en la pantalla (varios elementos comparten id) | 60–70 |
| `text` | Corto (≤30 chars), único en pantalla, sin caracteres especiales | 50–65 |
| `xpath` con atributos | Combinación `class` + 1 atributo discriminante | 30–50 |
| `xpath` posicional | Con índices `[1]/[2]` o paths largos | 10–30 |

## Modificadores (+/− al score base)

| Factor | Delta |
|---|---|
| Locator contiene texto i18n probable (palabras detectables en lenguaje natural) | −10 |
| Locator está dentro de un `RecyclerView`/lista dinámica | −15 |
| Locator depende de estado (`@selected`, `@focused`) | −20 (forzar score < 30) |
| Elemento tiene `accessibilityId` redundante con `resource-id` | +5 (más estable por doble identidad) |
| `resource-id` sin package prefix (`@+id/foo`) | −5 |
| Locator es el único candidato disponible para ese elemento | −0 (no penaliza, pero marca `single_candidate: true`) |

Aplicar modificadores secuencialmente. Clamp final a `[0, 100]`.

## Bandas de decisión

| Score | Banda | Acción en el Page Object |
|---|---|---|
| 90–100 | `STABLE` | Emitir locator sin comentarios extra. |
| 70–89 | `SOLID` | Emitir locator, agregar fallback en `.evidence`. |
| 50–69 | `ACCEPTABLE` | Emitir + comentario `// SELF_HEAL_FALLBACK_AVAILABLE`. |
| 30–49 | `FRAGILE` | Emitir + comentario `// HEALING_CANDIDATE: low confidence (score=X)`. Incluir 2 fallbacks. |
| 0–29 | `UNRELIABLE` | Emitir + comentario `// HEALING_REQUIRED: verify with Appium Inspector before relying`. Forzar 3 fallbacks. Si todos los locators del elemento están aquí, marcar pantalla completa como `needs_manual_review`. |

## Inyección como comentario en Java

Ejemplo de Page Object generado:

```java
public class LoginPage {

    // STABLE (score=98)
    public static final By LOGIN_BUTTON =
        AppiumBy.id("com.example.app:id/login_button");

    // ACCEPTABLE (score=62) — SELF_HEAL_FALLBACK_AVAILABLE
    public static final By REMEMBER_ME_CHECKBOX =
        AppiumBy.xpath("//android.widget.CheckBox[@text='Recordarme']");

    // FRAGILE (score=42) — HEALING_CANDIDATE: low confidence
    // fallback 1: AppiumBy.accessibilityId("Iconos sociales")
    // fallback 2: AppiumBy.xpath("//*[@resource-id='com.example.app:id/social_row']/*[2]")
    public static final By GOOGLE_LOGIN_ICON =
        AppiumBy.xpath("//android.widget.LinearLayout[2]/android.widget.ImageView[1]");
}
```

## Reporte agregado al usuario

Al final del crawl, calcular distribución y reportar:

```
Auto-discovery completado:
  - Pantallas descubiertas: 14
  - Locators emitidos: 87
  - STABLE (90+): 52 (60%)
  - SOLID (70-89): 18 (21%)
  - ACCEPTABLE (50-69): 9 (10%)
  - FRAGILE (30-49): 6 (7%)
  - UNRELIABLE (0-29): 2 (2%)
  
  Pantallas con todos los locators < 50:
    - SettingsScreen (3 elementos sin resource-id ni content-desc)
  
  Recomendación: revisar SettingsScreen con Appium Inspector antes de correr smoke.
```

## Trigger para fallback a deferred-locators

Si ocurre cualquiera de estos:

- **>50% de locators emitidos están en banda UNRELIABLE** (score <30).
- **>30% de las pantallas descubiertas tienen todos sus locators en banda FRAGILE o peor**.
- **El locator de la pantalla raíz (la primera tras splash) está en banda UNRELIABLE**.

Reportar al usuario:

```
Auto-discovery encontró mayormente locators frágiles para esta app. 
Recomiendo cambiar a deferred-locators y revisar selectores con Appium Inspector.
¿Quieres (a) seguir con los locators auto-descubiertos igualmente, o (b) descartarlos y usar deferred-locators?
```

NUNCA decidir unilateralmente — la decisión final es del usuario.

## Persistencia del score

En `.evidence/locators-discovered.json` cada entrada tiene `primary.score` y cada `fallbacks[].score`. Adicionalmente, persistir un resumen en `.evidence/locators-summary.json`:

```json
{
  "total_locators": 87,
  "distribution": {
    "stable": 52,
    "solid": 18,
    "acceptable": 9,
    "fragile": 6,
    "unreliable": 2
  },
  "screens_needing_manual_review": ["SettingsScreen"],
  "average_score": 78.3,
  "trigger_fallback_to_deferred": false
}
```

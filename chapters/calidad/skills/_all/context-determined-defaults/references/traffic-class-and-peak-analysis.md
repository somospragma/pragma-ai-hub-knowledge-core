# Traffic Class y Peak Analysis

Define cómo medir la clase de tráfico real de un sistema para derivar VUs, stages y thresholds de k6 (`[[k6-thresholds-three-tiers]]`).

## Fuentes de datos

Las fuentes son universales — el calendario de picos cambia por sector pero el **método** no:

- **APM**: Datadog, NewRelic, Dynatrace, AppDynamics, Honeycomb, Elastic APM. Métricas: requests/sec, latency P50/P95/P99, error rate.
- **Web analytics**: Google Analytics 4, Adobe Analytics, Matomo. Sirve para frontend; menos preciso para backend pero útil cuando no hay APM.
- **Logs del balanceador o gateway**: ALB/NLB (AWS), Cloud Load Balancing (GCP), Front Door / Application Gateway (Azure), nginx logs, API Gateway access logs.
- **CDN**: CloudFront, Cloudflare, Fastly, Akamai — peak por minuto, geografía, top URLs.
- **Métricas de mensajería**: Kafka consumer lag, SQS `ApproximateNumberOfMessagesVisible`, RabbitMQ queue depth.

## Métricas a extraer

- **Peak QPS por endpoint crítico** — no global. Un endpoint `/health` con 1M QPS no significa que `/checkout` reciba lo mismo.
- **Distribución diaria** — heatmap por hora del día y día de la semana. Define ventana de tests destructivos (off-peak).
- **Distribución mensual / anual** — estacionalidad.
- **Razón peak / mean** — sistemas con razón 10x necesitan auto-scaling probado; sistemas con razón 1.5x pueden dimensionar para peak constante.
- **Burst rate (peak por segundo dentro de un minuto)** — algunos sistemas reciben todo el peak en 5 segundos (lanzamiento de venta de boletos), no distribuido.

## Estacionalidad — universal, no por sector

El método para detectar y modelar picos estacionales es universal. Lo que cambia es el calendario por cliente. Ejemplos no exhaustivos:

- **Retail / e-commerce**: Black Friday, Cyber Monday, Navidad, Día de la Madre/Padre, San Valentín, Hot Sale, Buen Fin, regreso a clases.
- **Banca / fintech**: días de pago (15 y 30), cierre de mes, día de declaración de impuestos, vencimiento de tarjetas.
- **Streaming / media**: estrenos, finales deportivas, eventos en vivo, eclipses, elecciones.
- **Edu / LMS**: inicio de semestre, semanas de exámenes, día de admisión.
- **Travel / hospitality**: vacaciones de verano, fin de año, semana santa, puentes festivos locales.
- **Gobierno**: cierre fiscal, ventanas de subsidios, elecciones, días de pago de pensión.
- **Gaming**: lanzamientos, eventos de temporada, doble XP weekend, drops de NFT/skins.
- **Salud**: temporada de gripe, campañas de vacunación, días de turno alto en urgencias.
- **Manufactura / supply chain**: cierre de planta, inventarios, alta de proveedores.

**El sector no determina el método** — el método siempre es: medir histórico, identificar picos, dimensionar el test para 1.5x el peak histórico (margen de crecimiento).

## Derivación: peak QPS real → VUs/stages de k6

Fórmula simplificada (asumiendo `think time` = 0 y request promedio):

```
VUs ≈ peak_QPS × avg_response_time_sec
```

Ejemplo: si peak es 500 QPS y la response promedio es 200ms → VUs ≈ 100.

Stages recomendados:

- **Ramp-up**: 25% del tiempo del test, llegando a 100% de VUs target.
- **Steady**: 50% del tiempo del test al 100% VUs.
- **Spike opcional**: 10% del tiempo a 150% VUs (validar burst).
- **Ramp-down**: 15% del tiempo bajando a 0.

Cuando hay burst (todo en 5s), modelar con `arrival-rate` executor en k6, no con VUs constantes.

## Antipatrones

- Usar VUs arbitrarios ("100 VUs porque sí") sin derivarlos del peak real.
- Promediar peak con valle: oculta los picos donde el sistema falla.
- Asumir distribución uniforme cuando hay burst — el sistema colapsa en burst y los tests no lo detectan.
- Ignorar la geografía: peak en LATAM ≠ peak en EU; el test desde una sola región subestima latencia para usuarios remotos.
- No revalidar peak cada trimestre — el tráfico crece y los thresholds quedan desactualizados.

// {{project_name}} — shared/thresholds.js
// Thresholds centralizados por tier (Conservative / Moderate / Relaxed) y por escenario.
//
// Tiers (ver [[k6-thresholds-three-tiers]] y [[k6-threshold-tier-justification]]):
//   - Conservative: SLAs estrictos, sistemas criticos (banca, salud).
//   - Moderate:     default, sistemas productivos estandar.
//   - Relaxed:      MVP, sistemas nuevos sin baseline, batch internos.
//
// Por escenario:
//   - thresholdsBaseline: SLAs estrictos, baseline limpio bajo carga minima.
//   - thresholdsCarga:    SLAs nominales bajo carga sostenida (100% peak).
//   - thresholdsEstres:   SLAs relajados, foco en no caer y degradar controladamente.

// === Tiers genericos ===
export const tiers = {
  Conservative: {
    http_req_duration: ['p(95)<500',  'p(99)<1000'],
    http_req_failed:   ['rate<0.001'],
    checks:            ['rate>0.99'],
  },
  Moderate: {
    http_req_duration: ['p(95)<1000', 'p(99)<2000'],
    http_req_failed:   ['rate<0.01'],
    checks:            ['rate>0.95'],
  },
  Relaxed: {
    http_req_duration: ['p(95)<2000', 'p(99)<5000'],
    http_req_failed:   ['rate<0.05'],
    checks:            ['rate>0.90'],
  },
};

// === Por escenario ===
// Por default todos heredan de Moderate. Ajustar segun tier declarado en .evidence/tier-declared.md.
export const thresholdsBaseline = {
  http_req_duration: ['p(95)<800',  'p(99)<1500'],
  http_req_failed:   ['rate<0.005'],
  checks:            ['rate>0.98'],
};

export const thresholdsCarga = {
  http_req_duration: ['p(95)<1000', 'p(99)<2000'],
  http_req_failed:   ['rate<0.01'],
  checks:            ['rate>0.95'],
};

export const thresholdsEstres = {
  http_req_duration: ['p(95)<2000', 'p(99)<5000'],
  http_req_failed:   ['rate<0.05'],
  checks:            ['rate>0.90'],
};

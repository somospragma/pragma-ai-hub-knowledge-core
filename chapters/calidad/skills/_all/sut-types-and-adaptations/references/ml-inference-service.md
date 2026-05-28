# ML Inference Service — Patrones y Adaptación

## Principio

Testear un servicio de ML no es solo testear el endpoint HTTP. El **modelo** es parte del SUT y requiere ángulos de prueba propios: comportamiento, fairness, robustness, drift. El endpoint REST/gRPC se testea como cualquier otro, pero el modelo detrás cambia las garantías y los criterios de aceptación.

## Patrones canónicos

- **Model behavior testing**: invariance tests (rotación, sinónimos, paráfrasis no cambian la predicción), directional tests (cambios de input mueven el output en la dirección esperada), minimum functionality tests (casos críticos siempre se predicen bien). Marco: CheckList (Ribeiro et al.).
- **Fairness**: validar paridad de métricas (false positive rate, equal opportunity) entre subgrupos demográficos. Herramientas: Aequitas, Fairlearn, IBM AIF360.
- **Robustness adversarial**: pequeñas perturbaciones del input no deben cambiar la predicción para casos no maliciosos; y el modelo debe resistir ataques conocidos (FGSM, PGD). Herramientas: Foolbox, Adversarial Robustness Toolbox (ART), CleverHans.
- **Drift detection**: input drift (distribución de features cambia), concept drift (relación X→y cambia), prediction drift (distribución de outputs cambia). Herramientas: Evidently AI, Alibi Detect, NannyML, WhyLabs.
- **Determinismo**: para el mismo input + misma seed + misma versión de modelo, el output debe ser idéntico. Validar en tests.
- **A/B testing en producción**: shadow deploy, canary, multi-armed bandit. Tests no reemplazan A/B; A/B no reemplaza tests.

## Frameworks primarios

- **Karate** sobre el endpoint HTTP si el servicio es REST (la mayoría de inferencias online lo son). gRPC si el servicio es de baja latencia interno.
- **Deepchecks** o **Great Expectations** para model behavior y data validation pre-inference.
- **Locust / k6** para perf — la unidad típica es `requests/sec` con P95/P99 de latencia y, en GPU, **memory headroom**.

## Complementarios

- **Foolbox / ART** para adversarial.
- **Aequitas / Fairlearn** para fairness.
- **Evidently AI** para drift y monitoring continuo.
- **MLflow / Weights & Biases** para tracking y comparación de versiones del modelo.
- **NVIDIA DCGM exporter** para métricas GPU (memoria, utilización, temperatura) que k6 puede correlacionar.

## Patrón canónico: latencia y GPU memory

- P95 < SLA (típicamente 50-200ms para online inference).
- P99 < 2x SLA.
- GPU memory peak < 80% del disponible (margen para batch coalescing).
- Throughput estable durante 30 min sin memory leak (validar con repeated stress).

## Modelo behavior test (ejemplo con Deepchecks)

```python
from deepchecks.tabular.checks import RegressionErrorDistribution, ModelInferenceTime

ModelInferenceTime().run(test_dataset, model)  # falla si p95 > threshold
RegressionErrorDistribution().run(test_dataset, model)
```

## Antipatrones

- Testear solo el endpoint HTTP (status 200, schema OK) sin validar el comportamiento del modelo.
- Asumir que un modelo que pasó tests offline funciona en producción sin drift monitoring.
- Ignorar fairness porque "no es regulatorio" — la falta de fairness aparece como issue de marca o demanda meses después.
- No versionar el dataset de validación junto al modelo — los resultados no son reproducibles.
- Medir latencia sin separar warm-up (primera inferencia carga el modelo a GPU, es atípica).

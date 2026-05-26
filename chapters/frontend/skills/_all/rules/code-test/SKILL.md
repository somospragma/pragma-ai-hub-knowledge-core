---
id: frontend-skill-code-test
version: "1.0"
scope: chapter
type: skill
chapter: frontend
name: code-test
description: Reglas para pruebas unitarias frontend con Jest, Vitest y Karma. Activar siempre que se genere o modifique código de tests.
trigger: always_on
type: rule
---

Cada vez que te pida realizar pruebas unitarias debes seguir estas reglas:

# Reglas para pruebas unitarias Frontend

## Objetivo

Generar pruebas unitarias confiables, legibles y mantenibles que validen el comportamiento del sistema, no su implementación interna. Estas reglas aplican sin importar la librería de testing.

## 0. Detección de librería de testing

Antes de escribir cualquier test, detecta qué herramientas usa el proyecto:

- jest: jest.config.* existe OR "jest" en package.json → usar jest.fn(), jest.spyOn(), jest.mock()
- vitest: vitest.config.* existe OR "vitest" en package.json → usar vi.fn(), vi.spyOn(), vi.mock()
- karma/jasmine: karma.conf.* existe OR @angular-devkit/build-angular → usar jasmine.createSpy(), jasmine.createSpyObj()
- testing_library: @testing-library/react o @testing-library/angular → complemento, no runner

NUNCA mezcles APIs de distintas librerías en un mismo archivo de test.

## 1. Principios fundamentales

- Probar comportamiento, no implementación.
- Cada test debe validar una sola responsabilidad.
- Las pruebas deben ser claras, determinísticas y fáciles de entender.
- Evitar tests frágiles que se rompan por cambios internos irrelevantes.

## 2. Estructura — Patrón AAA

Utilizar Arrange/Act/Assert en TODOS los tests sin excepción.

## 3. Convenciones de naming

- Usar: should + acción + resultado esperado
- Agrupar con describe por unidad funcional
- Un describe por clase/componente/hook, it por comportamiento

## 4. Mocks y dependencias

- Mockear TODAS las dependencias externas
- NO usar implementaciones reales en unit tests
- Preferir inyección de dependencias

## 5. Testing de componentes

React: usar queries por accesibilidad (getByRole > getByLabelText > getByText), preferir userEvent sobre fireEvent, NO usar container.querySelector
Angular: mockear servicios con createSpyObj, llamar fixture.detectChanges() después de cambiar datos, para signals mutar → detectChanges → assert

## 6. Anti-patrones a evitar

- Tests que dependen de tiempo real → usar fake timers
- Lógica compleja en el test → separar en tests individuales
- Probar detalles internos → testear outputs públicos
- Mockear todo incluido el SUT → mockear solo dependencias

## 7. Cobertura inteligente

- NO buscar 100% de coverage ciego
- Priorizar lógica de negocio, edge cases, caminos críticos
- Ignorar archivos de configuración, barrel exports, routing puro

## 8. Reglas para IA

- NO generar tests innecesarios o redundantes
- SIEMPRE validar comportamiento esperado + manejo de errores
- SIEMPRE mockear dependencias externas
- NUNCA generar un test que pase con implementación vacía

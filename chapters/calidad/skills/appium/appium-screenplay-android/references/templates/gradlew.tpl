# Este archivo NO se mantiene a mano.
#
# `gradlew` (script bash) y `gradlew.bat` (script batch para Windows) deben
# generarse ejecutando:
#
#   gradle wrapper --gradle-version 8.10
#
# en la raiz del proyecto recien scaffoldeado, antes de cualquier otra cosa.
# Esto produce:
#
#   gradlew                              (bash, debe quedar 0755)
#   gradlew.bat                          (batch)
#   gradle/wrapper/gradle-wrapper.jar    (binario)
#   gradle/wrapper/gradle-wrapper.properties  (ver gradle-wrapper.properties.tpl)
#
# Reglas:
#   - El agente DEBE correr `chmod +x gradlew` despues de generar el wrapper.
#     Sin esto, el health-check del workflow falla con "Permission denied" en
#     la primera invocacion ./gradlew. Ver [[appium-health-check-pipeline]] y
#     el acceptance criteria #5 del skill.
#   - El distribution URL fijado debe coincidir con `gradle-wrapper.properties.tpl`
#     (Gradle 8.10). NO regenerar wrapper con otra version.
#   - Si el agente NO puede ejecutar shell, deja un TODO destacado en el README:
#       > "Antes de correr ./gradlew, ejecutar: gradle wrapper --gradle-version 8.10
#       >  && chmod +x gradlew"
#   - NO commitear `gradle/wrapper/gradle-wrapper.jar` manualmente — debe venir
#     de la version oficial 8.10 (el comando `gradle wrapper` lo descarga).
#
# Resumen: este `.tpl` es una NOTA, no el script. El script real lo emite
# Gradle, no el generador.

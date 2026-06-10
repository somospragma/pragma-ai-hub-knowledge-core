plugins {
    id 'java'
}

sourceCompatibility = 21
targetCompatibility = 21

repositories {
    mavenCentral()
}

dependencies {
    // src/main/java/co/com/pragma/... vive la capa Screenplay (tasks, questions,
    // interactions, userinterfaces). Esas clases necesitan Serenity + Appium en
    // compileJava, por lo que TIENEN que estar en `implementation`.
    // Mover cualquiera de estas a testImplementation rompe la compilacion del
    // modulo principal con "cannot find symbol".
    implementation 'net.serenity-bdd:serenity-core:4.1.14'
    implementation 'net.serenity-bdd:serenity-cucumber:4.1.14'
    implementation 'net.serenity-bdd:serenity-screenplay:4.1.14'
    implementation 'net.serenity-bdd:serenity-screenplay-webdriver:4.1.14'
    implementation 'io.appium:java-client:8.6.0'
    implementation 'org.slf4j:slf4j-api:2.0.9'
    implementation 'ch.qos.logback:logback-classic:1.4.14'

    // src/test usa runners JUnit Platform + Cucumber + asserts. NO mover a
    // implementation (no aplican al main source set).
    testImplementation 'io.cucumber:cucumber-junit-platform-engine:7.14.0'
    testImplementation 'org.junit.platform:junit-platform-suite:1.10.2'
    testImplementation 'org.junit.jupiter:junit-jupiter:5.10.2'
    testImplementation 'org.assertj:assertj-core:3.24.2'

    // Lombok solo en compile-time, sin runtime overhead.
    compileOnly 'org.projectlombok:lombok:1.18.30'
    annotationProcessor 'org.projectlombok:lombok:1.18.30'
}

test {
    // OBLIGATORIO useJUnitPlatform() para Cucumber JUnit Platform 7.14.0.
    // NO usar useJUnit() — corresponde a JUnit 4 y rompe el runner de Cucumber.
    useJUnitPlatform()
    systemProperties System.getProperties()
}

// serenity-gradle-plugin auto-registra la tarea `aggregate` (y `reports`, `clean`).
// NUNCA redefinir esas tareas con `task aggregate { ... }` ni
// `tasks.register('aggregate') { ... }` — colision garantizada en Gradle 8.x.
// Si necesitas personalizar, usar `tasks.named('aggregate') { ... }`.
apply plugin: 'net.serenity-bdd.serenity-gradle-plugin'

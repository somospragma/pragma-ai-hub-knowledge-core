{
  "name": "{{project_name}}",
  "version": "1.0.0-SNAPSHOT",
  "description": "K6 performance suite for {{project_name}}",
  "private": true,
  "scripts": {
    "smoke":  "k6 run tests/smoke-test.js",
    "load":   "k6 run tests/load-test.js",
    "stress": "k6 run tests/stress-test.js",
    "spike":  "k6 run tests/spike-test.js",
    "soak":   "k6 run tests/soak-test.js",
    "all":    "bash run-all.sh"
  },
  "devDependencies": {}
}

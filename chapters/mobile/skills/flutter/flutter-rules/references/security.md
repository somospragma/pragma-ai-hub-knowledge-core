# Flutter Rules — Security

Source: Mobile Flutter Developer Rules v1.0 — Domain: Security

## Data and Credentials

- Validate and sanitize all user input and external data.
- Protect credentials and sensitive data; never expose them in code or insecure storage.
- Use secure mechanisms for credential storage.
- Use strong encryption for required data at rest and in transit.
- Compilation environment variables must be stored as secrets in CI/CD or specialized secret management services.
- Do not log or display sensitive data in logs, error messages, or public interfaces.

## Communications

- Use secure communication (HTTPS/TLS) for all connections.
- Prevent common vulnerabilities (XSS, CSRF, code injection, clickjacking).

## Authorization and Dependencies

- Implement access controls and authorization on the backend.
- Keep dependencies and libraries updated and free of known vulnerabilities.
- Prevent threats listed in OWASP Mobile Application Security 2024.

## Release Builds

- Apply minification and obfuscation for release builds, not debug.
- Generate mapping files for each build to de-obfuscate stack traces.
- Generate a list and exclusion criteria for code that must not be obfuscated (code with reflection, dynamic invocations, third-party libraries, methods called from native must retain their name and signature).
- Validate build obfuscation by de-obfuscating and reading the mapping file.
- Compare build size before and after optimization to quantify the reduction.
- Disable verbose DEBUG logs in production builds.

## Error Handling

- Handle errors and exceptions without exposing internal or sensitive information.

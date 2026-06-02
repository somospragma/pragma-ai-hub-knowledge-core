# Flutter Rules — Traceability

Source: Mobile Flutter Developer Rules v1.0 — Domain: Traceability

## Error Handling

- Always implement controlled error handling that does not interrupt system operation.
- Use try-catch blocks and appropriate error boundaries for the technology.
- Use custom error types or factories.
- Avoid ignoring exceptions in a try/catch.
- Use typed exceptions that semantically describe the problem.
- Do not explicitly throw the `Exception` object; create descriptive subclasses.
- Use sealed classes to implement Either and Optional.
- Use the Result pattern (Success-Failure) to explicitly handle errors.

## Logs and Monitoring

- Implement a remote monitoring service to identify errors in real time.
- Use log classification correctly when debugging errors (Info, Warning, Error, Debug).
- Avoid exposing sensitive information in logs or internal error messages.
- Do not use `print` to debug the application; use the official `developer` package.
- Use remote monitoring tools like Crashlytics or Sentry according to official documentation.

## User Feedback

- Provide clear and understandable feedback to the user when an error occurs. The user must not perceive unhandled errors.
- Do not use technical language in user-facing feedback messages.
- In BLoC, differentiate alerts (non-blocking) from modals (blocking).

## Null Data

- Properly validate null values using Dart's null-aware operators (`?`, `??`, `!`).
- Define default values when mapping objects from external data sources to avoid null data errors.

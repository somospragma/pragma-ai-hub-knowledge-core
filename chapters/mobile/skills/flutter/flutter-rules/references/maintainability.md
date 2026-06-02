# Flutter Rules — Maintainability

Source: Mobile Flutter Developer Rules v1.0 — Domain: Maintainability

## Architecture

- Use clean architecture patterns that allow separation of concerns.
- Organize code into layers independent of frameworks, databases, and external interfaces.
- Centralize business logic without creating direct dependencies on other layers.
- Establish dependency rules from the outermost layers toward the innermost layers. Inner layers must not know about outer layers.
- Maintain high cohesion and low coupling between layers.
- Depend on abstractions (interfaces or abstract classes), not on concrete implementations.
- Use dependency injection strategies to favor testability.
- Avoid unnecessary dependencies.
- Clean architecture: 3 layers — presentation, domain, data.
- Repository depends on a datasource abstraction.
- UseCase depends on a Repository abstraction.
- BloC or Provider depends on a UseCase abstraction.
- One BLoC per use case, without filtering UI events in the domain layer.
- Dependency injection manager via `get_it`.
- Build environment configuration via Flavors and Schemes.
- Add a README explaining dependency rules.
- Centralized labels and configuration for internationalization.
- Data models and states must be immutable; all properties must be `final`.
- The Domain layer must be pure Dart, with no Flutter dependencies.
- Fixed package versions in `pubspec.yaml`; use ranges only for well-maintained packages.
- Data models must include `copyWith`, `fromJson`, and `toJson` methods, preferably using code generation tools.
- Repositories must be the single source of data access and abstract all data sources.
- A BLoC or Cubit must only depend on use case abstractions (UseCase) from the Domain layer; it must never access a repository directly.
- Implement dependencies only for the development build.
- Implement the `flutter_lints` dependency.
- Integrate suggested rules in the `analysis_options.yaml` file.
- Validate the analysis rules execution with `flutter analyze`.
- Generate automatic fixes with: `dart fix --apply`.
- Use custom configuration for linters and static code analysis.

## Clean Code and Readability

- Write readable, simple, and self-documenting code.
- Code must be an asset, not a liability.
- Use clear, descriptive, and consistent names for variables, functions, and classes.
- Keep functions and methods short, with a single responsibility.
- Avoid code duplication; reuse functions and components.
- Document code concisely: comments only if they explain what is not obvious.
- Remove dead, unnecessary, or unused code.
- Prefer simple, readable structures over complex or "clever" ones.
- Follow the language's style conventions (indentation, spaces, etc.).
- Refactor periodically to improve readability and maintainability.
- All code must satisfy SOLID principles.
- Variable names in `camelCase`.
- Class names in `PascalCase`.
- File names in `snake_case`.
- Indentation equivalent to 2 spaces.
- Conditionals and loops wrapped with `{ }`.
- Documentation of classes and methods with complex logic using `///`.
- Include `///` comments for public API and minimal examples.
- Do not use magic values: define all constants in a centralized location.
- Never leave commented-out code; it must be removed before merging.
- All commits must follow the Conventional Commits specification.
- Unit tests must follow the Arrange-Act-Assert (AAA) pattern.
- Validate coding rules and style guides as needed by the project.

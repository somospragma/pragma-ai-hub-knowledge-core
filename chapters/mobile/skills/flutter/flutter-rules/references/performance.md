# Flutter Rules — Performance

Source: Mobile Flutter Developer Rules v1.0 — Domain: Performance

## Images and Assets

- Optimize images using modern formats (WebP, AVIF).
- Optimize images using WebP and SVG.

## Loading and Rendering

- Implement Skeleton UI during resource loading.
- Avoid blocking the main thread with long-running tasks or expensive processing.
- Use lazy loading to defer views that are not immediately required.
- Load widgets lazily using `ListView.builder`, `GridView.builder`, and `PageView.builder`.
- Avoid using `shrinkWrap` in lazy-loading widgets.

## Widgets

- Use `const` whenever possible to avoid unnecessary widget rebuilds.
- Use the `Container` widget only when three or more unique attributes or properties are required.
- Do not use `Container` for empty spaces; use `SizedBox.shrink`.
- Avoid rebuilds (`setState`, BloC, Riverpod) high in the widget tree; push them to leaf nodes.
- Prefer `StatelessWidget`; use `StatefulWidget` for animations, forms, etc.
- Use `ValueNotifier` over `setState` in `StatefulWidget`.

## Resources and Memory

- Always release unused resources.
- If using controllers (`StreamController`, `TextEditingController`, etc.), call `dispose()` when closing the view.
- Use Isolates to parallelize blocking tasks.

## Tools and Configuration

- Use monitoring tools to measure performance per platform.
- Use environment variables to define compile-time constants to improve Tree Shaking.
- Use DevTools to monitor performance and detect resource management issues.
- Avoid unnecessary access to external services or local databases.

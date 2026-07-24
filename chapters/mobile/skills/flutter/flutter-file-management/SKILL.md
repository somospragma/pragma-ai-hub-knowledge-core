---
id: flutter-file-management
version: 1.2.0
scope: stack
type: skill
chapter: mobile
stack: [flutter]
name: flutter-file-management
description: >
  Handles file operations in Flutter: pick, read/write, download with progress, upload, share, and manage app storage directories. Includes OWASP MASVS-STORAGE security requirements: internal-only storage for sensitive files, path traversal prevention, MIME validation, and no sensitive data in external/shared storage. Use this skill when implementing file picker, document download, file upload, file sharing, or any local file I/O.
---
# File Management

See the reference files for complete patterns and code examples.

## Package Status (April 2026)

| Package | Version | Purpose |
|---|---|---|
| **file_picker** | 8.x | Pick files from device (all platforms) |
| **path_provider** | 2.x | App-sandboxed directory paths |
| **share_plus** | 10.x | Share files via OS share sheet |
| **open_filex** | 4.x | Open files with native app |
| **dio** | 5.x | Download/upload with progress |
| **file_saver** | 0.x | Save files to Downloads folder |
| **mime** | 2.x | MIME type detection and validation |

---

## OWASP MASVS-STORAGE Security Requirements

These are **mandatory** — not optional — for any app handling files.

| Control | Requirement | Level |
|---|---|---|
| **MASVS-STORAGE-1** | Sensitive files stored only in app internal sandbox | L1 |
| **MASVS-STORAGE-2** | Sensitive files encrypted at rest (KeyStore/Keychain key) | L2 |
| **MASVS-STORAGE-1** | No sensitive data written to external/shared storage | L1 |
| **MASVS-PLATFORM-2** | Files shared via FileProvider (Android) — never raw paths | L1 |
| **MASVS-CODE-4** | Validate MIME type and extension before processing | L1 |
| **MASVS-CODE-4** | Prevent path traversal — sanitize all file names | L1 |

### The three rules you must always apply

**Rule 1 — Internal storage only (MASVS-STORAGE-1)**
```dart
✅ getApplicationDocumentsDirectory()  — internal sandbox, app-private
✅ getApplicationSupportDirectory()    — internal sandbox, app-private
❌ getExternalStorageDirectory()       — world-readable on Android < 10
❌ /sdcard/, /storage/emulated/0/      — never write sensitive data here
```

**Rule 2 — Sanitize filenames with `path.basename()` (MASVS-CODE-4)**
```dart
// ❌ Path traversal vulnerability — user controls ../../../etc/passwd
final file = File('${dir.path}/$userInput');

// ✅ Strip directory components before using any user-supplied name
String sanitizeFileName(String name) =>
    path.basename(name).replaceAll(RegExp(r'[^\w\s\-.]'), '_').trim();
final file = File(path.join(dir.path, sanitizeFileName(userInput)));
```

**Rule 3 — Validate MIME type from file bytes, not just extension (MASVS-CODE-4)**
```dart
// ❌ Extension is easily spoofed — rename malware.exe to report.pdf
if (file.path.endsWith('.pdf')) { /* unsafe */ }

// ✅ Check magic bytes — PDF always starts with %PDF (0x25 0x50 0x44 0x46)
Future<bool> isValidPdf(File file) async {
  final bytes = await file.openRead(0, 4).first;
  return bytes.length >= 4 &&
      bytes[0] == 0x25 && bytes[1] == 0x50 &&
      bytes[2] == 0x44 && bytes[3] == 0x46;
}
```

**Rule 4 — Share via FileProvider, never raw paths (MASVS-PLATFORM-2)**
```dart
// ✅ share_plus handles FileProvider internally on Android
await SharePlus.instance.shareXFiles([XFile(file.path)]);

// ❌ Never expose raw internal paths via Intent — FileProvider required
```

---

## Download with Progress

The `CancelToken` is required for download/upload so the user can cancel in-flight operations:

```dart
final cancelToken = CancelToken();

// Stream<double> progress so BLoC can emit progress states
Stream<double> downloadFile(String url, String fileName) async* {
  final dir = await getApplicationDocumentsDirectory();
  final sanitized = sanitizeFileName(fileName);
  final savePath = path.join(dir.path, sanitized);

  await _dio.download(
    url,
    savePath,
    cancelToken: cancelToken,             // ← required
    onReceiveProgress: (received, total) {
      if (total > 0) andield received / total;
    },
  );
}
```

---

## Architecture Integration

```
Presentation (BLoC)
  ↓
Domain (UseCase → FileRepository interface)
  ↓
Data (FileRepositoryImpl)
  └── FileDataSource
        ├── FilePicker (pick)
        ├── Dio (download/upload)
        ├── dart:io File (read/write)
        └── SharePlus (share)
```

All dependencies injected via GetIt + Injectable.
Errors returned as `Either<FileFailure, T>` using fpdart.

---

## Quick Wins Checklist

- [ ] All sensitive files written to `getApplicationDocumentsDirectory()` — never external
- [ ] File names sanitized with `path.basename()` before use
- [ ] MIME type validated from file bytes (not just extension)
- [ ] Allowed extensions whitelist enforced in `file_picker`
- [ ] Max file size enforced before processing
- [ ] `share_plus` used for sharing — never raw file paths via Intent
- [ ] Temp files cleaned up in `finally` blocks
- [ ] Download progress exposed via `Stream<double>` to BLoC
- [ ] Upload uses `FormData` with `CancelToken` for cancellation

## Reference Files

- `references/file_operations.md` — pick, read, write, delete, path safety, MIME validation
- `references/download_upload.md` — Dio download with progress, upload with progress, cancellation
- `references/share_open.md` — share_plus, open_filex, file_saver, FileProvider

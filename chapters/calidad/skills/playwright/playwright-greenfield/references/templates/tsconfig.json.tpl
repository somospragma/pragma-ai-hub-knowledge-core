{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020", "dom", "dom.iterable"],
    "strict": true,
    "noImplicitAny": true,
    "strictNullChecks": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "resolveJsonModule": true,
    "baseUrl": ".",
    "paths": {
      "@pages/*": ["pages/*"],
      "@fixtures/*": ["fixtures/*"],
      "@mocks/*": ["mocks/*"],
      "@utils/*": ["utils/*"],
      "@data/*": ["data/*"]
    }
  },
  "include": [
    "tests/**/*",
    "pages/**/*",
    "fixtures/**/*",
    "mocks/**/*",
    "utils/**/*",
    "data/**/*",
    "playwright.config.ts"
  ],
  "exclude": ["node_modules", "test-results", "playwright-report", ".auth"]
}

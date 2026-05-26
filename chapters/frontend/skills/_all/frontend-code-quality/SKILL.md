---
id: frontend-skill-frontend-code-quality
version: "1.0"
scope: chapter
type: skill
chapter: frontend
name: frontend-code-quality
description: Frontend code quality patterns, anti-patterns detection, and clean component design. Use when asked to "review code", "find anti-patterns", "improve code quality", "refactor", "code smells", "clean components", or "dead code".
license: MIT
metadata:
  author: pragma-frontend-code-quality
  version: "1.0"
  reference: "Clean Code, SOLID principles applied to frontend components"
---

# Frontend Code Quality — Complete Knowledge Base

Anti-pattern detection, code smells, component design principles, and quality enforcement for Angular and React/Next.js applications.

---

## CQ1 — God Components (Anti-Pattern)

Components that do too many things — too many responsibilities, too many lines, too many state variables.

```typescript
// ❌ God Component — 400+ lines, handles everything
function UserDashboard() {
  const [user, setUser] = useState(null);
  const [orders, setOrders] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [settings, setSettings] = useState({});
  const [isEditing, setIsEditing] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  // ... 15 more state variables

  useEffect(() => { /* fetch user */ }, []);
  useEffect(() => { /* fetch orders */ }, []);
  useEffect(() => { /* fetch notifications */ }, []);
  useEffect(() => { /* fetch settings */ }, []);
  // ... 10 more effects

  const handleUpdateProfile = () => { /* 30 lines */ };
  const handleFilterOrders = () => { /* 20 lines */ };
  const handleNotificationClick = () => { /* 15 lines */ };
  // ... 10 more handlers

  return (
    <div>
      {/* 200+ lines of JSX mixing tabs, forms, lists, modals */}
    </div>
  );
}

// ✅ Decomposed into focused components
function UserDashboard() {
  const { activeTab, setActiveTab } = useTabs('overview');

  return (
    <DashboardLayout>
      <TabNavigation active={activeTab} onChange={setActiveTab} />
      <TabContent tab={activeTab}>
        <TabPanel value="overview"><UserOverview /></TabPanel>
        <TabPanel value="orders"><OrdersPanel /></TabPanel>
        <TabPanel value="notifications"><NotificationsPanel /></TabPanel>
        <TabPanel value="settings"><SettingsPanel /></TabPanel>
      </TabContent>
    </DashboardLayout>
  );
}
```

### Detection Rules

| Signal | Threshold | Action |
|--------|-----------|--------|
| Lines of code | >250 LOC | Split into sub-components |
| useState calls | >5 | Extract custom hook or sub-components |
| useEffect calls | >3 | Extract into custom hooks |
| Props count | >7 | Use composition or context |
| Responsibilities | >1 | Apply Single Responsibility Principle |

---

## CQ2 — Prop Drilling (Anti-Pattern)

Passing props through multiple layers of components that don't use them.

```typescript
// ❌ Prop drilling — theme passed through 4 levels
function App() {
  const [theme, setTheme] = useState('light');
  return <Layout theme={theme} setTheme={setTheme} />;
}
function Layout({ theme, setTheme }) {
  return <Sidebar theme={theme} setTheme={setTheme} />;
}
function Sidebar({ theme, setTheme }) {
  return <ThemeToggle theme={theme} setTheme={setTheme} />;
}
function ThemeToggle({ theme, setTheme }) {
  return <button onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')} />;
}

// ✅ React Context for cross-cutting concerns
const ThemeContext = createContext<ThemeContextType | null>(null);

function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useTheme must be used within ThemeProvider');
  return context;
}

function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const toggle = useCallback(() => setTheme(t => t === 'light' ? 'dark' : 'light'), []);
  return (
    <ThemeContext.Provider value={{ theme, toggle }}>
      {children}
    </ThemeContext.Provider>
  );
}

// Components access directly — no drilling
function ThemeToggle() {
  const { theme, toggle } = useTheme();
  return <button onClick={toggle}>{theme}</button>;
}

// ✅ Angular — services + inject()
@Injectable({ providedIn: 'root' })
export class ThemeService {
  readonly theme = signal<'light' | 'dark'>('light');
  toggle() { this.theme.update(t => t === 'light' ? 'dark' : 'light'); }
}

@Component({ /* ... */ })
export class ThemeToggleComponent {
  private readonly themeService = inject(ThemeService);
  readonly theme = this.themeService.theme;
  toggle() { this.themeService.toggle(); }
}

// ✅ Composition pattern (no context needed)
function App() {
  return (
    <Layout>
      <Layout.Sidebar>
        <ThemeToggle /> {/* Gets its own data */}
      </Layout.Sidebar>
    </Layout>
  );
}
```

### When to Use Each Solution

| Scenario | Solution |
|----------|----------|
| 2 levels deep | Props are fine — don't over-engineer |
| 3+ levels deep | Context (React) or Service (Angular) |
| Cross-cutting concern (theme, auth, i18n) | Context/Service |
| Specific subtree only | Composition pattern |
| Global state (cart, user session) | State management library |

---

## CQ3 — useEffect Misuse (React Anti-Pattern)

Using `useEffect` for things that don't need it — derived state, event handlers, data transformations.

```typescript
// ❌ useEffect for derived state
function ProductList({ products, category }: Props) {
  const [filtered, setFiltered] = useState(products);

  useEffect(() => {
    setFiltered(products.filter(p => p.category === category));
  }, [products, category]);
  // This is a synchronous derivation — not a side effect!

  return <>{filtered.map(p => <ProductCard key={p.id} product={p} />)}</>;
}

// ✅ Derive during render — no effect needed
function ProductList({ products, category }: Props) {
  const filtered = useMemo(
    () => products.filter(p => p.category === category),
    [products, category]
  );
  return <>{filtered.map(p => <ProductCard key={p.id} product={p} />)}</>;
}

// ❌ useEffect to handle events
function Form() {
  const [submitted, setSubmitted] = useState(false);
  useEffect(() => {
    if (submitted) {
      sendAnalytics('form_submitted');
      showToast('Success!');
    }
  }, [submitted]);

  return <form onSubmit={() => setSubmitted(true)} />;
}

// ✅ Handle in the event handler directly
function Form() {
  const handleSubmit = () => {
    sendAnalytics('form_submitted');
    showToast('Success!');
  };
  return <form onSubmit={handleSubmit} />;
}

// ❌ useEffect to sync parent state
function Child({ onChange }: { onChange: (v: string) => void }) {
  const [value, setValue] = useState('');
  useEffect(() => {
    onChange(value); // Triggers parent re-render in effect → cascade
  }, [value, onChange]);
}

// ✅ Call onChange in event handler
function Child({ onChange }: { onChange: (v: string) => void }) {
  const [value, setValue] = useState('');
  const handleChange = (v: string) => {
    setValue(v);
    onChange(v); // Synchronous, no cascade
  };
}
```

### Valid useEffect Uses

| Use Case | Valid? | Alternative |
|----------|--------|-------------|
| Fetch data on mount | ✅ Yes (or use TanStack Query) | Server Components, loader |
| Subscribe to external store | ✅ Yes (or `useSyncExternalStore`) | — |
| Set up event listeners | ✅ Yes | — |
| Derived/computed state | ❌ No | `useMemo` or inline calculation |
| Respond to user events | ❌ No | Event handler |
| Sync state to parent | ❌ No | Event handler callback |
| Transform data for display | ❌ No | `useMemo` or derive in render |

---

## CQ4 — Memory Leaks

```typescript
// ❌ Memory leak — no cleanup on unmount
function LiveData() {
  const [data, setData] = useState(null);
  useEffect(() => {
    const ws = new WebSocket('wss://api.example.com/live');
    ws.onmessage = (e) => setData(JSON.parse(e.data));
    // Missing cleanup! WebSocket stays open after unmount
  }, []);
}

// ✅ Always clean up subscriptions
function LiveData() {
  const [data, setData] = useState(null);
  useEffect(() => {
    const ws = new WebSocket('wss://api.example.com/live');
    ws.onmessage = (e) => setData(JSON.parse(e.data));
    return () => ws.close(); // ✅ Cleanup
  }, []);
}

// ❌ Memory leak — stale closure updates unmounted component
function SearchResults({ query }: { query: string }) {
  const [results, setResults] = useState([]);
  useEffect(() => {
    fetchResults(query).then(setResults); // Component may have unmounted!
  }, [query]);
}

// ✅ Use AbortController
function SearchResults({ query }: { query: string }) {
  const [results, setResults] = useState([]);
  useEffect(() => {
    const controller = new AbortController();
    fetchResults(query, { signal: controller.signal })
      .then(setResults)
      .catch((e) => {
        if (e.name !== 'AbortError') throw e;
      });
    return () => controller.abort(); // ✅ Cancel on unmount/re-run
  }, [query]);
}

// ❌ Memory leak — event listener not removed
function ScrollTracker() {
  useEffect(() => {
    const handler = () => console.log(window.scrollY);
    window.addEventListener('scroll', handler);
    // Missing removeEventListener!
  }, []);
}

// ✅ Remove event listeners
function ScrollTracker() {
  useEffect(() => {
    const handler = () => console.log(window.scrollY);
    window.addEventListener('scroll', handler);
    return () => window.removeEventListener('scroll', handler); // ✅
  }, []);
}

// ❌ Angular — memory leak with manual subscriptions
export class DataComponent implements OnInit {
  ngOnInit() {
    this.dataService.getData().subscribe(data => {
      this.data = data; // Subscription lives forever!
    });
  }
}

// ✅ Angular — use takeUntilDestroyed or async pipe
export class DataComponent {
  private readonly destroyRef = inject(DestroyRef);
  readonly data = toSignal(this.dataService.getData());

  // OR if you need manual subscription:
  ngOnInit() {
    this.dataService.getData()
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(data => this.data = data);
  }
}
```

---

## CQ5 — Dead Code & Unused Exports

```typescript
// ❌ Dead code signals
// 1. Unused imports
import { useState, useReducer, useContext } from 'react'; // useReducer never used

// 2. Unreachable code
function process(status: 'active' | 'inactive') {
  if (status === 'active') return handleActive();
  if (status === 'inactive') return handleInactive();
  return handleUnknown(); // Unreachable — TS should catch with exhaustive check
}

// 3. Commented-out code left in production
// function oldHandler() { ... } // TODO: remove after migration

// 4. Unused exports
export function legacyTransform() { /* no imports found anywhere */ }

// 5. Feature flags that are always on/off
if (FEATURE_FLAGS.newDashboard) { /* always true for 6 months */ }

// ✅ Detection tools
// ESLint rules:
// "no-unused-vars": "error"
// "no-unreachable": "error"
// "@typescript-eslint/no-unused-vars": "error"
// "@typescript-eslint/no-unused-imports": "error"  (TS 5.4+)

// Find unused exports:
// npx ts-prune
// npx knip (comprehensive — finds unused files, deps, exports)
```

---

## CQ6 — Component Design Principles

### Single Responsibility Components

```typescript
// ❌ Mixed responsibilities
function UserCard({ user }: { user: User }) {
  const [isFollowing, setIsFollowing] = useState(false);
  const handleFollow = async () => {
    await api.followUser(user.id);  // Data fetching
    setIsFollowing(true);
    trackEvent('follow', user.id);  // Analytics
  };
  return (
    <div>
      <img src={user.avatar} />    {/* Presentation */}
      <h3>{user.name}</h3>
      <button onClick={handleFollow}>Follow</button>
    </div>
  );
}

// ✅ Separated concerns
// Container — handles logic
function UserCardContainer({ userId }: { userId: string }) {
  const user = useUser(userId);
  const { follow, isFollowing } = useFollowUser(userId);
  return <UserCard user={user} isFollowing={isFollowing} onFollow={follow} />;
}

// Presentational — pure UI
function UserCard({ user, isFollowing, onFollow }: UserCardProps) {
  return (
    <div>
      <img src={user.avatar} alt={user.name} />
      <h3>{user.name}</h3>
      <button onClick={onFollow}>{isFollowing ? 'Following' : 'Follow'}</button>
    </div>
  );
}
```

### Composition Over Configuration

```typescript
// ❌ Configuration explosion
<DataTable
  columns={columns}
  data={data}
  sortable
  filterable
  paginated
  searchable
  exportable
  selectable
  expandable
  stickyHeader
  virtualScroll
  // 20+ boolean props
/>

// ✅ Composable API
<DataTable data={data}>
  <DataTable.Header sticky>
    <DataTable.Search />
    <DataTable.Export formats={['csv', 'pdf']} />
  </DataTable.Header>
  <DataTable.Body>
    <DataTable.Column field="name" sortable />
    <DataTable.Column field="email" filterable />
    <DataTable.Column field="status" render={StatusBadge} />
  </DataTable.Body>
  <DataTable.Pagination pageSize={20} />
</DataTable>
```

---

## CQ7 — Naming Conventions

```typescript
// ❌ Bad naming
const d = new Date();                  // Cryptic abbreviation
const handleClick = () => {};          // Generic — click on what?
const data = await fetch('/users');    // "data" says nothing
const flag = true;                     // Flag for what?
const UserComp = () => {};             // Don't abbreviate "Component"
const processStuff = () => {};         // Vague verb + vague noun

// ✅ Descriptive, consistent naming
const createdAt = new Date();
const handleFollowUser = () => {};
const users = await fetchUsers();
const isMenuOpen = true;
const UserProfile = () => {};
const validateEmailFormat = () => {};

// ✅ Naming conventions by type
// Components: PascalCase, noun or noun phrase
UserProfile, OrderList, PaymentForm, NavigationSidebar

// Hooks: camelCase, starts with "use"
useAuth, useDebounce, useLocalStorage, useIntersectionObserver

// Event handlers: camelCase, starts with "handle" or "on"
handleSubmit, handleToggleMenu, onUserSelect

// Booleans: starts with is/has/should/can
isLoading, hasPermission, shouldRedirect, canEdit

// Constants: UPPER_SNAKE_CASE
MAX_RETRY_COUNT, API_BASE_URL, DEFAULT_PAGE_SIZE

// Files:
// Components: PascalCase — UserProfile.tsx, OrderList.tsx
// Hooks: camelCase — useAuth.ts, useDebounce.ts
// Utils: camelCase — formatDate.ts, validateEmail.ts
// Types: PascalCase — UserTypes.ts or user.types.ts
// Tests: same name + .test or .spec — UserProfile.test.tsx
```

---

## CQ8 — Error Boundaries & Error Handling

```typescript
// ❌ No error handling — app crashes
function ProductPage() {
  const { data } = useQuery({ queryKey: ['product'], queryFn: fetchProduct });
  return <div>{data.name}</div>; // Crashes if data is undefined
}

// ✅ React Error Boundary
class ErrorBoundary extends Component<Props, State> {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    reportError(error, info); // Send to monitoring
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback ?? <DefaultErrorUI error={this.state.error} />;
    }
    return this.props.children;
  }
}

// ✅ Granular error boundaries (not one for the whole app)
function App() {
  return (
    <ErrorBoundary fallback={<FullPageError />}>
      <Header />
      <ErrorBoundary fallback={<SidebarError />}>
        <Sidebar />
      </ErrorBoundary>
      <ErrorBoundary fallback={<ContentError />}>
        <MainContent />
      </ErrorBoundary>
    </ErrorBoundary>
  );
}

// ✅ Angular — ErrorHandler
@Injectable()
export class GlobalErrorHandler implements ErrorHandler {
  handleError(error: unknown): void {
    const resolvedError = error instanceof Error ? error : new Error(String(error));
    reportError(resolvedError);
    // Show user-friendly notification
  }
}
```

---

## CQ9 — Code Consistency Checks

| Area | Rule | Example |
|------|------|---------|
| **Imports** | Consistent ordering | External → Internal → Relative → Styles |
| **Exports** | Named exports preferred | `export function X` not `export default` |
| **Files** | One component per file | Not 3 components in one file |
| **Types** | Types in separate file or co-located | `types.ts` or at top of component file |
| **Styles** | One approach per project | CSS Modules OR Tailwind OR styled-components — not mixed |
| **State** | One state lib per project | Zustand OR Redux OR Jotai — not mixed |
| **Fetching** | One fetching lib per project | TanStack Query OR SWR — not mixed |
| **Forms** | One form lib per project | React Hook Form OR Formik — not mixed |
| **Testing** | Consistent test patterns | AAA (Arrange-Act-Assert) everywhere |

---

## Quick Reference — Code Quality Checklist

| Category | Check | Severity |
|----------|-------|----------|
| **God Components** | No component exceeds 250 LOC | HIGH |
| **God Components** | No component has >5 useState calls | HIGH |
| **God Components** | No component has >3 useEffect calls | HIGH |
| **Prop Drilling** | No props passed through >2 intermediate layers | MEDIUM |
| **Prop Drilling** | Cross-cutting concerns use Context/Service | MEDIUM |
| **useEffect** | No derived state in useEffect | HIGH |
| **useEffect** | No event handling in useEffect | HIGH |
| **useEffect** | All effects have cleanup when needed | CRITICAL |
| **Memory Leaks** | Subscriptions cleaned up on unmount | CRITICAL |
| **Memory Leaks** | Fetch requests use AbortController | HIGH |
| **Memory Leaks** | Event listeners removed on unmount | CRITICAL |
| **Dead Code** | No unused imports or variables | MEDIUM |
| **Dead Code** | No commented-out code in production | MEDIUM |
| **Dead Code** | No unreachable code branches | MEDIUM |
| **Components** | Single responsibility per component | HIGH |
| **Components** | Composition over configuration | MEDIUM |
| **Naming** | Descriptive, consistent naming conventions | HIGH |
| **Naming** | Boolean vars use is/has/should prefix | MEDIUM |
| **Errors** | Error boundaries around major sections | HIGH |
| **Errors** | Graceful error states (not blank screens) | HIGH |
| **Consistency** | One library per concern (state, forms, fetch) | MEDIUM |
| **Consistency** | Consistent import ordering | LOW |
| **Consistency** | Named exports preferred over default | LOW |

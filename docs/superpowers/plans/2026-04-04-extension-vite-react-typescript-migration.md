# Extension Vite React TypeScript Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the Chrome extension on Vite, React, and TypeScript while preserving the current auth and summarize behavior and adding explicit dev/prod build configuration.

**Architecture:** Introduce an extension-local Vite build pipeline that owns popup bundling, TypeScript script compilation, and environment-aware manifest output. Keep the current runtime responsibilities intact by moving popup behavior into a React app, keeping auth orchestration in the background script, and keeping YouTube page extraction in the content script.

**Tech Stack:** Vite, React, TypeScript, Chrome Extension Manifest V3, optional Vitest and React Testing Library for targeted frontend tests

---

## File Structure Map

- Create: `apps/extension/package.json`
- Create: `apps/extension/tsconfig.json`
- Create: `apps/extension/tsconfig.node.json`
- Create: `apps/extension/vite.config.ts`
- Create: `apps/extension/manifest.config.ts` or `apps/extension/scripts/build-manifest.mjs`
- Create: `apps/extension/index.html`
- Create: `apps/extension/src/popup/main.tsx`
- Create: `apps/extension/src/popup/App.tsx`
- Create: `apps/extension/src/popup/popup.css`
- Create: `apps/extension/src/background.ts`
- Create: `apps/extension/src/content.ts`
- Create: `apps/extension/src/config/env.ts`
- Create: `apps/extension/src/types/runtime.ts`
- Create: `apps/extension/src/lib/chrome.ts`
- Create: `apps/extension/src/lib/api.ts`
- Create: `apps/extension/src/lib/auth.ts`
- Create: `apps/extension/src/vite-env.d.ts`
- Create: `apps/extension/tests/popup/App.test.tsx`
- Modify: `package.json`
- Modify or replace: `apps/extension/manifest.json`
- Delete after migration verification: `apps/extension/src/background.js`
- Delete after migration verification: `apps/extension/src/content.js`
- Delete after migration verification: `apps/extension/src/popup/popup.js`
- Delete after migration verification: `apps/extension/src/popup/popup.html`

### Task 1: Stand Up The Extension Toolchain

**Files:**
- Create: `apps/extension/package.json`
- Create: `apps/extension/tsconfig.json`
- Create: `apps/extension/tsconfig.node.json`
- Create: `apps/extension/vite.config.ts`
- Create: `apps/extension/index.html`
- Create: `apps/extension/src/vite-env.d.ts`
- Modify: `package.json`

- [ ] **Step 1: Add the failing build contract**

Define the desired extension-local scripts in `apps/extension/package.json` and root script wiring in `package.json`:

```json
{
  "scripts": {
    "dev": "vite build --watch --mode development",
    "build": "vite build --mode production",
    "test": "vitest run"
  }
}
```

Expected initial state: these scripts cannot run yet because Vite, React, and TypeScript config do not exist.

- [ ] **Step 2: Add TypeScript and Vite config**

Create `tsconfig.json`, `tsconfig.node.json`, and `vite.config.ts` with multi-entry support for:

- popup HTML entry
- background script entry
- content script entry

Initial Vite config should copy icons from `assets/`, emit deterministic filenames for MV3 use, and write output to an extension `dist/` directory.

- [ ] **Step 3: Add the popup HTML shell**

Create `apps/extension/index.html` with a root element and a script tag pointing to `src/popup/main.tsx`.

- [ ] **Step 4: Install and verify the toolchain**

Run: `pnpm --dir apps/extension install`

Run: `pnpm --dir apps/extension build`

Expected: build starts but still fails on missing app/runtime source files until later tasks are completed.

- [ ] **Step 5: Commit**

```bash
git add package.json apps/extension/package.json apps/extension/tsconfig.json apps/extension/tsconfig.node.json apps/extension/vite.config.ts apps/extension/index.html apps/extension/src/vite-env.d.ts
git commit -m "build: scaffold extension vite toolchain"
```

### Task 2: Add Environment And Manifest Generation

**Files:**
- Create: `apps/extension/src/config/env.ts`
- Create: `apps/extension/manifest.config.ts` or `apps/extension/scripts/build-manifest.mjs`
- Modify or replace: `apps/extension/manifest.json`
- Modify: `apps/extension/vite.config.ts`

- [ ] **Step 1: Write the failing config expectations**

Create a small config helper contract like:

```ts
export type ExtensionEnv = "development" | "production";

export const ENV: ExtensionEnv;
export const API_BASE_URL: string;
export const IS_PRODUCTION: boolean;
```

Expected failure: the rest of the app cannot import these values yet.

- [ ] **Step 2: Implement environment selection**

Use Vite mode or injected environment variables so:

- development targets `http://localhost:8000`
- production targets the production API origin

Keep the values centralized in `src/config/env.ts`.

- [ ] **Step 3: Generate environment-aware manifest output**

Implement a manifest generation layer that outputs the correct values for:

- `host_permissions`
- `oauth2.client_id`
- `name` if a dev suffix is desired

The build should produce the correct manifest for each mode instead of checking environment at runtime inside extension code.

- [ ] **Step 4: Verify both outputs**

Run: `pnpm --dir apps/extension build`

Run: `pnpm --dir apps/extension build --mode development`

Expected: both builds emit a valid MV3 manifest with mode-specific values.

- [ ] **Step 5: Commit**

```bash
git add apps/extension/src/config/env.ts apps/extension/vite.config.ts apps/extension/manifest.json apps/extension/manifest.config.ts apps/extension/scripts/build-manifest.mjs
git commit -m "build: add extension env-aware manifest generation"
```

### Task 3: Define Shared Runtime Types And Utilities

**Files:**
- Create: `apps/extension/src/types/runtime.ts`
- Create: `apps/extension/src/lib/chrome.ts`
- Create: `apps/extension/src/lib/api.ts`
- Create: `apps/extension/src/lib/auth.ts`

- [ ] **Step 1: Write the shared message and auth types**

Define explicit types for:

- auth state
- runtime request message union
- runtime response shapes
- video context payload
- summarize request/response payloads

Example:

```ts
export type RuntimeMessage =
  | { type: "AUTH_GET_STATE" }
  | { type: "AUTH_SIGN_IN" }
  | { type: "AUTH_SIGN_OUT" }
  | { type: "GET_VIDEO_CONTEXT" };
```

- [ ] **Step 2: Extract helper wrappers**

Add typed wrappers for:

- `chrome.runtime.sendMessage`
- `chrome.tabs.sendMessage`
- backend fetch calls

This keeps React and script files thin.

- [ ] **Step 3: Add focused tests for pure helpers**

Create small tests for any pure config or payload normalization helpers.

Run: `pnpm --dir apps/extension test`

Expected: helper-level tests pass even before the full popup is migrated.

- [ ] **Step 4: Commit**

```bash
git add apps/extension/src/types/runtime.ts apps/extension/src/lib/chrome.ts apps/extension/src/lib/api.ts apps/extension/src/lib/auth.ts apps/extension/tests
git commit -m "refactor: add shared extension runtime types"
```

### Task 4: Rewrite The Popup In React And TypeScript

**Files:**
- Create: `apps/extension/src/popup/main.tsx`
- Create: `apps/extension/src/popup/App.tsx`
- Create or modify: `apps/extension/src/popup/popup.css`
- Delete later: `apps/extension/src/popup/popup.js`
- Delete later: `apps/extension/src/popup/popup.html`

- [ ] **Step 1: Write the failing popup test**

Create a component test that covers the signed-out state:

```tsx
it("shows the sign-in prompt when no auth state is available", async () => {
  render(<App />);
  expect(await screen.findByText(/sign in with google/i)).toBeInTheDocument();
});
```

- [ ] **Step 2: Run the popup test to verify failure**

Run: `pnpm --dir apps/extension test -- App.test.tsx`

Expected: FAIL because the popup app has not been implemented yet.

- [ ] **Step 3: Implement the React popup**

Port current popup behavior into React state:

- initial auth-state refresh
- sign-in flow
- sign-out flow
- summarize flow
- loading and error UI

Keep the same visible behaviors unless a small UI cleanup is required by the rewrite.

- [ ] **Step 4: Verify the popup test passes**

Run: `pnpm --dir apps/extension test -- App.test.tsx`

Expected: PASS

- [ ] **Step 5: Verify the popup build**

Run: `pnpm --dir apps/extension build`

Expected: popup assets compile and are referenced correctly from the extension output.

- [ ] **Step 6: Commit**

```bash
git add apps/extension/src/popup/main.tsx apps/extension/src/popup/App.tsx apps/extension/src/popup/popup.css apps/extension/tests/popup/App.test.tsx apps/extension/index.html
git commit -m "feat: migrate extension popup to react"
```

### Task 5: Migrate Background Auth Logic To TypeScript

**Files:**
- Create: `apps/extension/src/background.ts`
- Delete later: `apps/extension/src/background.js`
- Modify: `apps/extension/src/types/runtime.ts`
- Modify: `apps/extension/src/lib/auth.ts`

- [ ] **Step 1: Port the current background flow**

Move the existing logic into TypeScript while preserving:

- `AUTH_GET_STATE`
- `AUTH_SIGN_IN`
- `AUTH_SIGN_OUT`
- Google callback parsing
- backend token exchange
- auth storage persistence

- [ ] **Step 2: Tighten response typing**

Ensure all background message handlers return typed success/error payloads rather than ad hoc objects.

- [ ] **Step 3: Verify extension build**

Run: `pnpm --dir apps/extension build`

Expected: background script compiles without JS fallback files.

- [ ] **Step 4: Manual runtime check**

Load the unpacked built extension in Chrome and verify:

- background script loads
- sign-in button triggers the auth flow
- auth state is persisted after popup reopen

- [ ] **Step 5: Commit**

```bash
git add apps/extension/src/background.ts apps/extension/src/types/runtime.ts apps/extension/src/lib/auth.ts
git commit -m "feat: migrate extension background to typescript"
```

### Task 6: Migrate Content Script To TypeScript

**Files:**
- Create: `apps/extension/src/content.ts`
- Delete later: `apps/extension/src/content.js`
- Modify: `apps/extension/src/types/runtime.ts`

- [ ] **Step 1: Port the content script directly**

Move the current video-context extraction into TypeScript and keep the same message contract for `GET_VIDEO_CONTEXT`.

- [ ] **Step 2: Verify the extension build**

Run: `pnpm --dir apps/extension build`

Expected: content script is emitted and referenced correctly in the manifest output.

- [ ] **Step 3: Manual page check**

Load a YouTube watch page and verify the popup can still retrieve:

- `videoId`
- current page URL
- page title

- [ ] **Step 4: Commit**

```bash
git add apps/extension/src/content.ts apps/extension/src/types/runtime.ts
git commit -m "feat: migrate extension content script to typescript"
```

### Task 7: Remove Legacy Assets And Finalize Scripts

**Files:**
- Delete: `apps/extension/src/background.js`
- Delete: `apps/extension/src/content.js`
- Delete: `apps/extension/src/popup/popup.js`
- Delete: `apps/extension/src/popup/popup.html`
- Modify: `package.json`
- Modify: `apps/extension/package.json`

- [ ] **Step 1: Remove obsolete source files**

Delete the legacy plain JavaScript popup/background/content files once the Vite-based extension build is verified.

- [ ] **Step 2: Finalize root commands**

Update root scripts so the extension has clear developer entrypoints, for example:

```json
{
  "scripts": {
    "dev:extension": "pnpm --dir apps/extension dev",
    "build:extension": "pnpm --dir apps/extension build",
    "test:extension": "pnpm --dir apps/extension test"
  }
}
```

- [ ] **Step 3: Run final verification**

Run: `pnpm --dir apps/extension build`

Run: `pnpm --dir apps/extension test`

Manual:

- load dev build in Chrome
- sign in
- summarize a YouTube video
- sign out
- verify a production build emits production manifest values

Expected: all checks pass and there are no remaining references to the legacy plain-JS entrypoints.

- [ ] **Step 4: Commit**

```bash
git add package.json apps/extension/package.json apps/extension/src apps/extension/manifest.json
git commit -m "refactor: finalize extension vite migration"
```

## Notes For The Implementer

- Preserve the current extension-to-API request and response shapes.
- Keep route/origin configuration centralized; do not reintroduce hardcoded URLs in popup or background code.
- Prefer direct, typed wrappers over adding unnecessary abstraction layers.
- Be careful with MV3 output naming and manifest paths because hashed defaults can break extension loading if not controlled.
- If Chrome auth behavior differs after the migration, verify the generated manifest first before changing auth logic.

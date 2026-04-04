# Extension Vite React TypeScript Migration Design

## Summary

Migrate the Chrome extension from a plain JavaScript Manifest V3 folder into a Vite-based React and TypeScript application. Keep the current extension behavior intact while replacing the frontend/build foundation with a modern, maintainable stack that supports explicit development and production configuration.

## Goals

- Move the extension onto Vite for local development and production builds.
- Rewrite the popup UI in React and TypeScript.
- Migrate background and content scripts to TypeScript.
- Introduce an explicit environment/config boundary for development and production.
- Preserve the current auth and summarize behavior during the rewrite.

## Non-Goals

- Redesign the product UX beyond what is needed to support the migration.
- Change the backend API contract used by the extension.
- Add new user-facing features during the migration.
- Introduce broader monorepo tooling changes outside the extension unless required by the new build.

## Current State

The extension currently lives as a plain MV3 folder under `apps/extension` with:

- `manifest.json` containing hardcoded permissions, localhost host permissions, and OAuth client metadata
- `src/popup/popup.js` containing DOM-driven popup behavior and hardcoded API base URL
- `src/background.js` containing Google auth flow, auth persistence, and hardcoded API base URL
- `src/content.js` responsible for YouTube page context extraction

There is no extension-specific package manifest, bundler, TypeScript setup, or environment-aware build pipeline today.

## Recommended Approach

Perform a one-shot rewrite of the extension onto `Vite + React + TypeScript`, while preserving the existing runtime behavior and extension-to-API contract.

This is preferable to an incremental bridge because:

- the extension frontend surface is still small
- there is no large UI state model to preserve during migration
- deployment/environment handling depends on the build system choice
- a clean cut avoids temporary compatibility code that would be deleted shortly after

## Architecture

### Build System

Use Vite as the extension build entrypoint. Vite will be responsible for:

- building the popup React application
- bundling TypeScript-based background and content scripts
- producing environment-aware outputs for development and production
- supporting manifest generation or manifest transformation per environment

The build system should become the source of truth for extension packaging rather than relying on manually loaded plain source files.

### Runtime Units

The migrated extension should keep the existing runtime responsibilities:

- Popup app: React UI that renders auth status, sign-in/sign-out actions, summarize actions, and result/error states
- Background script: owns Google auth flow, backend token exchange, and persisted auth state
- Content script: extracts YouTube video context from the active page
- Shared config/types: centralizes environment values and message/auth contracts

These boundaries align with the current implementation and avoid unnecessary refactoring during the migration.

### Environment Handling

Development and production should be explicit build targets.

Environment-aware values should be centralized in a typed config boundary, such as:

- API base URL
- application label if needed
- manifest-specific values such as host permissions and OAuth client ID

The runtime code should not infer environment indirectly from extension IDs or ad hoc checks. Instead, the build should inject or select the correct environment values for each target.

## Data Flow

The runtime flow should remain equivalent to the current extension:

1. Popup loads and requests auth state from the background script.
2. Background reads persisted auth state from `chrome.storage.local`.
3. User signs in through the popup.
4. Background launches Google web auth, validates the callback, exchanges the Google token with the backend, and stores the resulting auth state.
5. User requests summarization from the popup.
6. Popup asks the content script for YouTube video context from the active tab.
7. Popup calls the backend summarize endpoint with the stored access token.
8. Popup renders loading, success, or error state.

This behavior should be preserved exactly unless a migration detail requires a narrowly scoped compatibility adjustment.

## File Structure Direction

The migrated extension should move toward a structure like:

- `apps/extension/package.json`
- `apps/extension/tsconfig.json`
- `apps/extension/vite.config.ts`
- `apps/extension/manifest.config.ts` or equivalent manifest-generation helper
- `apps/extension/src/config/*`
- `apps/extension/src/types/*`
- `apps/extension/src/background.ts`
- `apps/extension/src/content.ts`
- `apps/extension/src/popup/main.tsx`
- `apps/extension/src/popup/App.tsx`

Exact filenames may vary slightly based on the chosen Vite extension packaging strategy, but the important boundary is:

- React UI isolated in the popup app
- extension scripts kept simple and typed
- shared config/types extracted from UI and script logic

## Error Handling

The migration should preserve the current user-facing error behavior while making the contracts more explicit.

Recommended direction:

- background script returns normalized success/error responses for auth-related runtime messages
- popup owns user-facing loading and error display states
- shared TypeScript message and payload types prevent popup/background drift
- backend fetch failures continue surfacing simple user-readable messages rather than raw runtime internals

## Testing Strategy

Testing should stay proportional to the size of the extension.

### Automated

- Add unit tests for shared config and message/type helpers
- Add popup component tests for signed-out, signing-in, summarizing, success, and failure states
- Add focused tests for small extracted helpers where logic is nontrivial, such as auth response normalization or config selection

### Manual

Manual verification remains important for:

- Chrome extension loading in development
- Google auth flow behavior
- runtime messaging across popup/background/content
- summarize flow against the API in a dev environment
- production build packaging sanity

## Migration Sequence

1. Set up the extension-local Vite, React, and TypeScript toolchain.
2. Establish manifest generation/transformation for dev and prod.
3. Introduce the shared config/type boundary.
4. Rewrite popup UI into React and TypeScript.
5. Migrate background and content scripts to TypeScript.
6. Reconnect runtime messaging and API calls.
7. Add targeted tests and manual verification coverage.
8. Remove obsolete plain JavaScript assets and manual-only build assumptions.

## Risks

### MV3 Packaging Risk

Manifest V3 has stricter expectations around script entrypoints, permissions, and generated asset paths. The chosen Vite setup must explicitly support MV3 packaging rather than assuming a standard web app output.

### Auth Flow Risk

Google auth depends on manifest metadata and Chrome identity APIs. Migration must preserve:

- OAuth client ID placement
- redirect URL behavior
- runtime message flow between popup and background

### Over-Refactor Risk

Because this is a rewrite, there is a temptation to redesign behavior at the same time. The migration should stay focused on stack and deployment improvements, not product changes.

## Recommendation

Adopt a one-shot rewrite to `Vite + React + TypeScript`, while deliberately preserving the current extension behavior and keeping environment handling explicit and centralized.

This gives the extension:

- a maintainable frontend foundation
- a clean dev/prod deployment story
- typed message/config boundaries
- a smaller chance of duplicated migration work compared with solving deployment first in the current plain-JS setup

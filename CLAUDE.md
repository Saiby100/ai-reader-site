# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
npm run dev       # Start Next.js dev server
npm run build     # Production build
npm run start     # Start production server
npm run lint      # Lint (ESLint with next config)
```

## Architecture

**Next.js 16 app** (App Router, file-based routing) — an AI-powered reading assistant for complex articles. Uses Vercel AI SDK with Google AI provider, Tailwind CSS v4, and React 19.

### Routes (`src/app/`)

- `page.tsx` — Main page
- `layout.tsx` — Root layout with Geist font
- `api/chat/route.ts` — AI chat API endpoint (Vercel AI SDK)

### Key Patterns

- **Path alias** — `@/*` maps to `./src/*` (configured in `tsconfig.json`).
- **Styling** — Tailwind CSS v4 (PostCSS plugin). No CSS-in-JS.
- **AI SDK** — `ai` + `@ai-sdk/google` + `@ai-sdk/react` for streaming chat.
- **TypeScript strict mode** enabled.

## IMPORTANT: Always Clarify Before Acting

**Do NOT assume requirements. Always ask questions first.**

Before starting any task — especially feature work, refactors, or anything with ambiguity — ask clarifying questions to fully understand what is expected. Do not guess at intent, scope, or implementation details. It is always better to ask one too many questions than to build the wrong thing.

## Code Style

- Prefer small, focused files with utility functions over large files with many functions. Group closely related functions together in the same file.
- TypeScript strict mode
- 2-space indent, single quotes, 100 print width

## Component Definition Style

- **Do not use `React.FC`**: Define components as plain arrow functions with props typed inline — `const Foo = ({ bar }: FooProps) => { ... }`. `React.FC` adds no value in React 18+ and is avoided here.
- **Server Components by default**: Only add `'use client'` when the component needs interactivity, hooks, or browser APIs.

## UI Component Guidelines

- **Keep pages thin**: Page files in `app/` should primarily compose components and manage data fetching — not contain complex rendering logic.
- **Extract logic into custom hooks**: Move data fetching, subscriptions, and non-trivial logic out of page files into custom hooks in `src/hooks/`. Page files should read like a declarative composition of hooks and components.
- **Organize hooks by domain entity, not by page or query**: Group related queries and mutations into a single hook file per domain entity. Add new queries to the existing entity hook rather than creating a new hook file per query.
- **Single responsibility**: Each component should do one thing. Prefer focused components over monolithic pages that render everything inline.
- **Composable and prop-driven**: Components should accept props for data and callbacks — avoid reaching into global state from deep UI components.
- **Avoid premature abstraction**: Don't create a wrapper component for something used only once. Extract when there's actual reuse or the file becomes hard to follow.

## Type Definition Guidelines

- **Use `type` over `interface`**: Prefer `type` for consistency. Use `interface` only when declaration merging is needed.
- **No `any`**: Use `unknown` for truly unknown data, or type it properly. `Record<string, unknown>` over `Record<string, any>`.
- **Prefer narrow types**: Use string literal unions over plain `string` for fields with known values.
- **Props types next to components**: Component prop types should be defined in the same file as the component, not in a separate types file.
- **Document type fields**: Every field in a `type` definition must have a brief JSDoc comment (`/** ... */`) describing its purpose.

## Commit Guidelines

- **One commit per task**: Separate tasks must be committed separately — never bundle unrelated changes into a single commit. If you completed multiple tasks before committing, create one commit per task.
- **Ask when unsure**: If it's unclear whether changes belong in one commit or multiple, ask before committing.

## Maintaining this file

When making changes that affect architecture, commands, key patterns, or project structure, update the relevant sections of this CLAUDE.md to keep it accurate.

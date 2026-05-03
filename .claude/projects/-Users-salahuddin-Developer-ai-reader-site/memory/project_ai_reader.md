---
name: AI Reader project overview
description: AI-powered reading assistant app — Next.js, Vercel AI SDK, Gemini 2.0 Flash, MongoDB planned
type: project
---

AI Reader: a web app to streamline reading complex articles with AI assistance.

**Stack:** Next.js + React, Vercel AI SDK (`ai` v6, `@ai-sdk/google`, `@ai-sdk/react`), Gemini 2.0 Flash (free tier), MongoDB planned for persistent memory features.

**Core concept:** Reading pane + chat sidebar. Viewport text is automatically captured as LLM context. Users can also highlight text for targeted questions.

**Why:** User wants to reduce friction when reading complex articles — the LLM should understand what the user is currently reading without manual copy-paste.

**How to apply:** All features should revolve around the reading experience. Context management (viewport, selection) is a first-class concern.

<!-- GSD:project-start source:PROJECT.md -->

## Project

@.planning/PROJECT.md
<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->

## Technology Stack

@.planning/codebase/STACK.md
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

@.planning/codebase/CONVENTIONS.md
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

@.planning/codebase/ARCHITECTURE.md
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:strategy-start source:STRATEGY.md -->

## GSD Strategy

**Directo por defecto.** No lances la ceremonia GSD (`map-codebase`/`plan`/`execute`) para tareas triviales o mecánicas — consume tokens sin valor proporcional. Esta sección tiene prioridad sobre "Workflow Enforcement" de arriba.

- Trivial / mecánico / fix puntual / doc / config → **implementación directa**.
- Feature nueva con decisiones de diseño, refactor transversal, seguridad, infra/CI → `/gsd-execute-phase`.
- Bug difícil → `/gsd-debug`.
- Tras trabajo con riesgo → `code-review` + `verifier`.
- Tras trabajo directo → sincronizar `.planning/ROADMAP.md`, `STATE.md`, `PROJECT.md`.

Detalle: `.planning/STRATEGY.md`.

<!-- GSD:strategy-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->

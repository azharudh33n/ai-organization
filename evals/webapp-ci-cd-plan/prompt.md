---
tags: [ai-organization]
max_turns: 40
timeout_seconds: 900
allowed_tools: [Read, Glob, Grep, Skill, Write, Edit]
---

Use the ai-organization skill to plan this project. This is a dry run: produce the planning artifacts up to and including the work plan, then stop before execution. Don't install skills, clone repos or browse the web; where a skill would need sourcing, name your pick and mark it 'to verify'.

PROJECT: appointment booking web app for a 3-branch dental clinic in Dubai. Patients book, reschedule and cancel online; front-desk staff get a dashboard; WhatsApp reminders 24h before.
DELIVERABLES: GitHub repo with CI/CD, app deployed to our self-hosted Coolify server.
STACK: Next.js + Postgres.
CONSTRAINTS: 4 weeks, two human reviewers available, patient data must stay in the UAE (PDPL).

# AI agent rules (Antigravity / VS Code agents)

Use these rules in the project prompt/context:

1. Read the rubric, README and relevant module before editing. Ask before changing label rules or data definitions.
2. Never invent FDIC field semantics. Verify each field against FDIC's official data dictionary; mark unknowns explicitly.
3. No raw-data uploads, commits, cloud calls, or secrets. Local-only data stays in ignored directories.
4. Never use random train/test split. No future rows, post-exit observations, full-panel imputation/scaling, or test-driven threshold tuning.
5. Keep changes small and modular. Add/modify tests for each behavior. Run compile, tests and lint; report failures honestly.
6. For performance claims, benchmark repeated runs on identical inputs and hardware. Never fabricate runtime/RAM metrics.
7. Any generated code must be explained in Vietnamese to the student and accompanied by a code citation/AI-use disclosure in report/README.
8. Before changing files, provide a plan; after editing, summarize files changed, tests run, remaining risks. Do not overwrite student work without approval.

# AI agent guidelines (AGENTS.md)

**You are** an engineering agent (goose or Claude Code) on croit's fork of
`alerta-contrib`: plugins, webhooks and integrations for the
[Alerta](https://alerta.io/) monitoring system, in Python. croit runs some of
them, such as the Discord plugin, on its own Alerta server.

Commits, merge requests and testing: [CONTRIBUTING.md](CONTRIBUTING.md).

## Gating

- **Get an explicit OK on the approach before producing anything** (code,
  content, configuration). Reading, investigating and proposing a plan need no
  OK.
- **On a feature branch, commit and push freely:** small commits that pass the
  checks. Before the MR, list every commit on the branch (subject, why,
  files), show the MR description, and wait for an OK.
- **These need a fresh, explicit OK each time:** opening an MR, anything on
  `master`, force-pushes and other history rewrites, tags and releases,
  `--no-verify`, pushing to the `github` remote, and destructive or privileged
  actions. A prior OK never carries over, and silence is not consent.
- **Agents never merge.** The person who had the MR opened checks it, merges
  it, and is responsible for it.
- **Never work on `master`.** Branch off it for every change; it only changes
  through a reviewed MR.
- **Never commit secrets:** no passwords, API keys, webhook URLs or `.env`
  files in code, config, tests, commit messages or prompts. Tests use fake
  URLs and keys.
- **No AI attribution** anywhere: no co-author or session trailers, no
  "Generated with" lines, in commits, MR descriptions or comments.
- **Never add a `CLAUDE.md`:** Claude Code then stops loading `AGENTS.md` and
  with it these rules. Put rules into `AGENTS.md`.

## Rules of this repository

- **Two remotes:** `origin` is croit's GitLab and the one we work on.
  `github` is a fork of the upstream project
  ([alerta/alerta-contrib](https://github.com/alerta/alerta-contrib)). Never
  push to it or open upstream pull requests without an explicit OK.
- **Each plugin, webhook and integration is its own package** with its own
  `setup.py`, `README.md` and tests, in its own directory under `plugins/`,
  `webhooks/` or `integrations/`. A change stays inside the package it is
  about.
- **Upstream code stays as upstream wrote it.** Don't reformat, re-lint or
  refactor packages croit doesn't change; it makes merging upstream harder.

## Orientation

- `plugins/<name>/alerta_<name>.py`: server plugins, subclasses of
  `alerta.plugins.PluginBase`, loaded through the `alerta.plugins` entry point
  in their `setup.py`. Tests in `plugins/<name>/test_<name>.py`.
- `webhooks/`: server webhooks for other monitoring tools.
- `integrations/`: standalone tools that send alerts to the Alerta API.
- `requirements-dev.txt`: what the tests and linters need.
- `.github/workflows/`: upstream's GitHub Actions; they don't run on GitLab.

Alerta's server source (`alerta-server` on PyPI) is the reference for how and
when it calls a plugin's hooks; read it there instead of guessing. For
example, `Alert.update()` calls `status_change()` with the stored alert
before `post_receive()` gets the updated one.

## Before new code: the ladder

1. Is it needed at all? A configuration value or a README line may do.
2. Is it already here? Another plugin often solves the same problem
   (`slack`, `telegram`, `msteams` for chat notifications).
3. Does Alerta itself provide it (`PluginBase`, `get_config()`, the alarm
   model, plugin routing)?
4. Python's standard library.
5. A package the plugin already depends on, such as `requests`.
6. Only then new code, kept short. Propose a new dependency first.

## Validating a change

- Tests need a PostgreSQL database in `DATABASE_URL`; a throwaway local
  container is fine. Never point tests at a production Alerta server or
  database.
- Run the changed package's tests and the hooks on the files you changed, as
  [CONTRIBUTING.md](CONTRIBUTING.md) describes.

## Code

- Python 3, in the style of the file you change. One logger per module, named
  `alerta.plugins.<name>`; `logging` for diagnostics, never `print`. Never log
  webhook URLs, API keys or personal data.
- A plugin reads its configuration from environment variables first, then
  from `alertad.conf`, as the existing plugins do. Document every setting in
  the plugin's README.
- Unit tests mock every external service (`requests.post` and the like).

## How to think

- **Ask instead of guessing.** State your reading of an ambiguous request, and
  check names, paths and parameters instead of inventing them.
- **Push back.** When you see a simpler option, one that reuses what exists or
  serves the real goal better, say so in a line or two of trade-off and let
  the user decide. Never substitute it silently.
- **KISS and YAGNI.** Nothing speculative or configurable that wasn't asked
  for. Go down the ladder above and stop at the first step that works. The
  ladder never drops input checks, error handling or security.
- **Surgical changes.** Touch only what the task needs, remove what your change
  leaves unused, and match the file's style.
- **Never fail silently.** When something cannot do its job, it says what
  failed, why and where to look next.
- **Report bottom line first,** then the detail.

## Scope

- **One purpose per change:** no unrelated fixes, rewording, reformatting or
  refactoring.
- **Unrelated findings:** don't fix them. Note them, ask how to track them,
  and go back to the task.
- **Bug fixes start with a failing test;** it may share the fix's commit.
- **Stage explicit paths,** never `git add -A` or `git add .`: the checkout
  may hold someone else's untracked files.
- **Rebase conflicts:** if a rebase onto `origin/master` doesn't apply
  cleanly, stop; the human resolves it.

## Done

The change does what was asked, its tests pass, the hooks pass on the changed
files, the package's README is updated, and nothing out of scope changed.

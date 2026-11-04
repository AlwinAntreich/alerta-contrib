# Contributing

How we work on croit's fork of `alerta-contrib`. What each package does and
how to install it is in its own `README.md`. AI agents working in this
repository should also read [AGENTS.md](AGENTS.md).

## Workflow

`discord-plugin` is croit's main branch: everything croit runs lives there.
`master` holds upstream's code; don't commit to it.

Every change ends with a reviewed merge to `discord-plugin`. The project has
no issue tracker set up yet, so the merge request carries the what and the
why.

1. **Discuss** the approach before writing code.
1. **Branch** off `discord-plugin` and implement the minimal change. Update
   the package's `README.md` in the same MR wherever the change makes it
   wrong or incomplete.
1. **Validate locally** (see below).
1. **Commit** (see below). Before opening the merge request, and again before
   the merge, check whether `discord-plugin` has moved:
   `git fetch origin && git rev-list --count HEAD..origin/discord-plugin`
   counts the commits the branch is behind. If it is behind, rebase onto
   `origin/discord-plugin` and validate again.
1. **Open the merge request** on GitLab (`origin`). Its title and description
   say what the branch does, every commit's change included, and nothing it
   does not do; check them again after every further commit.

The `github` remote is a fork of the upstream project. Changes go upstream
only by an explicit decision, as their own pull request.

## Validating a change

Install the development requirements into a virtual environment:

```sh
python3 -m venv venv && . venv/bin/activate
pip install -r requirements-dev.txt
```

The tests need a PostgreSQL database. A throwaway container does:

```sh
podman run -d --rm --name alerta-pg -p 5432:5432 \
  -e POSTGRES_DB=alerta -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres docker.io/library/postgres:15
export DATABASE_URL=postgres://postgres:postgres@localhost:5432/alerta
pytest -v plugins/<name>/test_<name>.py
```

Run the hooks on the files you changed, not on the whole repository:

```sh
pre-commit run --files plugins/<name>/*
```

The hooks in `.pre-commit-config.yaml` are upstream's and pinned to old
versions: flake8 and isort fail to start on Python 3.12 and later. Use Python
3.11 for them, or run `flake8 --ignore=E501` and `isort --check-only --diff`
from the virtual environment. When a hook rewrites lines your change doesn't
touch, revert those rewrites.

## Commits

Commit titles use a tag prefix and a short, imperative description. Add a
body explaining the why for anything non-trivial, wrapped at 72 characters,
and sign off (`git commit -s`).

```text
discord: fix: post one message per alert change

A received alert that changed status posted two messages: one from
status_change() with the stored alert, one from post_receive() without
the text. post_receive() now posts it once, with the updated alert.

Signed-off-by: Jane Doe <jane.doe@croit.io>
```

Each commit message is permanent history on `discord-plugin`, so write it
to stand on its own, and squash fixup commits into the commit they fix before
the merge. Don't start a body line with `#`; git strips such lines when a
message is edited.

Tags (you may use more than one, e.g. `discord: fix: ...`):

**Component**

- `<name>`: the plugin, webhook or integration the change is about, e.g.
  `discord`, `prometheus`
- `agents`: AI agent guidelines (`AGENTS.md`)
- `ci`: CI workflows and `.pre-commit-config.yaml`

**Change type**

- `build`: packaging and dependencies (`setup.py`, requirements)
- `docs`: documentation additions or changes
- `feat`: a new feature
- `fix`: a bug fix
- `lint`: changes caused by linters
- `tests`: test additions or changes

## Merge requests

* Keep changes single-purpose. Do not mix unrelated refactoring with feature
  work, and do not reformat untouched files or packages.
* **Bug fixes**: add a failing regression test first, confirm it fails, then
  add the fix. Both may land in the same commit, but the test is written
  first.
* **Features**: include tests covering the core functionality before merge.
* Changes to gates (`.pre-commit-config.yaml`, CI) go in the first commit of a
  branch, so they check every later commit.
* If you spot an unrelated bug or tech debt, do not fix it here. Note it in
  the MR and keep this change focused.

## Code of conduct

This repository is part of the croit organization. Follow the croit Manifesto.

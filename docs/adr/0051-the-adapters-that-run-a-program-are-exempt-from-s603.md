# ADR-0051 · The adapters that run a program are exempt from S603

**Status:** proposed

## Context

The adapter of the project repository runs `git`, and the adapter of the verification runtime will
run `podman` ([ADR-0042](0042-a-port-of-the-project-repository-composes-the-trees-that-are-built.md),
[ADR-0043](0043-tests-run-only-on-an-engine-that-enforces-the-limits.md)).
Running a program is what they are for. The lint gate selects the rules `S` of ruff, and S603
reports every call that starts a process without a shell when its arguments are not literals. The
first version of the git adapter has two such calls, and both are reported. `tests/**` and
`tools/**` are already exempt from S603 and S607; `src/` is not.

## Decision

The rule S603 is not applied to `src/dokime/platform/**` and `src/dokime/sandbox/**`, by a
per-file ignore in `pyproject.toml`. Every other rule `S` stays in force there, S602 (a call with
a shell) and S607 (a program named by a partial path) included: an adapter resolves the path of
its program once when it opens, with `shutil.which`, and runs that path always, so that the
evidence can record which program and which version were used.

## Basis

Read in the documentation of ruff: S603 checks "method calls that initiate a subprocess without a
shell", and is "prone to false positives" because it cannot tell whether the arguments were
validated; S607 reports "the starting of a process with a partial executable path", because a
change of `PATH` could run another program. Measured on the git adapter: S603 reported its two
calls to `subprocess.run`, each with a list of arguments the adapter builds and no shell. Not
looked for: how other projects scope this rule. Reasoning, without a test: that an exemption
bounded to the two modules whose job is to run a program says the same as a mark on each call,
in one place, and leaves the rule in force where a call to a program would be a surprise.

## Alternatives considered

- **A `# noqa: S603` on each call.** It relaxes the same rule, spread over the calls, with no
  decision written down; a new call in another module would be silenced the same way.
- **Exempt all of `src/`.** A call to a program in a domain module, which must not talk to the
  outside, would no longer be reported.
- **Exempt S607 as well, and run `git` by name.** The program that ran would depend on the `PATH`
  of each call, and the evidence could not say which one it was.

## Consequences

- The two adapter modules may start processes with arguments they compute; review, not the gate,
  checks that those arguments come from the adapter and not from the project.
- A program named by a partial path, or a call through a shell, is still refused by the gate in
  the adapters.
- Another module that needs to run a program needs another ADR.

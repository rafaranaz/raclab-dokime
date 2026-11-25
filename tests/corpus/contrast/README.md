# The contrast with swarm-verify (R2)

**Before anything runs: what the arm S2 measures.** S2 gives swarm-verify the examples of a
dokime contract as black-box checks, and those checks observe with the program that observes of
dokime and compare with the oracle of dokime, copied as they are. So S2 does not measure how
swarm-verify compares; it measures **where the comparison happens**. In swarm-verify the sealed
checks, with their expected values, are laid into the checkout while they run, in the same
container as the code of the candidate, and its evidence publishes their sources. In dokime the
expected values never enter the zone (INV-2).

Nothing here runs on the corpus before the maintainer approves the criteria of R1.

## Where the held-out examples of the corpus live

The held-out examples of a case of the corpus exist in clear only where its sealed batch is opened,
on the machine of the maintainer, and never on the machine where this code is written:

- **On the machine of the maintainer only**, by commands that come with the runs of R2 and are
  reviewed before they run: the conversion of the held-out examples, their sealing for swarm-verify
  and the runs of S1 and S2 with sealed checks. Each run has its `SWARM_HOME` in a directory of its
  own, deleted when the run ends; the bundles of evidence stay on that machine.
- **What leaves that machine**, after review: the status of each case and, for each arm, how many
  visible and how many held-out checks passed and how many failed. No id of a held-out check, no
  `sealed/files/` and no log.
- **Here**, the code of the contrast opens no sealed batch and uses no identity (CORPUS-109).

The reason is a limit of swarm-verify, and a result for the table of R2: **its sealed checks and the
evidence of its runs are in clear.** Both `seal` and `sealFiles` write the sealed files unencrypted
in `$SWARM_HOME/sealed/<key>/files/`, in directories of mode 0700
(`dist/verify/sealed-store.js` of 3.1.0, lines 97–104 and 181–185), and each bundle of evidence
publishes them under `sealed/files/` (line 202). "Sealed" in swarm-verify means kept out of the
workspace of the candidate, not encrypted. `sealFiles` (line 173) takes the files in memory, so the
conversion need not write them to a workspace or a temporary file, though the store writes them.

## The arms

R2 runs [swarm-verify](https://github.com/moonrunnerkc/swarm-verify) 3.1.0, from npm, pinned by
its version and its integrity `sha512-xpAfXmNioZQVadKqldljIjLX6cAtLAqxqU08CFZ1Nu6Qt6Ha7saJBd0UZsTUksue5oTb/u2XnHcrhU95e8DlGw==`
(gitHead `b0887244e4ad9e1dfdb25e5241b871564b395fa9`), on the cases of the corpus, in three arms:

| Arm | What swarm-verify is given |
|---|---|
| S0 | The project and the patch |
| S1 | Besides, the tests that the original project added with its fix, sealed as held-out checks |
| S2 | Besides, the examples of the contract as black-box checks: the visible ones supplied as `user-acceptance`, the held-out ones sealed |

## The conversion

```console
$ uv run python -m tests.corpus.contrast.convert CONTRACT OUT EXAMPLE_ID...
```

writes the directory `OUT`, to be laid among the tests of a local copy of the base so that the
test check of the project collects it:

- `observe_program.py` and `dokime/` with `core`, `contract`, `oracle` and `sandbox`, copied from
  `src/dokime` as they are;
- `examples/<id>.json`, each example as dokime read it from the contract, its matchers and tuples
  named by their type, rebuilt by `run.py` without running any code;
- `run.py`, a copy of `runner.py`: from the root of the project, `python run.py <id>` sends the
  program that observes the request that the podman adapter sends, in a process of its own, with
  `.venv/bin/python` of the project when it has one, and compares the observation with the oracle:
  exit 0 when the example holds, 1 when it does not, 2 when the program ended with an error;
- `test_dokime_examples.py`, a copy of `checks_file.py`: one pytest test for each example, which
  passes only when `run.py` exits with 0.

The copies of dokime need Python 3.13, so the image of a run is uv on Python 3.13, pinned by its
digest in `adaptations.toml`; the default image of swarm-verify is on Python 3.12.

## The adaptations of each project

`adaptations.toml` holds, for each project, what was added to a local copy of its base so that
swarm-verify runs it: the files, the image, the command of setup and of the tests, and the minutes
it cost. They are the equivalent of a pack: made once for the project, before any result is seen,
and the same for all its cases. Every project of the corpus gives its minutes as a whole number;
only a project outside it may give `"not measured"`, as the entry `humanize` does, the trial of the
mount outside the corpus, which was not timed.

## What the trial on humanize found

Run at humanize `823ad60`, a project outside the corpus, with its good fix only; no bad patch was
run yet. These go to the table of R2 as results:

- **The supplied checks are given only through the API of Node** (`checks` of the request); the
  command line has no option for them. Their command sees only the checkout, so their files have to
  be in the base, where the patch can change them.
- **The sealed files share the container with the candidate**, and the evidence of swarm-verify
  publishes their sources (`sealed/files/` of the bundle), as the first paragraph says.

And these are of the mount, solved by the adaptations:

- swarm-verify hides `.git` in the container, so a project whose version comes from git
  (setuptools-scm) is `blocked` until the version is given in its setup.
- `init --seal` checks on the host, outside the container, that the held-out check fails at the
  base and passes on a reference patch: `dist/verify/held-out-validation.js` of swarm-verify 3.1.0
  runs it with `execution: hostExecution` (line 24), and the trial showed it, a command of
  `.venv/bin/python` failing with exit 127 on the host. So the command of the tests has to run on
  both; `uv run --frozen` with a `uv.lock` in the base does.
- A requirement mapped to a whole check stays `unverified`: swarm-verify asks for a test that fails
  before the change and passes after it, so the requirements are mapped to tests by name,
  `test_dokime_example[<id>]`.

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
- **Here**, no module of the contrast but `maintainer.py` opens a sealed batch or uses an identity
  (CORPUS-109), and `maintainer.py` is run here only by its tests, with an identity and a batch made
  for them.

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

## The runs

On the machine of the maintainer, with git, uv, node and docker:

```console
$ (cd tests/corpus/contrast && npm ci)
$ DOKIME_CORPUS_IDENTITY=<identity> uv run python -m tests.corpus.contrast.maintainer \
    OUT RESULTS --work DIR
```

`--work DIR` makes the local copies and the `SWARM_HOME` of each run in `DIR`, which should be on
a disk with room: without it they go to the temporary directory of the system, `TMPDIR` or `/tmp`,
which on the machine of the maintainer is a tmpfs of 2 GB (CORPUS-125).

`maintainer.py` asks for the passphrase on the terminal and refuses to start without an identity
(CORPUS-114). For each of the 32 cases that are not withdrawn, `--clones DIR` taking each project
from `DIR/<project>` instead of its address and `--case KEY` choosing cases, it runs S0, S1 and S2
(CORPUS-115):

- **The mount.** A local copy of the base of the case, the adaptation of its project committed on
  it, and the patch of the case committed on top. In S2 the conversion of the visible examples of
  the contract is committed in the base too, at `tests/dokime_visible/`, and given as a check of
  authority `user-acceptance` that runs the command of the tests of the adaptation on it alone.
- **S1** seals the files of the tests of the pack that the witness of the good case changed, as
  they are at the witness, with a check that runs the same command on them (CORPUS-117). A file
  that the base already tracks is sealed beside it, as `<name>_witness<suffix>`, for the reason
  below, and its tests are counted there (CORPUS-121).
- **The requirement.** S1 and S2 give swarm-verify one requirement for the contract, `R1`, of the
  kind `fix` and required, its text the requirements of the contract, with the sealed check bound to
  it and, in S2, the tests of the visible conversion as its evidence (CORPUS-124). Without it a
  check that fails at the base and still fails holds, as `inherited-failures`
  (`dist/verify/acceptance.js:84`), so a patch that leaves a visible example failing would give
  `complete`; with it, swarm-verify knows, as dokime does, that each example has to pass: a fix
  needs a test that fails before and passes after, chosen by someone else than the author of the
  patch (`acceptance.js:26-56`), and a mapped test that fails makes it `failed`.
- **S2** seals, when the contract holds out examples (17 of the 32 cases, the 5 good ones with a
  batch and the bad ones derived from them), the conversion of the held-out examples of its batch,
  at `tests/dokime_held_out/`, under the names `h1`, `h2`... that carry no id (CORPUS-118). The
  batch is opened in memory and the files go to `run_arm.mjs` only through its input, which seals
  them with `sealFiles` (CORPUS-113, CORPUS-119); the canary is not among them.
- **Each run** gives swarm-verify a `SWARM_HOME` of its own, deleted when it ends (CORPUS-116), and
  keeps its evidence in `OUT/<project>--<case>/<arm>/`. That evidence holds the sealed files in
  clear, as said above, and stays on that machine.

`RESULTS` receives one table `[[run]]` for each run, the only thing meant to leave that machine,
after review (CORPUS-120): the key of the case, the arm, the `state` and the `regression` that
swarm-verify gave, `visible_passed` and `visible_failed`, `held_out_passed` and
`held_out_failed`, `xfail_only` and `failure`, and nothing else. The counts are of tests, as they
ran: the visible ones are the tests of `tests/dokime_visible/` in the visible check, one for each
example; the held-out ones are, in S1, the tests that the witness turned green and, in S2, the
tests of `tests/dokime_held_out/`, each as it ran in the sealed check (CORPUS-121). A test that did
not pass counts as failed. `xfail_only` is true when the state is not `complete` and the only test
of the run that failed is the strict-xfail test of mdformat (CORPUS-122). `failure` is `mount` or
`helper` when the mount or the helper of Node failed, with no message, and the next run goes on
(CORPUS-123).

**Why a sealed file cannot go where the base tracks one**, from swarm-verify 3.1.0, a limit that
goes to the table of R2. After the checks of the candidate, `dist/verify/candidate.js:149` keeps as
the paths to restore only the test files that the candidate changed. `runSealedOnCandidate`
(`dist/verify/held-out.js:126-139`) lays the sealed files into the tree of the candidate, runs
them, restores only those paths, and records "the held-out run rewrote tracked files of the
candidate" when the digest of the tree differs. That problem makes `policyMet` false
(`dist/verify/assess.js:95`), and the state is `complete` only with it true
(`dist/verify/acceptance.js:96`). So a sealed file at a tracked path the candidate did not change
makes every run `incomplete`, whatever the patch: 8 of the 10 witnesses change test files that the
base has, `tests/test_api.py` or `tests/test_replace.py` among them. A user of swarm-verify can hold
out only new files.

Before the review, the command ran its three arms here on the small project of its tests, with the
real swarm-verify and docker and a batch made for the test, not on the corpus, its patch a comment
that fixes nothing. The first time, with no requirement and the witness file at its own path, S1
gave `incomplete` with its held-out test green, for the tracked file above, and S2 `complete` with
a visible example failing, for the inherited failures. As it is now: S0 `complete`; S1 `incomplete`
with `policyMet` true, its requirement `unverified` since the witness test passes at the base too;
S2 `incomplete`, its requirement `failed` on the example that the contract of the test gets wrong
on purpose, 5 visible examples passed and 1 failed, and the held-out one passed. The only file that
held the held-out example was the evidence of swarm-verify, under `sealed/files/`.

## The adaptations of each project

`adaptations.toml` holds, for each project, what was added to a local copy of its base so that
swarm-verify runs it: the files, the image, the command of setup and of the tests, and the minutes
it cost. They are the equivalent of a pack: made once for the project, before any result is seen,
and the same for all its cases. Every project of the corpus with a case has one (CORPUS-110), its
image pinned by its digest (CORPUS-111). Every project of the corpus gives its minutes as a whole
number; only a project outside it may give `"not measured"`, as the entry `humanize` does, the trial
of the mount outside the corpus, which was not timed.

The entries of mdformat and python-semver were set up on 2026-11-27, before any bad case ran:

- **No file of the project is changed.** The tools of the tests are those of the pack, at the
  versions of its Dockerfile, in an environment of their own under `.contrast/` with its `uv.lock`;
  the project is imported from `src/`, as the pack does. A patch therefore cannot touch the
  adaptation.
- **The runs that set them up are setup, not results of R2**, and were not kept. Each adaptation was
  laid on the base of every good case of its project with the good patch, and the tests were run on
  the host; one good case of each project was run in the arm S0 with docker, to see the mount work
  in the container.
- **The minutes** are those of the session that set both up, about seven by the clock, split four
  for mdformat and three for python-semver; they are not the minutes of a person.

One thing that setup showed goes to the table of R2 as a result, as the maintainer decided, and was
not adapted away. The three good patches of mdformat give in S0 `regression found`: the witness
`27e2ba3` fixes the code and takes the mark `xfail` off the test that the fix turns green, while the
good patch of the corpus holds only the code, so that test, still marked and with
`xfail_strict = true`, passes and pytest counts it as failed. The bad cases of mdformat share the base. Each run records whether its rejection comes only
from that test, public in the witness, and such rejections are counted apart, for good and bad cases
alike, as blocked runs and failures of the mount are, so that they count neither as caught nor as a
cost.

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

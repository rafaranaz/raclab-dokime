# ADR-0063 · A program of sandbox observes the examples inside the zone and writes what it saw as JSON

**Status:** proposed

## Context

The gate `visible-examples` of A3 runs the examples of a contract at the boundaries `function` and
`cli` ([ADR-0039](0039-what-a-contract-of-the-first-version-may-say.md)). What is decided: the
harness sends to the zone of verification "base plus filtered patch, inputs only", the zone gives
back observations, and the harness compares outside it
([`03-data-and-evidence.md`](../architecture/03-data-and-evidence.md#a-change-from-end-to-end));
the code under test receives only the inputs, returns an observation serialised as JSON, and each
example runs in a new process ([ADR-0012](0012-examples-are-observations-at-a-boundary.md)).
Nothing says which program runs an example inside the container, of which module it is, how it
gets there, with which interpreter, nor how it gives back what it saw.

## Decision

- **The program is of `sandbox`**, behind a port of its own in `core` that observes the steps of
  examples in an image and a tree and gives their observations. It is a port apart from that of
  the verification runtime, as the port of the audited repository is apart from that of the
  project repository, so that the adapters and the doubles of the self-check keep theirs. `verify`
  builds the requests and `oracle` compares the observations with what is expected.
- **It enters the container mounted read-only**, with the inputs, in a directory of its own such
  as `/dokime/probe`. The image is not changed, so its digest is the one built from the pack, and
  nothing that runs during the build can touch the program. The evidence records the digest of the
  program.
- **The main program runs on the Python of the image with `python -I -S`.** It needs nothing of
  third parties: `-I` leaves out the variables of Python and the directory of the user, and `-S`
  leaves out `site`, whose `.pth` files can run code, and the build runs code of the project
  (`pip install .`) that could leave one there.
- **Each example runs in a new process**, a child `python -I` that does have the site-packages of
  the image, since the code under test needs its dependencies. The child imports what it needs
  before it adds the paths of the project to the end of `sys.path`, so that a module of the
  project cannot replace one it has already loaded. The steps of one example share its process.
- **Each example has its own limit of time and its own working directory**, writable and empty,
  since the root of the container is read-only and a command at the boundary `cli` writes files.
  An example that hangs is observed as one that reached its limit, and the others still run.
- **One container for each side.** Every example of one side of a gate runs in one container,
  which the main program starts with; the guarantees of a run
  ([ADR-0043](0043-tests-run-only-on-an-engine-that-enforces-the-limits.md)) bound the whole.
- **The observations are a file of JSON in `/dokime/out`**: for each step, what `returns` or
  `raises` gives at `function`, or the `exit`, `stdout`, `stderr` and `files` at `cli`. A value
  returned that JSON cannot hold is observed as such, with the name of its type. The adapter reads
  the file with bounds: a limit of size, the path opened without following links, a limit of
  depth, and the refusal of repeated keys and of `NaN` or infinities. That reading is not the
  canonical form of [ADR-0062](0062-a-digest-is-taken-over-a-restricted-canonical-json.md): a
  value returned may hold decimals, which the canonical form refuses.

## Basis

Read in the code of the runners of others:

- HumanEval (`human_eval/execution.py`) runs each solution in a `multiprocessing.Process`, joins
  the prompt, the solution and the test and runs them with `exec` in that process, and gives back
  a text, `"passed"`, `"failed: …"` or `"timed out"`, through a shared list. Its
  `reliability_guard` says of itself that it "is NOT a security sandbox".
- EvalPlus (`evalplus/eval/__init__.py`) runs each solution in a `multiprocessing.Process`, calls
  `out = fn(*inp)` and compares it with what is expected, with `np.allclose` and a tolerance, in
  the same process that runs the code under test; it gives back a status and an array of booleans
  in shared memory.
- SWE-bench v3.0.0 runs the tests in a container and takes the result from the log of the runner
  of the tests, which is why a `conftest.py` of the agent can rewrite it
  ([BenchJack, section 3](https://arxiv.org/abs/2605.12673)).

So the three decide whether a solution passed inside the process of the code under test, or trust
what that code writes on its output; none of them keeps the expected value out of the process of
the code under test and compares outside it, which this decision does.

Read in summaries, not in their code: LiveCodeBench runs each case of standard input and output in
a subprocess of its own with a limit of time
([OpenJarvis](https://open-jarvis.github.io/OpenJarvis/api-reference/openjarvis/evals/scorers/livecodebench),
[Skywork](https://arxiv.org/pdf/2505.22312)); BigCodeBench runs `unittest` in a container with
its dependencies installed
([evalscope](https://evalscope.readthedocs.io/en/latest/benchmarks/bigcodebench.html)).

Looked for and not found: a runner of examples that serialises the observation and compares it
outside the zone.

Reasoning, without a test: that one container for each side and a process for each example meet
ADR-0012 at the cost of one start of a container instead of one per example, which for the 13
examples of the contract of `nextver`, by the runs of the policy and by base and patch, would be
more than 50 starts for one case.

## Alternatives considered

- **The program of `verify`**, passed through the run of the verification runtime. It mixes the
  logic of the gates with code that runs inside the zone.
- **The program declared by the pack**
  ([ADR-0028](0028-language-support-is-a-declarative-pack-with-levels.md)). It is still code that someone writes; it fits when a second language arrives, in block G.
- **The program inside the image**, in a layer of the harness. The digest of the image changes
  with each version of the harness, and the image is built twice.
- **The program through the standard input of `python -`.** The standard input is the input of
  the boundary `cli`.
- **An interpreter of the harness, mounted.** It cannot import the dependencies built for the
  Python of the image.
- **The boundary `cli` without a program**, with the runtime capturing its output. The run of the
  verification runtime throws its standard output away today, and A3 is Python only.
- **The observations on the standard output of the container.** The code under test writes there,
  and could write a false observation.
- **The observations with `pickle`.** Loading them runs code in the harness.
- **One container for each example.** More isolated, and more than 50 starts for one case.

## Consequences

- The code under test runs in the process that observes it, so it can rewrite its observation, for
  instance with an `atexit`, or load a `.pth` in a child; what this decision keeps out of the zone
  is the expected value. It resists T1 and part of T2 of
  [ADR-0010](0010-threat-model.md), and it is not a defence against hostile code.
- `core` gains a port, `sandbox` an adapter and a program, and `verify` a double of the port.
- The observations of the boundary `cli` include the files a command wrote in its working
  directory, which the program reads without following links.
- A second language needs its own program; whether the pack names it is decided then.

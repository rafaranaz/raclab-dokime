# sandbox

Adapters of the verification runtime, and later of the isolation of the agent. It imports only
`core`, and only `interfaces` imports it. This increment has the adapter that builds and runs with
the `podman` command; its requirements are in
[sandbox.md](../../../docs/requirements/sandbox.md).

## The podman adapter

```python
from dokime.sandbox.podman import PodmanRuntime

runtime = PodmanRuntime()  # refuses a podman older than 4.9
runtime.podman_path, runtime.podman_version  # the podman that every command runs
runtime.expat_version  # the Expat that reads the reports, refused if older than 2.8.5
built = runtime.build(dockerfile, directory, BuildLimits())
built.image, built.base  # the base by the digest of its platform, or None from scratch
result = runtime.run(built.image, command, project, output, RunLimits())
result.ending, result.exit_code  # exited, time-limit or memory-limit
report = runtime.read_report(output, PurePosixPath("report.xml"), ReportLimits())
```

A run has no network, limits of memory with swap, processor and processes, a read-only root with
a `/tmp` of its own, the project read-only at `/dokime/project`, which is the working directory,
and the output writable at `/dokime/out`. Its processes have no capabilities in any set and cannot
gain privileges by running a program (`--cap-drop ALL`, `--security-opt no-new-privileges`). Each
run has a container of its own, removed however the run ends; on SIGINT or SIGTERM the adapter
removes it and lets the interruption go on.

Only an image that runs as root is run, and any other user is refused with `user-not-root` before
anything runs: in a rootless engine, root in the container is the person who runs the harness, and
another user is a subordinate one that cannot write in the output. The user can come from the base
image; the person can set `USER root` in the Dockerfile of the pack.

A run that ends with 137 is `memory-limit` when podman reports `OOMKilled`, or when conmon has left
a file `oom` in the working directory from which the adapter started podman, a temporary directory
of each run. podman 4.9 never reports `OOMKilled`, because it looks for that file in another
directory, so with 4.9 the file is what tells the memory limit. That file is not documented; it was
read in the sources of conmon 2.1.10 and podman 4.9.3. If conmon stops writing it, a run killed by
the memory limit on podman 4.9 is given as `exited` with 137. That failure is safe: the limit still
kills the container, and a command killed this way writes no report, so reading it is refused with
`report-missing` and the self-check ends in `ERROR` as it would with `memory-limit`.

With podman 5.4.2 too, the cause can be lost: a run killed by the memory limit was given as `exited`
with 137 in 2 of about 12 runs of the whole suite, and never when its test ran alone. The reason is
reasoned, not shown: conmon may handle the end of the process before the event of the memory limit,
and then neither podman nor conmon reports it. The same safe failure applies. The test of the
guarantee therefore takes either ending as proof that the memory was bounded, and `memory-limit`
itself is tested with a podman that reports it.

`read_report` reads the JUnit report, which the code under check wrote. It opens the path part by
part from the output directory with `O_NOFOLLOW`, refuses a link or anything that is not a regular
file with `report-not-a-file`, and passes the open file to `reader_process.py`, started with
`python -I`. Its interpreter starts without limits; the program sets its own `RLIMIT_AS` and
`RLIMIT_CPU` from the limits of reading before it reads any byte of the report, which is safe with
threads, unlike a function run between fork and exec. It then bounds the size and refuses a
`DOCTYPE`. A crash, a
reached limit or an output that is not a report is refused with `report-reader-failed`. The
process bounds the parser; it is not isolation, since it runs with the permissions of the person.
Each test is named by its class name, `::` and its name, as pytest writes it.

The tests of the four guarantees load the container, and run over the list of engines in
`tests/sandbox/engines.py`. A test of an engine that is not installed skips, except in CI, where
it fails.

## The program that observes the examples

`observe_program.py` runs inside the container, from a directory mounted read-only (ADR-0063). It
needs only the standard library, and the main program refuses to read a request unless it runs with
`python -I -S`, since `site` would process `.pth` files that the build of a project can leave. It
reads `requests.json`, runs each example in a child `python -I` with an empty working directory and
the time of one example, and writes `observations.json` in the output directory. The child imports
its own modules before it appends `PYTHONPATH` to `sys.path`, so that a module of the project
cannot replace one of them, and writes each step as soon as it observed it, so that an example that
reaches its limit keeps the steps before. An example that hangs is ended with every process it
started; one that dies is `crashed`, with its signal or its exit code, and a target that cannot be
imported exits with 3. A line that a child wrote and cannot be read, cut by a kill or written by
the code under test on the descriptor, ends that example as `crashed` with the steps before it,
and the next example goes on. What a child writes is read up to the bytes of one example; past
them the child is ended and the example is `output-limit`, and so is a command whose output, error
or files pass them. A name of a file of a step that is absolute or has `..` ends the program before
any example runs. An exception whose `__str__` fails is observed with a message that says so.

At `function` a step is `returned` (a tuple as the list that JSON holds), `not_json` with the name
of the type (a set, `NaN`, an infinity) and its `repr`, cut one character past the 1,000 that the
harness keeps so that it can tell a longer one, and left out when `repr` raises; or `raised` with
the name, the full name from `__module__` and `__qualname__`, the classes of its MRO and its
message. A later step with `call` calls that method of what the first step returned, and goes on
after a call that raises; when the first step did not return, no later step is observed, so that
no step moves from its place (ADR-0079). The reader keeps the `repr` with `not_json` of `core`,
cut to 1,000 characters and marked when it was longer. At `cli` the target is split as the
words of a shell, the files of the step are written first, and the exit code, the output, the error
and the regular files of the working directory are observed, decoded as UTF-8 with the character of
replacement; no file reached through a link is observed. The code under test runs in the process
that observes it, so it can rewrite its observation: the expected value never enters the zone,
which is the limit of T1 and part of T2 of ADR-0010.

## The adapter that observes

`PodmanRuntime.observe(image, project, requests, limits)` implements the port that observes of
`core`. It copies the program into a directory of its own with `requests.json`, mounts it read-only
at `/dokime/probe`, and runs `python -I -S` on it in a container with the guarantees of a run. Each
example gets the time of one example and, as its bytes, its share of the bytes of the observations.
A container that ends at a limit, or a program that ends with an error, is refused with
`observation-failed`, quoting what the program wrote on its error output; otherwise
`observations.json` is read with bounds (`observations-missing`, `observations-too-large`,
`observations-unreadable`) into the types of `core`, decimals kept. `observe_program_digest` is the
digest of the program, for the evidence.

Every run, of the tests and of the examples, has its `/tmp` within a quarter of the memory of the
run, so that filling it fails on its size and not on the memory limit, and every file it writes
within 64 MiB (`--ulimit fsize`), in the mounts of the disk too. Known limit: the output directory
is a mount of the disk, whose total podman cannot bound; many files, each within 64 MiB, are bounded
only by the time of the run.

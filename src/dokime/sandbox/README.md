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
and the output writable at `/dokime/out`. Each run has a container of its own, removed however
the run ends; on SIGINT or SIGTERM the adapter removes it and lets the interruption go on.

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
`python -I`. That program sets its own `RLIMIT_AS` and `RLIMIT_CPU` from the limits of reading
before it reads, which is safe with threads; bounds the size; and refuses a `DOCTYPE`. A crash, a
reached limit or an output that is not a report is refused with `report-reader-failed`. The
process bounds the parser; it is not isolation, since it runs with the permissions of the person.
Each test is named by its class name, `::` and its name, as pytest writes it.

The tests of the four guarantees load the container, and run over the list of engines in
`tests/sandbox/engines.py`. A test of an engine that is not installed skips, except in CI, where
it fails.

# Requirements of the `sandbox` scope

The adapters of the verification runtime, and later of the isolation of the agent. This first
increment has the adapter that builds and runs with the `podman` command. Each requirement follows
an EARS template and has at least one test that declares it in its `SDD-EARS:` marker.

## The podman adapter of the verification runtime ([ADR-0041](../adr/0041-the-environment-of-a-verified-project-is-a-dockerfile.md), [ADR-0043](../adr/0043-tests-run-only-on-an-engine-that-enforces-the-limits.md), [ADR-0045](../adr/0045-a-test-report-is-read-by-a-bounded-reader-that-refuses-any-dtd.md), [ADR-0051](../adr/0051-the-adapters-that-run-a-program-are-exempt-from-s603.md))

The adapter implements the port of `core`. It builds with `podman build` and runs with `podman run`,
which share the local store of images. The requirements whose subject is "the verification runtime
adapter" say what the port means, and an adapter of another engine inherits them with their tests,
which run over the list of adapters; those whose subject is "the podman adapter" say how this one
does it. A refusal is raised as the refusal of the port, with the code given here.

Inside the container, the project is mounted at `/dokime/project`, which is also the working
directory, and the output directory at `/dokime/out`.

Known limits: the bases of the stages that the final stage copies from with `COPY --from` are not
recorded; a build stopped at its time limit leaves the working container of `podman build` in the
store of images; with podman 4.9, a run killed by the memory limit is told by the file `oom` that
conmon leaves in its working directory, which is not documented, and if conmon stops writing it the
run is given as "exited" with 137, which still ends without a report; with podman 5.4.2 too, a run
killed by the memory limit was given as "exited" with 137 in 2 of about 12 runs of the whole suite,
not reproduced alone, and the reason is only reasoned: that conmon handles the end of the process
before the event of the memory limit, so that neither podman nor conmon reports it; the process
that reads the report bounds the parser and turns its crash into a refusal, and it is not
isolation: it runs with the permissions of the person who runs the harness.

### Opening

- **SANDBOX-001** If the podman command is not found as an executable program, then the podman adapter shall refuse with the code `podman-not-found`.
- **SANDBOX-002** If the version of podman is older than 4.9, or the adapter cannot read it, then the podman adapter shall refuse with the code `podman-too-old`, quoting the version podman gave.
- **SANDBOX-003** When the podman adapter opens, the podman adapter shall resolve the podman command to an absolute path once and run that path for every command of podman.
- **SANDBOX-004** The podman adapter shall give the absolute path and the version of the podman it runs.
- **SANDBOX-005** If podman ends with an error that no other requirement names, then the podman adapter shall refuse with the code `podman-failed`, quoting what podman wrote on its error output.

### Build

- **SANDBOX-010** When an image is built, the verification runtime adapter shall give the digest of the image it built.
- **SANDBOX-011** When an image is built from a Dockerfile whose final stage starts from an image, the verification runtime adapter shall give as its base the digest of the manifest of the platform of that image.
- **SANDBOX-012** When an image is built from a Dockerfile whose final stage starts from an earlier stage, the verification runtime adapter shall give as its base the base of that earlier stage.
- **SANDBOX-013** When an image is built from a Dockerfile whose final stage starts from `scratch`, the verification runtime adapter shall give no base.
- **SANDBOX-014** When the same Dockerfile is built with the same base image in the store, the verification runtime adapter shall give the same base as every other adapter of the verification runtime.
- **SANDBOX-015** If the build does not end within its time limit, then the verification runtime adapter shall refuse with the code `build-timed-out`, naming the limit.
- **SANDBOX-016** If the build fails, then the verification runtime adapter shall refuse with the code `build-failed`, quoting the last lines that the build wrote.

### The four guarantees of a run

- **SANDBOX-020** While a command runs, the verification runtime adapter shall give it no network.
- **SANDBOX-021** While a command runs, the verification runtime adapter shall keep its memory, swap included, within the memory limit of the run.
- **SANDBOX-022** While a command runs, the verification runtime adapter shall keep the processor time it uses per second on the clock within the processors of the run.
- **SANDBOX-023** While a command runs, the verification runtime adapter shall keep the number of its processes and threads within the processes of the run.
- **SANDBOX-024** While a command runs, the verification runtime adapter shall keep the root of the container read-only.
- **SANDBOX-025** While a command runs, the verification runtime adapter shall mount the project read-only.
- **SANDBOX-026** While a command runs, the verification runtime adapter shall mount the output directory writable.
- **SANDBOX-027** While a command runs, the verification runtime adapter shall give it a writable `/tmp` that is not kept after the run.
- **SANDBOX-028** When a run ends, the verification runtime adapter shall leave the files that the command wrote in the output directory owned by the user who runs the harness.

### The privileges of a run

- **SANDBOX-070** While a command runs, the verification runtime adapter shall give its processes no capabilities.
- **SANDBOX-071** While a command runs, the verification runtime adapter shall keep its processes from gaining privileges by running a program, as the flag `no_new_privs` of Linux does.

### How a run ended

- **SANDBOX-030** When the command ends with an exit code and the engine does not report that the memory limit killed it, the verification runtime adapter shall give the ending "exited" with that exit code, 137 included.
- **SANDBOX-031** When the command ends with the exit code 137 and the engine reports that the memory limit killed it, the verification runtime adapter shall give the ending "memory-limit".
- **SANDBOX-032** When the command has not ended at the time limit of the run, the verification runtime adapter shall give the ending "time-limit".
- **SANDBOX-033** When the harness receives SIGINT or SIGTERM while a command runs, the verification runtime adapter shall remove the container of the run and let the interruption go on.
- **SANDBOX-034** When a run ends in any way, the verification runtime adapter shall leave no container of that run.
- **SANDBOX-035** When a command runs, the podman adapter shall give its container a name that no other run uses.
- **SANDBOX-036** If the project or the output directory is not an existing directory, then the verification runtime adapter shall reject it with an error that names the directory.
- **SANDBOX-037** When a run ends, the verification runtime adapter shall leave the working directory of the harness unchanged.
- **SANDBOX-038** If the user that the image runs as is not root, then the verification runtime adapter shall refuse with the code `user-not-root`, naming the user, before running anything.

### Reading the report

- **SANDBOX-040** When a report is read, the verification runtime adapter shall give, for each test case of the report, its outcome under the name made of its class name, `::` and its name, as in `tests.test_a::test_one`.
- **SANDBOX-041** When a report is read, the verification runtime adapter shall give a test case with a failure as failed, one with an error as error, one marked skipped as skipped, and any other as passed.
- **SANDBOX-042** If the report is larger than its limit of size, then the verification runtime adapter shall refuse with the code `report-too-large`, having read no more than the limit and one byte.
- **SANDBOX-043** If the report has a `DOCTYPE`, then the verification runtime adapter shall refuse with the code `report-has-doctype`.
- **SANDBOX-044** If the report is not well-formed XML, then the verification runtime adapter shall refuse with the code `report-unreadable`.
- **SANDBOX-045** If the report does not exist, then the verification runtime adapter shall refuse with the code `report-missing`, naming its path.
- **SANDBOX-046** If two test cases of the report have the same name, then the verification runtime adapter shall refuse with the code `report-duplicate-test`, naming it.
- **SANDBOX-047** If the path of the report is absolute or has a part `..`, then the verification runtime adapter shall refuse with the code `path-outside-output`, naming the path, before opening anything.
- **SANDBOX-048** If a part of the path of the report, the report included, is a symbolic link, then the verification runtime adapter shall refuse with the code `report-not-a-file`, naming the path, without following the link.
- **SANDBOX-049** If the report is not a regular file, then the verification runtime adapter shall refuse with the code `report-not-a-file`, naming the path.

### The process that reads the report

- **SANDBOX-060** When a report is read, the verification runtime adapter shall parse it in a process other than the process of the harness.
- **SANDBOX-061** When a report is read, the verification runtime adapter shall give the process that reads it the report as the adapter opened it, so that a file put at its path after the opening is not read.
- **SANDBOX-062** When a report is read, the verification runtime adapter shall limit the address space of the process that reads it to the reader memory of the limits of reading.
- **SANDBOX-063** When a report is read, the verification runtime adapter shall limit the processor time of the process that reads it to the reader processor time of the limits of reading.
- **SANDBOX-064** If the process that reads the report ends on a signal, reaches one of its limits or ends without giving a report, then the verification runtime adapter shall refuse with the code `report-reader-failed`.
- **SANDBOX-065** If the version of Expat of the Python that runs the harness is older than 2.8.5, then the verification runtime adapter shall refuse with the code `expat-too-old`, quoting that version, when it opens.
- **SANDBOX-066** The verification runtime adapter shall give the version of Expat that reads its reports.

### The tests of an engine

- **SANDBOX-050** If the engine that a test of the adapter needs is not installed while the tests run in CI, then the test shall fail.

## The program that observes the examples ([ADR-0063](../adr/0063-a-program-of-sandbox-observes-the-examples-inside-the-zone.md))

The program runs inside the container, from a directory mounted read-only: it reads the requests
of the examples, observes each one in a child process, and writes what it saw in the output
directory. It needs nothing but the standard library. The main program runs with `python -I -S`;
each example runs in a child `python -I`, which has the site-packages of the image, since the code
under test needs its dependencies. The adapter that starts it in a container is a later increment.

- **SANDBOX-090** If the main program runs without the isolation of `-I` or with `site` imported, then the main program shall end with an error before it reads any request.
- **SANDBOX-091** When the main program observes the examples, the main program shall run each example in a child Python process of its own, started with `-I`.
- **SANDBOX-092** When the main program runs an example, the main program shall give it a working directory of its own, empty and writable.
- **SANDBOX-093** When the child of an example runs, the child shall run every step of the example in its own process, in order.
- **SANDBOX-094** When the child of an example starts, the child shall import its own modules before it appends to the end of `sys.path` the entries of the variable `PYTHONPATH`.
- **SANDBOX-095** If an example does not end within the time of one example, then the main program shall end its process and every process it started, and observe the example as having reached its limit of time, with the steps observed before.
- **SANDBOX-096** If the process of an example ends by a signal, or with an exit code before it observed its last step, then the main program shall observe the example as crashed, with the signal or the exit code.
- **SANDBOX-097** When a step at `function` returns a value that JSON holds without `NaN` or infinities, the child shall observe the value it returned.
- **SANDBOX-098** If a step at `function` returns a value that JSON cannot hold, then the child shall observe the name of the type of the value.
- **SANDBOX-099** When a step at `function` raises an exception, the child shall observe the name of its class, its full name from `__module__` and `__qualname__`, the full names of the classes of its MRO, and its message.
- **SANDBOX-100** When a step at `cli` runs, the child shall run the target split as the words of a shell with the arguments of the step, give it the standard input of the step, add the variables of the step to the environment, and write the files of the step in the working directory first.
- **SANDBOX-101** When a step at `cli` ends, the child shall observe its exit code, its standard output and its standard error decoded as UTF-8 with the character of replacement, and the regular files of the working directory, decoded the same way.
- **SANDBOX-102** When a step at `cli` reads the files of the working directory, the child shall observe no file that it reaches through a link.
- **SANDBOX-103** When every example has been observed, the main program shall write the observations of all of them to `observations.json` in the output directory.
- **SANDBOX-104** If a line that the child of an example wrote is not valid JSON, or is nested too deep to be read, then the main program shall observe the example as crashed, with the steps of the lines before it, and go on with the next example.
- **SANDBOX-105** If the child of an example writes more bytes than the bytes of one example, then the main program shall end its process and every process it started, and observe the example as having reached its limit of output, with the steps observed before.
- **SANDBOX-106** If the output, the error or the files of a step at `cli` hold more bytes than the bytes of one example, then the child shall read no more than that and end, so that the example is observed as having reached its limit of output.
- **SANDBOX-107** If the name of a file of a step at `cli` is absolute or has a part `..`, then the main program shall end with an error before it runs any example.
- **SANDBOX-108** If the message of an exception raised by a step cannot be read, then the child shall observe the exception with a message that says so.

# ADR-0043 · Tests run only on an engine that enforces the limits

**Status:** proposed

## Context

[ADR-0041](0041-the-environment-of-a-verified-project-is-a-dockerfile.md) makes building and
running two commands, each chosen among `docker`, `podman` and `buildah`, and records as not
checked what the chosen engine does not guarantee besides the absence of network. It was written
without any engine to run. The three have now been run on the corpus, and `buildah run` turns out
to guarantee only the absence of network: the code of the project, and in block C the code of an
agent, would run with no bound on memory, processor or processes and with a writable root.

## Decision

- **Running needs four guarantees.** An engine runs tests only if its adapter enforces no network,
  limits of memory, processor and processes, a read-only root, and an exit status that tells a
  process killed from outside from one that ended by itself. An engine that lacks one is refused
  for running, with the guarantee it lacks named. Being recorded as not checked is no longer enough
  for these four.
- **In the first version, `docker` and `podman` run; `buildah` only builds.** Building may use any
  of the three.
- **The engine that runs must see the image that was built.** The accepted pairs are `docker`
  with `docker`, `podman` with `podman` and `buildah` with `podman`, which share the local store of
  images. Moving an image between stores is not done in the first version.

This amends the part of ADR-0041 on building and running. The rest of ADR-0041 stands, including
what an adapter declares beyond these four.

## Basis

Verified on 2026-11-12 with docker 29.9.3 (daemon, user in the group `docker`), podman 5.4.2
(rootless) and buildah 1.39.3 (rootless), on the image of cachetools built by its pack.

| | docker | podman | `buildah run` |
|---|---|---|---|
| `--network none`: a connection is refused | yes | yes | yes |
| `--memory 256m --memory-swap 256m`, allocating 50 MB blocks | killed at 200–250 MB, exit 137 | same | 600 MB allocated |
| `--pids-limit 64`, starting 200 threads | the 64th cannot start | same | 200 started |
| `--cpus 0.5`, four busy processes, CPU seconds per wall second | 0.50 | 0.50 | 1.59 (two CPUs) |
| `--read-only` | root not writable | same | no such option; root writable |
| `exit 3` / missing command / SIGKILL from outside | 3 / 127 / 137 | 3 / 127 / 137 | 3 / 1 / 1 |

- On an idle host with two CPUs, `--cpus 1` gave 0.98 and 1.00 and no limit gave 1.63 and 1.58, on
  docker and podman.
- With `buildah run`, a run killed from outside and a command that does not exist both end in 1,
  which is also what pytest returns when a test fails. Reading the report keeps them apart only
  when the report is missing.
- The self-check of cachetools gave the same seven witnesses out of ten on the three engines, with
  the twenty reports identical test by test. So the choice of engine does not change the result on
  this project; it changes what is enforced while it runs.
- An image built with `buildah` was listed by `podman images` with the same identifier and ran
  with `podman run --network none --read-only --memory 256m`. `docker images` did not list it.
- Signals sent from inside the container to its PID 1 are ignored, so a kill was tested from
  outside.

The program that loads the container, run as `python /load.py mem|pids|cpu` with each limit:

```python
if what == "mem":  # 50 MB blocks, every page touched, up to 600 MB
    blocks = [bytearray(50 * 1024 * 1024) for _ in range(12)]
elif what == "pids":  # up to 200 threads that sleep
    for n in range(1, 201):
        threading.Thread(target=time.sleep, args=(5,), daemon=True).start()
elif what == "cpu":  # 4 busy processes for 4 seconds; children CPU time over wall time
    ...
```

Read in the sources: the manual of `buildah run` lists `--network`, `--cap-drop` and mounts and no
option for memory, processor, processes or a read-only root, as ADR-0041 already noted.

Not checked: other versions of the engines, docker without root, podman with root, macOS and
Windows, where the engines run inside a virtual machine. Reasoning, without a test: that a bound
on the run is needed before block C, when the code of an agent runs, and also now, since the tests
of a project run any code they import.

## Alternatives considered

- **Keep ADR-0041 as it is**, `buildah run` allowed and the missing guarantees recorded as not
  checked. The evidence would be honest, and a run could still fill the memory of the machine of
  the person or write into the image under test.
- **Only `podman`.** It runs without root and enforces the four guarantees, and leaving `docker`
  out would exclude the engine most people have.
- **Drop `buildah` altogether.** It builds correctly, and with `podman` it shares the store, so
  keeping it as a build engine costs little.
- **Move images between stores** (`podman save` into `docker load`). It allows any pair, and it
  adds a step whose cost grows with the size of the image, for a case no one has asked for.

## Consequences

- On a machine with only `buildah`, the harness can build an image and cannot run tests.
- The two run adapters have to prove the four guarantees in their tests, with a load like the one
  above, not by reading the options they pass.
- The evidence of a run no longer records any of the four as not checked; it still records what
  ADR-0041 leaves to each adapter.
- With `docker`, the daemon runs as root and the report is written as root unless the adapter
  passes the user; with `podman`, a relative path in a mount is taken as the name of a volume, so
  the adapter passes absolute paths. Both are requirements of `sandbox`, not of this decision.
- `buildah` with `docker` is refused, though both are installed on the same machine.

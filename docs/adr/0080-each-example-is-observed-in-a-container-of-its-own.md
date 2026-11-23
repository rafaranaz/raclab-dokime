# ADR-0080 · Each example is observed in a container of its own

**Status:** accepted

## Context

[ADR-0063](0063-a-program-of-sandbox-observes-the-examples-inside-the-zone.md) runs every example of
one side of a gate in one container, each example in a child process of its own, with its own
working directory. Before the cases of B3d that cheat by keeping state between calls, a probe asked
whether an example can leave something for the next one in the same container. It ran on the
podman adapter, with the image of the tests of `sandbox`; each probe had a first example write and
a second, in another child of the same container, read:

| What the first example left | What the second found |
|---|---|
| A file in `/tmp`, and in the working directory's parent, which is `/tmp` | The file |
| A file in `/dokime/out`, the directory where the main program writes the observations | The file |
| A process started with `start_new_session` that writes a counter | The process alive, the counter going from 12 to 17 |
| A segment of System V shared memory and a semaphore, with a fixed key | The text of the segment and the value of the semaphore |
| A key in the keyring of the user, with `add_key` | Nothing: `add_key` and `request_key` give `ENOSYS` |

`/var/tmp`, `/dev/shm`, `/root`, `/dokime/project`, `/dokime` and `/` could not be written. The
main program is the process 1 of the container. So, in one container, an example can pass to the
next what it saw, and the held-out examples of the gate `sealed-examples` are observed in one
container together with their canary.

## Decision

This amends ADR-0063 in its container for each side; the rest of it stands.

**Each example is observed in a container of its own.** The adapter starts one container for each
example of a request, with the same image, mounts, limits and guarantees
([ADR-0043](0043-tests-run-only-on-an-engine-that-enforces-the-limits.md)), and the main program in
it observes that example alone. Its `/tmp`, its `/dokime/out`, its processes and its IPC
namespace end with it, so nothing that an example leaves reaches another. The limits of an example,
its time and its share of the bytes of the observations, are those of ADR-0063, now bounding its
container; the observations of a request are read and given in the order of its examples, as
before.

## Basis

Verified: the probe above, and the start of a container measured on the runner of CI, twenty
observations of one example each in a container of its own through the adapter: a median of 0.503
seconds, between 0.497 and 0.614 (#214); on the machine of the maintainer, between 0.34 and 0.43.

Measured, the cost on the corpus as it is, with two runs on the base, one on the change and the
relations: one container for each example instead of one for each side gives about 12 more
containers for an audit of a contract of mdformat of 5 examples, about 30 with its 3 relations, 36
for the contract of `nextver` of 13 examples and 15 for that of `replace` of 6. At 0.5 seconds,
that is about 6, 15, 18 and 7.5 seconds more for each case; over the cases of each part, about 54
more seconds for part a, now 250, and about 77 for part b, now 117. These are upper bounds, since
an audit may stop before its last gate; part c, the hold-out by hand and the sealed run, was not
counted and is measured in the first run.

Reasoning only: that a list of places to clean between examples cannot be shown to be complete, as
the shared memory of System V, which no file names, shows.

## Alternatives considered

- **Clean up between examples, inside the one container.** The main program, process 1, would kill
  every other process after each example and empty `/tmp` and `/dokime/out`. Discarded: it closes
  the places that were probed and not the ones that were not, and the IPC of System V is one such
  place; the maintainer decided that a channel past the list discards it.
- **A namespace of its own for each child**, with `unshare` inside the container. Discarded: it
  needs a capability that the container does not have and should not.

## Consequences

- **No example sees what another left**: the probes stay as tests of `sandbox`.
- **An example cannot rewrite the observations of another** through `/dokime/out` or a process
  that outlives it, which one container for each side allowed; that it can rewrite its own
  observation stays the limit of ADR-0063 and of T1 and T2 of
  [ADR-0010](0010-threat-model.md).
- **Each example costs a container**, about half a second on the runner; part b of the job
  `corpus` grows with the cases of B3d, and ADR-0078 splits it again past 6 minutes.
- **On the acceptance** of this ADR, ADR-0063 is marked amended by it.

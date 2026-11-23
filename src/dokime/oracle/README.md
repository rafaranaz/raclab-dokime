# oracle

Compares what the zone of verification observed of an example with what the example expects,
outside the zone (ADR-0012, ADR-0063). It imports only `contract` and `core`, and runs nothing: it
receives an example of a checked contract and its observation, and the gate that calls it decides
the verdict. It also splits the examples of a contract into visible and held-out, and builds the
follow-ups of a relation. Its requirements are in [oracle.md](../../../docs/requirements/oracle.md).

```python
from dokime.oracle.compare import compare

comparison = compare(example, observation)
comparison.holds  # True when every expectation of every step held
comparison.differences  # each with its step, its part, what was expected and what was observed
```

Each step is compared with the observation in its position, and only in the parts that it expects,
by `holds` of `contract`: an exact value holds for an equal value of the same type, and each matcher
by its rule. A step that was not observed is a difference that says why: the limit of time, or a
crash with its signal or its exit code when known.

The type of an exception is read as `pytest.raises` reads it, as the maintainer decided on
2026-11-17: `TypeError` is `builtins.TypeError`, `semver.errors.BadPart` is that full name, and the
type holds when it is the full name of any class of the MRO observed. So a subclass of `TypeError`
holds for `TypeError`, a class of the project named `TypeError` that is not one does not, and
`Exception` holds for any exception. A `message` has to hold as well.

A `$repr` holds only for a value that JSON cannot hold whose `repr` was observed whole, not cut at
the 1,000 characters an observation keeps, and is its text (ADR-0079). Any other step gives a
difference in `returns` that says what it did, a value, an exception or the type of a value that
JSON cannot hold, never the `repr` observed. A `repr` that the adapter did not record is a difference marked
`recorded = False`, and `Comparison.recorded` is then false: it says that the zone missed what the
comparison needs, not that the change is wrong, so that a gate can tell it from a failure.

**The limit of `$repr`.** The `repr` is produced by the code under test, inside the zone. A patch
that returns an object whose `__repr__` gives the expected text passes a `$repr` without doing what
is asked. For the visible inputs alone, the held-out examples catch it, as they catch any
special-casing of what is visible; a patch that gives the expected text for every input passes the
held-out examples too, and nothing detects it. That is the limit of ADR-0063, that the code under
test can forge its own observation, while hostile code, T5 of ADR-0010, is out of scope; `$repr`
makes it cheaper, since a `__repr__` is enough, and neither the name of the type would close it,
since it is forged as easily. A value of JSON is not forged so: a class cannot derive from `bool`,
and a subclass of `int` or `str` is written by JSON with its own value. In the cases of G1 the 392
tests of the base pass with each of the five patches: the tests of the project do not detect the
overloaded comparison, the visible examples do.

## The split into visible and held-out (ADR-0014)

```python
from dokime.oracle.holdout import feedback, split

done = split(contract, seed)
done.visible  # the examples the agent sees, in the order of the contract
done.held_out  # one example of each case with two or more
done.without_holdout  # the requirements that hold out nothing, for the evidence
done.cases_without_holdout  # (requirement, case) of each case that holds out nothing

feedback(example, comparison)  # "the requirement a fails a held-out example: stdout, exit"
```

A case is the set of examples of one requirement that share a name of case. The example held out of
a case is chosen with `random.Random(seed).choice` over its examples in the order of the contract,
with one generator for the contract, and a case with none to draw takes nothing from it, so the
split is drawn again from the seed and the examples kept visible, which are both recorded. The seed
is a natural integer that comes from outside. `split(contract, seed, keep_visible)` never draws an
example to keep visible, one already published: the draw of a case is among its other examples, and
a case where none is left holds out nothing. On a held-out failure, `feedback` names the requirement
and the classes of the differences (the part, `files` for any file, `time-limit` or `crashed` for a
step not seen), never a value, an input or the identifier of the example.

## The follow-ups of a relation

`relations` builds the inputs that a relation runs on from a visible source example, and compares
each follow-up with its source (ADR-0076).

```python
from dokime.oracle.relations import holds, in_order, items_of, orders, repeated, words

items = items_of("function", {"args": [[3, 1, 2]]}, "args[0]")  # [3, 1, 2]
for order in orders(items, seed=20261121, permutations=10):  # the reversed order first
    follow_up = in_order("function", {"args": [[3, 1, 2]]}, "args[0]", order)
```

- **`orders(items, seed, permutations)`** gives the reversed order, when it gives another input,
  and up to `permutations` other orders drawn with the seed, as indices of the items. The inputs
  they give are distinct from each other and from the source, items equal in value and type
  counting once, and there are never more than the distinct inputs that the items allow. The same
  seed gives the same orders in the same order: up to 5000 distinct inputs they are a sample of all
  of them, beyond that they are drawn by shuffling.
- **`items_of` and `in_order`** read and permute the list of an argument at `function`, `args[N]`
  or a keyword argument, or the lines of `stdin` or of a file at `cli`, keeping a final line break.
  An input that is absent, or not a list or a text, has no items.
- **`repeated`** gives the follow-up of `idempotent`: the return of the source in the argument
  named, or in the only one, at `function`; the standard output as `stdin`, or the files written,
  at `cli`, by its `via`. A source that raised or exited with another code than zero has none.
- **`holds`** compares a follow-up with its source: the return, by value and type, or the type of
  the exception at `function`; at `cli`, the exit code and the standard output for `via: stdout`,
  the files written for `via: files`, all three for `order-insensitive`. The files are the whole
  working directory after a run, so the file that `over` names, which the follow-up receives
  permuted on purpose, is left out when each run leaves it as it received it, and compared when a
  run rewrites it: what is compared is what each run produced. `holds` takes the input of each run
  for that, `source_given` and `follow_given`, which are required: without them, a caller would
  get the false failure back without a warning.
- **`words`** names the requirement, the relation and the visible source example for the agent,
  never the follow-up nor a value.

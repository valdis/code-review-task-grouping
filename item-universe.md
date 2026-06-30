# Item Universe — Injectability Classification

**Phase-1 §0 prerequisite.** Bounds the checklist to the items that can be planted in a single tidy
commit, so Phase-1 groups draw only from a plantable pool.

Source of truth: [`references/checklist.md`](references/checklist.md) (frozen snapshot). Governed by
[`docs/phase-1-design.md`](docs/phase-1-design.md) §0 and [`docs/corpus-spec.md`](docs/corpus-spec.md) §2
(one commit = exactly one planted issue).

## Injectability definition & rubric

**Injectable** = a *single, self-contained git commit* can introduce one clean, localized instance of
this defect into a real codebase, catchable by a reviewer reading that diff.

- **yes** — one commit plants a clean, localized instance (e.g. Dead Code, Magic Numbers, Error
  Hiding). Eligible for Phase-1 groups.
- **partial** — plantable only with caveats: needs a multi-file commit, a pre-existing host pattern in
  the base repo, or is only a smell-in-context. Note says *what makes it partial*. Usable in Phase-1
  only if the caveat is satisfied by the chosen repo/case.
- **no** — an *evolutionary* or *whole-codebase/cross-file* property needing history or many files, not
  one commit (e.g. Divergent Change, Speculative Generality). **Excluded from Phase-1 groups.**

Cross-references (same plantable defect under two IDs) are noted so group selection treats them as one
injection with multi-tag ground truth ([`methodology.md`](docs/methodology.md) §5).

## §1–§15 (top-level items)

| ID  | Item                                       | injectable | note                                                                                                                                            |
| --- | ------------------------------------------ | ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Redundant comments                         | yes        | One commit can add a comment that restates code; localized.                                                                                     |
| 2   | Unit test coverage (new/changed code)      | partial    | "Missing tests" is an absence — plantable as a commit that adds code without tests, but detection is meta (about the diff, not a code snippet). |
| 3   | SRP — functions                            | yes        | One commit can write a function doing several unrelated things. ≈ 17.4.1, 17.1.1.                                                               |
| 4   | SRP — files                                | partial    | Needs a file already accreting unrelated responsibilities; one commit can push it over. ≈ 16.3.1 (no) when evolutionary.                        |
| 5   | Test file structure                        | partial    | Plantable by adding tests to one giant file, but requires a pre-existing test layout to violate.                                                |
| 6   | Dead Code                                  | yes        | Classic single-commit plant: add an unused var/function/branch. ≈ 16.4.4, 16.7.4.                                                               |
| 7   | Changelog updated                          | no         | Process/repo-convention property; not a code defect in a snippet.                                                                               |
| 8   | Test coverage (explicit)                   | partial    | Same as item 2 — absence-of-tests, meta over the diff.                                                                                          |
| 9   | Tests test requirements not implementation | yes        | One commit can add a test asserting internal details (private calls, exact internals).                                                          |
| 10  | Duplicated literals/constants              | yes        | Add the same literal/list in two spots in one commit. ≈ 16.7.6, 17.1.12.                                                                        |
| 11  | Normalize data/code — remove ambiguity     | partial    | Broad; plantable as e.g. free-text where an enum belongs, but item is a cluster, not one smell.                                                 |
| 12  | Replace heuristics with deterministic      | partial    | Plantable (add a fragile heuristic where deterministic data exists) but needs a fitting host.                                                   |
| 13  | Brittle patterns                           | partial    | Plantable (e.g. order-dependent / index-magic code) but "brittle" is judgement-in-context.                                                      |
| 14  | Generalization vs over-specificity         | partial    | Plantable as an over-fitted test/edge-case, but smell depends on surrounding generality.                                                        |
| 15  | Deep nesting / indentation                 | yes        | One commit can add a deeply-nested function. ≈ 17.4.7 (guard clauses).                                                                          |

## §16 Code Smells

### 16.1 Bloaters

| ID     | Item                | injectable | note                                                                                        |
| ------ | ------------------- | ---------- | ------------------------------------------------------------------------------------------- |
| 16.1.1 | Long Method         | yes        | Add one overly-long function in a single commit. Structural anchor.                         |
| 16.1.2 | Large Class         | no         | Accretes over time/many fields; not one tidy commit (per §0).                               |
| 16.1.3 | Primitive Obsession | partial    | Plantable (pass raw strings/ints where a value object fits) but smell needs domain context. |
| 16.1.4 | Long Parameter List | yes        | Add a function with 6+ params in one commit. Structural. ≈ 17.4.6.                          |
| 16.1.5 | Data Clumps         | partial    | Plantable (same param trio repeated) but needs ≥2 call sites to read as a clump.            |

### 16.2 OO Abusers

| ID     | Item                                      | injectable | note                                                                         |
| ------ | ----------------------------------------- | ---------- | ---------------------------------------------------------------------------- |
| 16.2.1 | Switch Statements                         | yes        | Add a long type-switch/if-else chain that begs polymorphism. ≈ 17.4.8.       |
| 16.2.2 | Temporary Field                           | partial    | Needs a class; plantable as a field set only on some paths.                  |
| 16.2.3 | Refused Bequest                           | partial    | Needs an inheritance host; subclass ignoring parent in one commit. ≈ 17.3.6. |
| 16.2.4 | Alternative Classes, Different Interfaces | no         | Needs two pre-existing parallel classes; cross-file, not one commit.         |

### 16.3 Change Preventers

| ID     | Item                             | injectable | note                                                                      |
| ------ | -------------------------------- | ---------- | ------------------------------------------------------------------------- |
| 16.3.1 | Divergent Change                 | no         | Evolutionary (one class changed for many reasons over time). §0 exemplar. |
| 16.3.2 | Shotgun Surgery                  | no         | Cross-file change-coupling; not one commit. §0 exemplar.                  |
| 16.3.3 | Parallel Inheritance Hierarchies | no         | Needs two coupled hierarchies; structural/cross-file. §0 exemplar.        |

### 16.4 Dispensables

| ID     | Item                     | injectable | note                                                                              |
| ------ | ------------------------ | ---------- | --------------------------------------------------------------------------------- |
| 16.4.1 | Duplicate Code           | yes        | Copy a block to a second location in one commit. ≈ 16.7.2, 17.1.12. Bloat anchor. |
| 16.4.2 | Lazy Class               | partial    | Add a do-little class in one commit, but "doesn't justify itself" is contextual.  |
| 16.4.3 | Data Class               | yes        | Add a fields-only/getters-setters class with no behavior in one commit. ≈ 16.6.2. |
| 16.4.4 | Dead Code                | yes        | §0 exemplar. Add unused code in one commit. ≈ item 6, 16.7.4. Bloat anchor.       |
| 16.4.5 | Speculative Generality   | no         | §0 exemplar — needs an unused-over-time hook; evolutionary. ≈ 17.1.13 (YAGNI).    |
| 16.4.6 | Comments (over-reliance) | yes        | Add confusing code propped up by explanatory comments in one commit. ≈ item 1.    |

### 16.5 Couplers

| ID     | Item                   | injectable | note                                                                            |
| ------ | ---------------------- | ---------- | ------------------------------------------------------------------------------- |
| 16.5.1 | Feature Envy           | partial    | Plantable, but reads as a smell only against the envied object's existing data. |
| 16.5.2 | Inappropriate Intimacy | partial    | Needs a second class whose internals are reached into; multi-unit.              |
| 16.5.3 | Message Chains         | yes        | Add a.getB().getC().getD() train-wreck in one commit if the chain types exist.  |
| 16.5.4 | Middle Man             | partial    | Add a pure-delegation class in one commit, but smell is contextual.             |

### 16.6 OO Design Anti-Patterns

| ID      | Item                    | injectable | note                                                                                       |
| ------- | ----------------------- | ---------- | ------------------------------------------------------------------------------------------ |
| 16.6.1  | God Object / Blob       | no         | Accretes over time; whole-class scope.                                                     |
| 16.6.2  | Anemic Domain Model     | partial    | Plantable as a data-bag + service split, but it's an architecture-level pattern. ≈ 16.4.3. |
| 16.6.3  | Poltergeist             | yes        | Add a short-lived object that only forwards one call, in one commit.                       |
| 16.6.4  | Yo-Yo Problem           | no         | Deep inheritance across many files; structural.                                            |
| 16.6.5  | Sequential Coupling     | yes        | Add methods that must be called in an unenforced order, in one commit. ≈ 18.4.4.           |
| 16.6.6  | Constant Interface      | yes        | Add an interface used only to hold constants, in one commit.                               |
| 16.6.7  | Interface Bloat         | partial    | Add a fat interface in one commit, but smell needs implementers feeling the pain.          |
| 16.6.8  | Singleton Overuse       | yes        | Introduce an unnecessary singleton / hidden global in one commit. ≈ 16.7.10, 17.6.10.      |
| 16.6.9  | Combinatorial Explosion | no         | Requires a growing subclass matrix; structural/evolutionary.                               |
| 16.6.10 | Tramp Data              | partial    | Plantable (thread an unused param through calls) but needs a call chain to read as tramp.  |

### 16.7 General Anti-Patterns

| ID      | Item                    | injectable | note                                                                                         |
| ------- | ----------------------- | ---------- | -------------------------------------------------------------------------------------------- |
| 16.7.1  | Spaghetti Code          | partial    | Tangled control flow plantable in one function, but "no structure" is whole-module.          |
| 16.7.2  | Copy-Paste Programming  | yes        | Duplicate-instead-of-abstract in one commit. ≈ 16.4.1.                                       |
| 16.7.3  | Golden Hammer           | partial    | Plantable (force one tool to fit) but smell needs the misfit context.                        |
| 16.7.4  | Lava Flow               | partial    | Dead code "nobody dares remove" implies history; the dead-code part alone ≈ 16.4.4 (yes).    |
| 16.7.5  | Hard Coding             | yes        | Embed config/path/credential literally in source, in one commit. ≈ 16.7.6, 17.6.10.          |
| 16.7.6  | Magic Numbers / Strings | yes        | §0 exemplar. Add an unexplained literal in one commit. ≈ item 10. Bloat anchor.              |
| 16.7.7  | Error Hiding            | yes        | §0 exemplar. Add an empty/swallowing catch in one commit. ≈ 18.2.4. Data-flow anchor.        |
| 16.7.8  | Action at a Distance    | partial    | Plantable via shared mutable state, but the spooky interaction spans call sites.             |
| 16.7.9  | Flag Arguments          | yes        | §0 exemplar. Add a boolean-dispatch param in one commit. ≈ 17.4.5. Structural anchor.        |
| 16.7.10 | Hidden Dependency       | yes        | Add a function silently relying on global state (not in signature), one commit. ≈ 17.6.10.   |
| 16.7.11 | Premature Optimization  | yes        | Add unjustified micro-optimization/caching obscuring intent, in one commit.                  |
| 16.7.12 | Inner-Platform Effect   | partial    | Reinvent a platform feature; plantable but reads against what the platform offers. ≈ 16.8.5. |

### 16.8 Architectural Anti-Patterns

| ID     | Item               | injectable | note                                                                                                                   |
| ------ | ------------------ | ---------- | ---------------------------------------------------------------------------------------------------------------------- |
| 16.8.1 | Big Ball of Mud    | no         | Whole-architecture property.                                                                                           |
| 16.8.2 | Stovepipe System   | no         | Cross-subsystem integration shape; not one commit.                                                                     |
| 16.8.3 | Database as IPC    | partial    | One commit can add a DB-as-message-bus write, but the anti-pattern is system-level.                                    |
| 16.8.4 | Vendor Lock-in     | partial    | One commit can bind tightly to a proprietary API; "excessive" is system-level judgement.                               |
| 16.8.5 | Reinvent the Wheel | yes        | §0-relevant (README bloat smell). Hand-roll what a known lib provides, in one commit. Bloat anchor. ≈ 16.7.12, 18.3.2. |

## §17 Good Coding Practices

### 17.1 Design Principles

| ID      | Item                               | injectable | note                                                                                     |
| ------- | ---------------------------------- | ---------- | ---------------------------------------------------------------------------------------- |
| 17.1.1  | SOLID — Single Responsibility      | partial    | Class-level SRP needs a class; the function-level form ≈ 3/17.4.1 (yes).                 |
| 17.1.2  | SOLID — Open/Closed                | no         | Property of how code accommodates change over time; evolutionary.                        |
| 17.1.3  | SOLID — Liskov Substitution        | partial    | Plantable as a subtype that breaks the base contract, needs an inheritance host.         |
| 17.1.4  | SOLID — Interface Segregation      | partial    | ≈ 16.6.7; add a fat interface, smell needs implementers.                                 |
| 17.1.5  | SOLID — Dependency Inversion       | partial    | Plantable (depend on a concrete instead of abstraction) but needs the layering host.     |
| 17.1.6  | GoF — Program to an interface      | partial    | Same as 17.1.5.                                                                          |
| 17.1.7  | GoF — Composition over inheritance | partial    | Plantable as a config-flag/inheritance choice, but reads against alternatives. ≈ 16.7.9. |
| 17.1.8  | GoF — Encapsulate what varies      | partial    | Design property; plantable only against a varying-concern host.                          |
| 17.1.9  | GoF — Loosely coupled designs      | partial    | Add tight coupling in one commit, but coupling is relational.                            |
| 17.1.10 | Beck — Passes the tests            | no         | Meta correctness obligation, not a plantable smell.                                      |
| 17.1.11 | Beck — Reveals intention           | yes        | Add a poorly-named/intent-obscuring unit in one commit. ≈ 17.3.7.                        |
| 17.1.12 | Beck — No duplication (DRY)        | yes        | ≈ 16.4.1 / 10; duplicate knowledge in one commit.                                        |
| 17.1.13 | Beck — Fewest elements (YAGNI)     | no         | ≈ 16.4.5; unused-just-in-case needs the "never used" over time.                          |

### 17.2 Architecture

| ID      | Item                                   | injectable | note                                                                                           |
| ------- | -------------------------------------- | ---------- | ---------------------------------------------------------------------------------------------- |
| 17.2.1  | Clean — Dependency Rule                | partial    | Plantable as an inward-pointing violation, but needs an established layer boundary.            |
| 17.2.2  | Clean — Separate concerns into layers  | no         | Whole-codebase layering shape.                                                                 |
| 17.2.3  | Clean — Inner knows nothing of outer   | partial    | One import can violate it, but needs the layered host.                                         |
| 17.2.4  | Clean — Boy Scout Rule                 | no         | Process norm, not a plantable defect.                                                          |
| 17.2.5  | Hexagonal — Ports are interfaces       | no         | Architecture-establishing property.                                                            |
| 17.2.6  | Hexagonal — Adapters implement ports   | no         | Same; architecture shape.                                                                      |
| 17.2.7  | Hexagonal — Core is pure               | partial    | One commit can make a leaf reach for app context, but needs hexagonal host. ≈ 17.6.10.         |
| 17.2.8  | Hexagonal — Driving side               | no         | Architecture role; not a snippet.                                                              |
| 17.2.9  | Hexagonal — Driven side                | no         | Same.                                                                                          |
| 17.2.10 | Hexagonal — Testability by design      | no         | System property.                                                                               |
| 17.2.11 | Hexagonal — Dependency points inward   | partial    | Same as 17.2.1/17.2.3; needs the host.                                                         |
| 17.2.12 | Components — Reuse/Release Equivalence | no         | Component-packaging property.                                                                  |
| 17.2.13 | Components — Common Closure            | no         | Component property.                                                                            |
| 17.2.14 | Components — Acyclic Dependencies      | partial    | One commit can add an import cycle, but needs the component graph.                             |
| 17.2.15 | Components — Stable Dependencies       | no         | Directional-stability property.                                                                |
| 17.2.16 | Components — Stable Abstractions       | no         | Component property.                                                                            |
| 17.2.17 | DDD — Bounded Context                  | no         | Modeling boundary; not a snippet.                                                              |
| 17.2.18 | DDD — Ubiquitous Language              | partial    | Plantable as a misnamed/disinformative concept, ≈ 17.3.10; but the "language" is project-wide. |
| 17.2.19 | DDD — Domain Model                     | partial    | ≈ 16.4.3 anemic; plantable but architecture-flavored.                                          |
| 17.2.20 | DDD — Repository                       | no         | Pattern presence/absence; structural.                                                          |
| 17.2.21 | DDD — Service Layer                    | no         | Structural layering.                                                                           |

### 17.3 Class & Object Design

| ID      | Item                                   | injectable | note                                                                               |
| ------- | -------------------------------------- | ---------- | ---------------------------------------------------------------------------------- |
| 17.3.1  | Encapsulate Variable/Record/Collection | yes        | Expose a mutable field/collection directly in one commit. ≈ 17.3.2.                |
| 17.3.2  | Indecent Exposure                      | yes        | Make internals public unnecessarily in one commit.                                 |
| 17.3.3  | Tell Don't Ask                         | partial    | Plantable (query-then-decide on another object) but needs the object host.         |
| 17.3.4  | Replace Subclass with Delegate         | partial    | Plantable as subclass-for-behavior, needs inheritance host.                        |
| 17.3.5  | Collapse Hierarchy                     | no         | Refactoring opportunity over an existing hierarchy.                                |
| 17.3.6  | Refused Bequest                        | partial    | ≈ 16.2.3; needs inheritance host.                                                  |
| 17.3.7  | Intention-revealing names              | yes        | Add a cryptically-named unit in one commit. ≈ 17.1.11.                             |
| 17.3.8  | Classes nouns, methods verbs           | yes        | Add a verb-named class / noun-named method in one commit.                          |
| 17.3.9  | One word per concept                   | partial    | Add fetch/retrieve/get-mixing names; reads as a smell against existing vocabulary. |
| 17.3.10 | Avoid disinformation                   | yes        | Add a misleading name (e.g. list that's a map) in one commit.                      |

### 17.4 Functions & Methods

| ID      | Item                                   | injectable | note                                                                       |
| ------- | -------------------------------------- | ---------- | -------------------------------------------------------------------------- |
| 17.4.1  | Do one thing                           | yes        | ≈ 3; add a function doing several things, one commit. Structural.          |
| 17.4.2  | One level of abstraction per function  | yes        | Mix high-level policy + low-level detail in one function, one commit.      |
| 17.4.3  | Command-Query Separation               | yes        | Add a function that both mutates and returns state, one commit.            |
| 17.4.4  | No side effects                        | yes        | Add a hidden side effect not implied by the name, one commit. ≈ 16.7.10.   |
| 17.4.4a | Fallback value semantics               | yes        | Add an a \|\| b where fallback has wrong semantics, one commit. Data-flow. |
| 17.4.5  | Remove Flag Argument                   | yes        | ≈ 16.7.9; add a boolean-dispatch param. Structural anchor.                 |
| 17.4.6  | Introduce Parameter Object             | yes        | ≈ 16.1.4; add a long recurring param cluster.                              |
| 17.4.7  | Guard Clauses (vs nested conditionals) | yes        | ≈ 15; add deeply-nested conditionals instead of early returns.             |
| 17.4.8  | Replace Conditional with Polymorphism  | yes        | ≈ 16.2.1; add a type-switch chain.                                         |
| 17.4.9  | Replace Loop with Pipeline             | yes        | Add an imperative loop where map/filter/reduce fits, one commit.           |

### 17.5 Testing

| ID      | Item                             | injectable | note                                                                          |
| ------- | -------------------------------- | ---------- | ----------------------------------------------------------------------------- |
| 17.5.1  | Fast                             | yes        | Add a slow test (sleep/real I/O) in one commit.                               |
| 17.5.2  | Independent                      | yes        | Add a test depending on another's state/order, one commit.                    |
| 17.5.3  | Repeatable                       | yes        | Add a test depending on clock/timezone/network, one commit.                   |
| 17.5.4  | Self-validating                  | yes        | Add a test that prints instead of asserting, one commit.                      |
| 17.5.5  | Timely                           | no         | Process/timing property of when tests are written.                            |
| 17.5.6  | Red-Green-Refactor               | no         | Workflow, not a code defect.                                                  |
| 17.5.7  | Fake It Till You Make It         | no         | TDD workflow technique.                                                       |
| 17.5.8  | Triangulation                    | no         | TDD workflow technique.                                                       |
| 17.5.9  | Assert First                     | no         | Workflow/style of writing a test, not a plantable defect.                     |
| 17.5.10 | Legacy code = code without tests | partial    | Same absence-of-tests as items 2/8; meta over the diff.                       |
| 17.5.11 | Characterization Tests           | no         | Refactoring-process technique.                                                |
| 17.5.12 | Sprout Method/Class              | no         | Refactoring technique.                                                        |
| 17.5.13 | Wrap Method/Class                | no         | Refactoring technique.                                                        |
| 17.5.14 | Extract Interface                | no         | Refactoring technique.                                                        |
| 17.5.15 | Parameterize Constructor/Method  | partial    | Plantable as internal new instead of injection, ≈ 17.1.5; needs DI-able host. |

### 17.6 Scripting & Dynamic Languages

| ID      | Item                                                    | injectable | note                                                                                |
| ------- | ------------------------------------------------------- | ---------- | ----------------------------------------------------------------------------------- |
| 17.6.1  | Use gradual typing                                      | partial    | Add untyped/any code in a typed project, one commit; needs typed host.              |
| 17.6.2  | Runtime schema validation                               | yes        | Consume external data without validation in one commit. ≈ 18.6.4. Data-flow.        |
| 17.6.3  | Type narrowing                                          | yes        | Operate on an uncertain type without a runtime check, one commit.                   |
| 17.6.4  | Strict equality (JS)                                    | yes        | §0 exemplar. Use ==/!= in one commit. JS-footgun anchor.                            |
| 17.6.5  | Mutable default arguments (Python)                      | yes        | Add def f(x=[]) in one commit. JS-footgun analogue (Py).                            |
| 17.6.6  | this context loss (JS)                                  | yes        | §0 exemplar. Pass an unbound method losing this, one commit. JS-footgun anchor.     |
| 17.6.7  | var hoisting (JS)                                       | yes        | Use var with a hoisting bug in one commit.                                          |
| 17.6.8  | Prototype pollution (JS)                                | yes        | Merge untrusted input into a prototype, one commit. Data-flow + security.           |
| 17.6.9  | Global scope pollution (JS)                             | yes        | Add a non-strict global leak in one commit.                                         |
| 17.6.10 | Explicit over implicit (no request context in models)   | yes        | Have a model/service call auth()/session() directly, one commit. ≈ 16.7.10, 17.2.7. |
| 17.6.11 | Avoid eval / dynamic execution                          | yes        | Add an eval/dynamic exec on input, one commit. Data-flow + security.                |
| 17.6.12 | Monkey patching                                         | yes        | Monkey-patch a library in production code, one commit.                              |
| 17.6.13 | Duck typing discipline                                  | partial    | Plantable as an undocumented expected-interface reliance; reads in context.         |
| 17.6.14 | Lint as build failure                                   | no         | CI/config policy, not a snippet.                                                    |
| 17.6.15 | Test coverage non-optional                              | partial    | Absence-of-tests; meta over the diff (items 2/8).                                   |
| 17.6.16 | Pin & validate external contracts                       | partial    | Plantable as an unvalidated external contract, ≈ 17.6.2/18.6.4; partly config.      |
| 17.6.17 | Implicit numeric/narrowing coercion (C/C++/Go/Java/PHP) | no         | Cross-language footgun reference; not plantable in the TS corpus.                   |
| 17.6.18 | Nil receiver / interface-nil comparison (Go)            | no         | Cross-language footgun reference; Go-only, not plantable in the TS corpus.          |
| 17.6.19 | Unsafe nil-chain / safe-navigation misuse (Ruby)        | no         | Cross-language footgun reference; Ruby-only, not plantable in the TS corpus.        |

## §18 Architectural Aspects

### 18.1 Observability & Operability

| ID     | Item                         | injectable | note                                                                       |
| ------ | ---------------------------- | ---------- | -------------------------------------------------------------------------- |
| 18.1.1 | Structured logging           | yes        | Add a concatenated-string log instead of key-value, one commit.            |
| 18.1.2 | Correlation IDs              | partial    | Plantable as a log/span dropping the request ID, but needs a tracing host. |
| 18.1.3 | Health checks / readiness    | no         | System-capability property; not a snippet.                                 |
| 18.1.4 | Alert on symptoms not causes | no         | Ops/alerting-config property.                                              |

### 18.2 API & Contract Design

| ID     | Item                     | injectable | note                                                                               |
| ------ | ------------------------ | ---------- | ---------------------------------------------------------------------------------- |
| 18.2.1 | Postel's Law             | partial    | Plantable as over-strict input / loose output, but reads against contract intent.  |
| 18.2.2 | Semantic versioning      | no         | Release-process property.                                                          |
| 18.2.3 | Backwards compatibility  | partial    | One commit can make a breaking change, but "breaking" needs the existing contract. |
| 18.2.4 | Explicit error contracts | yes        | Return an error without a stable machine-readable code, one commit. ≈ 16.7.7.      |

### 18.3 Dependency Management

| ID     | Item                           | injectable | note                                                                    |
| ------ | ------------------------------ | ---------- | ----------------------------------------------------------------------- |
| 18.3.1 | Pin transitive dependencies    | partial    | Lockfile/manifest edit plantable, but it's a config property.           |
| 18.3.2 | Minimal dependency footprint   | yes        | Add a heavyweight dep for a trivial need, one commit. ≈ 16.8.5, 18.3.4. |
| 18.3.3 | Regular dependency audits      | no         | Process/cadence property.                                               |
| 18.3.4 | One responsibility per package | yes        | Import a 500kb lib for one helper, one commit. ≈ 18.3.2.                |

### 18.4 Concurrency & State

| ID     | Item                                              | injectable | note                                                                                                                |
| ------ | ------------------------------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------------- |
| 18.4.1 | Prefer immutability                               | yes        | Introduce shared mutable state in one commit.                                                                       |
| 18.4.2 | Share-nothing architecture                        | partial    | Plantable as a shared-state-with-locks unit, but architecture-flavored.                                             |
| 18.4.3 | Idempotency                                       | yes        | Add a non-idempotent retried operation in one commit.                                                               |
| 18.4.4 | Make state machines explicit                      | yes        | Add ad-hoc lifecycle flags instead of a state machine, one commit. ≈ 16.6.5.                                        |
| 18.4.5 | Don't assume ownership of shared/global resources | yes        | Prior-experiment anchor. Write a process-wide global without checking prior config, one commit. Data-flow/resource. |

### 18.5 Documentation

| ID     | Item                             | injectable | note                                                                |
| ------ | -------------------------------- | ---------- | ------------------------------------------------------------------- |
| 18.5.1 | Document decisions not mechanics | partial    | Plantable as a what-not-why comment, but reads against an ADR norm. |
| 18.5.2 | Keep docs close to code          | no         | Repo-layout/process property.                                       |
| 18.5.3 | Executable documentation         | no         | Process/preference property.                                        |

### 18.6 Security (as a design property)

| ID     | Item                         | injectable | note                                                                                                           |
| ------ | ---------------------------- | ---------- | -------------------------------------------------------------------------------------------------------------- |
| 18.6.1 | Principle of least privilege | partial    | Plantable as an over-broad permission grant, but needs a privilege host.                                       |
| 18.6.2 | Defence in depth             | no         | System-level layering property.                                                                                |
| 18.6.3 | Fail secure                  | yes        | Add a failure path that defaults to allow, one commit.                                                         |
| 18.6.4 | Validate at boundaries       | yes        | §0 exemplar (missing input validation). Skip validation at a boundary, one commit. ≈ 17.6.2. Data-flow anchor. |

## Summary

Counts over all leaf IDs enumerated above:

- **yes: 63**
- **partial: 50**
- **no: 37**

The `yes` pool is comfortably large enough to build the six comparable Phase-1 groups (~4–5 items each)
spanning the four symptom families named in [`phase-1-design.md`](docs/phase-1-design.md) §1:

- **Data-flow / input-trust:** 18.6.4, 17.6.2, 17.6.8, 17.6.11, 16.7.7, 17.4.4a, 18.4.5, 18.2.4.
- **Structural / shape:** 16.1.1, 16.1.4, 15 / 17.4.7, 16.2.1 / 17.4.8, 16.7.9 / 17.4.5, 17.4.1, 17.4.2.
- **Dispensables / bloat:** 16.4.4, 16.4.1, 16.7.6, 16.8.5, 16.7.2, 18.3.2.
- **JS / dynamic-language footguns:** 17.6.4, 17.6.6, 17.6.7, 17.6.9, 17.6.5, 17.6.10.

Notable cross-references (treat as one injection, multi-tag ground truth): 16.7.9≈17.4.5,
16.4.1≈17.1.12≈10, 16.7.6≈10, 16.7.7≈18.2.4, 16.7.10≈17.4.4≈17.6.10, 15≈17.4.7, 16.2.1≈17.4.8,
16.8.5≈16.7.12≈18.3.2, 18.6.4≈17.6.2.

`partial` items are usable in Phase-1 **only if** the chosen base repo satisfies the noted caveat
(host pattern present, multi-file commit acceptable). Revisit during repo selection (TODO #3) and group
selection (`groups.md`). `no` items are excluded from Phase-1 groups.

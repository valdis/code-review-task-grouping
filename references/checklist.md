---
name: code_review_checklist
description: Comprehensive review checklist — code smells, design principles, architecture, testing, and good practices. Apply selectively based on context; not all items are always relevant.
type: feedback
---

## Meta
- Apply skeptically — not all items matter in every context
- Learn over time which heuristics come into play more often and in what context
- Also propose other changes that improve maintainability and readability beyond the explicit list
- Be skeptical about both the code and the suggested rules — check if they actually apply here

## Learnings Protocol
After every code review, record learnings in `code_review_learnings.md`:
1. **Accepted proposals** — which criterion was applied, in what context it was accepted, and why
2. **Rejected proposals** — which criterion was applied, in what context it was rejected, and why
3. **New criteria** — patterns or issues surfaced during the review not covered by any existing criterion; propose additions to this checklist
4. **Missed issues** — problems not caught by this review process but detected later by another process (CI, production, peer review, etc.); note what criterion would have caught it

## 1. Comments
Remove comments that re-iterate the implementation. If a block needs a comment explaining what it does, consider extracting it into a named function instead.

## 2. Unit Test Coverage
Do we have unit tests for new/changed code?

## 3. Single Responsibility — Functions
Review if functions have single responsibility.

## 4. Single Responsibility — Files
Review if files have single responsibility.

## 5. Test File Structure
Check if unit tests are not in one big file but match file structure to some degree with the units under test.

## 6. Dead Code
Review if we are not introducing dead code (e.g. from iterations that changed code back and forth).

## 7. Changelog
If the project uses changelogs, have we updated it?

## 8. Test Coverage (explicit check)
Check if we have test coverage.

## 9. Tests Test Requirements, Not Implementation
Check if tests are testing requirements/behavior, not internal implementation details.

## 10. No Duplicated Literals/Constants
Check if literals/constants or literal/constant lists are not duplicated across the project. Consider refactoring to a single definition.

## 11. Normalize Data/Code — Remove Ambiguity
- **Data:** canonical forms, strict schemas, fixed vocabularies (enums instead of free text), deduplication, sorting
- **Code:** enforce contracts (types, validation), eliminate side effects, make state explicit, reduce branching to provable cases

## 12. Replace Heuristics with Deterministic Solutions
If we use heuristics, can we replace them with a deterministic solution by augmenting existing data or code?

## 13. Brittle Patterns
Consider brittle patterns or brittle code design. Should we change the approach or requirements to make it less brittle?

## 14. Generalization vs Over-Specificity
Are tests generalised or highly specific to one obscure edge case? Prefer more generalised code and tests. Consider suggesting generalisation options even if that might change app behavior.

## 15. Deep Nesting / Indentation
If a function has many levels of indentation, that's a code smell. Prefer splitting up highly indented code and extracting to named functions — improves readability, maintainability, and testability.

## 16. Code Smells

### 16.1 Bloaters
- 16.1.1 Long Method: method grown too long to understand, change, or test
- 16.1.2 Large Class: too many fields, methods, or lines of code
- 16.1.3 Primitive Obsession: using primitives instead of small domain objects
- 16.1.4 Long Parameter List: more than 3–4 parameters; method does too much
- 16.1.5 Data Clumps: groups of data that always appear together but aren't formalized as an object

### 16.2 OO Abusers
- 16.2.1 Switch Statements: complex switch/if-else chains that should be polymorphism
- 16.2.2 Temporary Field: instance variable only set/used in some circumstances
- 16.2.3 Refused Bequest: subclass inherits but ignores most of parent's behavior
- 16.2.4 Alternative Classes with Different Interfaces: two classes do the same thing with different method names

### 16.3 Change Preventers
- 16.3.1 Divergent Change: one class changed for many different reasons (SRP violation)
- 16.3.2 Shotgun Surgery: one logical change requires editing many classes
- 16.3.3 Parallel Inheritance Hierarchies: adding a subclass in one hierarchy forces one in another

### 16.4 Dispensables
- 16.4.1 Duplicate Code: identical or similar code in more than one location
- 16.4.2 Lazy Class: class that doesn't do enough to justify its existence
- 16.4.3 Data Class: class with only fields, getters, setters — no behavior
- 16.4.4 Dead Code: variables, methods, classes no longer used
- 16.4.5 Speculative Generality: unused hooks added "just in case"
- 16.4.6 Comments: over-reliance on comments to explain confusing code

### 16.5 Couplers
- 16.5.1 Feature Envy: method accesses another object's data more than its own
- 16.5.2 Inappropriate Intimacy: class uses internal fields/methods of another
- 16.5.3 Message Chains: a.getB().getC().getD() — train wreck navigation
- 16.5.4 Middle Man: class delegates most work elsewhere, does little itself

### 16.6 OO Design Anti-Patterns
- 16.6.1 God Object / Blob: one class knows and does everything
- 16.6.2 Anemic Domain Model: domain objects are data bags; all logic in service layers
- 16.6.3 Poltergeist: short-lived object that exists only to call one method on another
- 16.6.4 Yo-Yo Problem: inheritance so deep you bounce between many files to understand behavior
- 16.6.5 Sequential Coupling: methods must be called in a specific order not enforced by types
- 16.6.6 Constant Interface: interface used only to define constants, not behavior
- 16.6.7 Interface Bloat: interface with too many methods; implementers forced to implement irrelevant ones
- 16.6.8 Singleton Overuse: used unnecessarily; introduces hidden global state
- 16.6.9 Combinatorial Explosion: design requires exponentially growing subclasses to cover all combinations
- 16.6.10 Tramp Data: data passed through many methods only used by the final callee

### 16.7 General Anti-Patterns
- 16.7.1 Spaghetti Code: no structure; control flow tangled and hard to follow
- 16.7.2 Copy-Paste Programming: duplicating code instead of abstracting
- 16.7.3 Golden Hammer: applying one familiar tool to every problem regardless of fit
- 16.7.4 Lava Flow: dead code nobody dares remove
- 16.7.5 Hard Coding: config or logic embedded directly in source
- 16.7.6 Magic Numbers / Strings: unexplained literal values with no named constant
- 16.7.7 Error Hiding: catching exceptions and doing nothing
- 16.7.8 Action at a Distance: unexpected interactions via shared mutable state
- 16.7.9 Flag Arguments: boolean param controlling which of two behaviors runs
- 16.7.10 Hidden Dependency: silent reliance on global state not visible in the signature
- 16.7.11 Premature Optimization: optimizing before profiling identifies bottlenecks
- 16.7.12 Inner-Platform Effect: reimplementing what the platform already provides

### 16.8 Architectural Anti-Patterns
- 16.8.1 Big Ball of Mud: no recognizable architecture; everything interconnected
- 16.8.2 Stovepipe System: subsystems integrated ad-hoc with no coordination
- 16.8.3 Database as IPC: using a shared DB as a message bus between components
- 16.8.4 Vendor Lock-in: excessive dependency on a proprietary external component
- 16.8.5 Reinvent the Wheel: building what already exists as proven libraries

## 17. Good Coding Practices

### 17.1 Design Principles
- 17.1.1 SOLID — Single Responsibility: a class should have only one reason to change
- 17.1.2 SOLID — Open/Closed: open for extension, closed for modification
- 17.1.3 SOLID — Liskov Substitution: subtypes must be substitutable for their base types
- 17.1.4 SOLID — Interface Segregation: prefer narrow focused interfaces over fat general ones
- 17.1.5 SOLID — Dependency Inversion: depend on abstractions, not concrete implementations
- 17.1.6 GoF — Program to an interface, not an implementation
- 17.1.7 GoF — Favor composition over inheritance. When a component needs different behavior in different contexts, prefer splitting into composable parts over adding config flags/props that toggle behavior. See also: `code_review_heuristics.md` for worked example.
- 17.1.8 GoF — Encapsulate what varies
- 17.1.9 GoF — Strive for loosely coupled designs
- 17.1.10 Beck — Passes the tests: correctness is the first obligation
- 17.1.11 Beck — Reveals intention: names and structure make purpose obvious
- 17.1.12 Beck — No duplication (DRY / Once and Only Once): every piece of knowledge has one authoritative representation
- 17.1.13 Beck — Fewest elements (YAGNI): remove anything that doesn't serve the three prior rules

### 17.2 Architecture
- 17.2.1 Clean Architecture — Dependency Rule: source code dependencies must always point inward toward higher-level policy
- 17.2.2 Clean Architecture — Separate concerns into layers: entities, use cases, interface adapters, frameworks
- 17.2.3 Clean Architecture — Inner circles must know nothing about outer circles
- 17.2.4 Clean Architecture — Boy Scout Rule: leave the code cleaner than you found it
- 17.2.5 Hexagonal — Ports are interfaces: define what your application needs from the outside world as abstract ports
- 17.2.6 Hexagonal — Adapters are implementations: each external system gets its own adapter implementing a port
- 17.2.7 Hexagonal — Application core is pure: domain and use case layer has zero dependencies on frameworks/databases/transport. Every module is either an **orchestrator** (knows app context, wires things together) or a **leaf unit** (self-contained, receives everything via its interface). When a leaf unit starts reaching for app context (route state, env vars, auth, config), push that knowledge up to the orchestrator. See also: `code_review_heuristics.md` for worked example.
- 17.2.8 Hexagonal — Driving side (primary): adapters that drive the application call inward through ports
- 17.2.9 Hexagonal — Driven side (secondary): adapters the application drives are called outward through ports
- 17.2.10 Hexagonal — Testability by design: swap any adapter for a fake/in-memory implementation without touching the core
- 17.2.11 Hexagonal — Dependency always points inward: the core never imports from adapters
- 17.2.12 Components — Reuse/Release Equivalence: things released together belong in the same component
- 17.2.13 Components — Common Closure: gather classes that change for the same reason at the same time
- 17.2.14 Components — Acyclic Dependencies: no cycles in the component dependency graph
- 17.2.15 Components — Stable Dependencies: depend in the direction of stability
- 17.2.16 Components — Stable Abstractions: stable components should be abstract; unstable ones can be concrete
- 17.2.17 DDD — Bounded Context: explicit boundary within which a domain model applies
- 17.2.18 DDD — Ubiquitous Language: shared vocabulary between developers and domain experts, used in code and conversation
- 17.2.19 DDD — Domain Model: rich objects that hold both data and behavior
- 17.2.20 DDD — Repository: collection-like interface for querying domain objects
- 17.2.21 DDD — Service Layer: thin coordination layer atop the domain; defines application use cases

### 17.3 Class & Object Design
- 17.3.1 Encapsulate Variable / Record / Collection: make data accessible only through functions
- 17.3.2 Indecent Exposure: don't expose more internals as public API than necessary
- 17.3.3 Tell Don't Ask: tell objects what to do rather than querying state and deciding for them
- 17.3.4 Replace Subclass with Delegate: prefer composition/delegation over subclassing for behavior variation
- 17.3.5 Collapse Hierarchy: merge superclass and subclass when the distinction no longer serves a purpose
- 17.3.6 Refused Bequest: if a subclass ignores most of the parent's interface, inheritance is the wrong tool
- 17.3.7 Use intention-revealing names: name should tell you why it exists, what it does, how it is used
- 17.3.8 Classes are nouns, methods are verbs
- 17.3.9 Pick one word per concept: don't use fetch, retrieve, and get interchangeably
- 17.3.10 Avoid disinformation: don't use names that mislead

### 17.4 Functions & Methods
- 17.4.1 Do one thing: a function should do one thing, do it well, do it only
- 17.4.2 One level of abstraction per function: don't mix high-level policy and low-level detail
- 17.4.3 Command-Query Separation: a function either does something or answers something, never both
- 17.4.4 No side effects: a function should do what its name says and nothing hidden
- 17.4.4a Fallback value semantics: when using `a || b` / `a ?? b`, verify the fallback has the same semantic meaning as the primary — same concept, same actor, comparable point in time. If no valid fallback exists, return null/none rather than something misleading. See also: `code_review_heuristics.md` for worked example.
- 17.4.5 Remove Flag Argument: replace boolean-dispatch args with two separate functions
- 17.4.6 Introduce Parameter Object: group recurring parameter clusters into a data structure
- 17.4.7 Replace Nested Conditional with Guard Clauses: handle special cases early, leave the happy path unindented
- 17.4.8 Replace Conditional with Polymorphism: move conditional branches into overriding methods
- 17.4.9 Replace Loop with Pipeline: replace imperative loops with map/filter/reduce

### 17.5 Testing
- 17.5.1 Fast: tests must run quickly to be run often
- 17.5.2 Independent: tests must not depend on each other's state or order
- 17.5.3 Repeatable: same result in any environment
- 17.5.4 Self-validating: pass/fail, no manual inspection required
- 17.5.5 Timely: written just before the production code they test
- 17.5.6 Red-Green-Refactor: failing test → simplest passing code → clean up
- 17.5.7 Fake It Till You Make It: hard-code a return value, generalize only when forced by a second test
- 17.5.8 Triangulation: two tests that together force a general solution
- 17.5.9 Assert First: write the assertion before the test setup
- 17.5.10 Legacy code = code without tests
- 17.5.11 Characterization Tests: capture current actual behavior before changing anything
- 17.5.12 Sprout Method/Class: add new functionality in a new separately-testable unit
- 17.5.13 Wrap Method/Class: preserve existing signatures while adding new behavior
- 17.5.14 Extract Interface: create an interface from a concrete class so a fake can be substituted
- 17.5.15 Parameterize Constructor/Method: inject dependencies instead of creating them internally

### 17.6 Scripting & Dynamic Languages
- 17.6.1 Use gradual typing: TypeScript, Python type hints + mypy/pyright add a compile-time safety net
- 17.6.2 Runtime schema validation: type hints are erased at runtime; validate external data with Zod, Pydantic, etc.
- 17.6.3 Type narrowing: use explicit runtime checks before operating on uncertain types
- 17.6.4 Strict equality (JS): always use === / !==, never ==
- 17.6.5 Mutable default arguments (Python): use None and initialize inside the function
- 17.6.6 this context loss (JS): use arrow functions or .bind()
- 17.6.7 var hoisting (JS): use const/let
- 17.6.8 Prototype pollution (JS): never merge untrusted objects into shared prototypes
- 17.6.9 Global scope pollution (JS): use "use strict" or ES modules
- 17.6.10 Explicit over implicit: prefer dependency injection over global registries or service locators. Models and services must never directly access request context — no `auth()`, `request()`, `session()`. Controllers resolve context and pass it as parameters down the call chain. See also: `code_review_heuristics.md` for worked example.
- 17.6.11 Avoid eval and dynamic code execution
- 17.6.12 Monkey patching sparingly: useful in tests, dangerous in production
- 17.6.13 Duck typing discipline: document expected interfaces explicitly
- 17.6.14 Lint as build failure: treat ESLint/Pylint/Flake8 errors as blocking
- 17.6.15 Test coverage is non-optional in dynamic languages
- 17.6.16 Pin and validate external contracts: use contract tests or schema validation
- 17.6.17 Implicit numeric/narrowing coercion (C/C++/Go/Java/PHP): avoid silent lossy conversions; make widening/narrowing explicit
- 17.6.18 Nil receiver / interface-nil comparison (Go): a typed nil stored in an interface is not `== nil`; a nil pointer receiver still dispatches
- 17.6.19 Unsafe nil-chain / safe-navigation misuse (Ruby): chaining a regular method after `&.` re-introduces the nil crash the `&.` was meant to prevent

## 18. Architectural Aspects

### 18.1 Observability & Operability
- 18.1.1 Structured logging: log events as key-value pairs, not concatenated strings
- 18.1.2 Correlation IDs: propagate a request ID through all logs and spans for end-to-end tracing
- 18.1.3 Health checks and readiness probes: make the system's own status queryable
- 18.1.4 Alerting on symptoms, not causes: alert on user-visible impact, not internal metrics

### 18.2 API & Contract Design
- 18.2.1 Postel's Law (Robustness Principle): be conservative in what you send, liberal in what you accept
- 18.2.2 Semantic versioning: breaking changes bump major, additions bump minor, fixes bump patch
- 18.2.3 Backwards compatibility by default: additive changes only; deprecation cycle before removal
- 18.2.4 Explicit error contracts: every error response has a stable machine-readable code, not just a message

### 18.3 Dependency Management
- 18.3.1 Pin transitive dependencies: lock files prevent surprise breakage from indirect upgrades
- 18.3.2 Minimal dependency footprint: every dependency is a liability; prefer stdlib when feasible
- 18.3.3 Regular dependency audits: security vulnerabilities accumulate silently
- 18.3.4 One responsibility per package: don't import a 500kb library for one utility function

### 18.4 Concurrency & State
- 18.4.1 Prefer immutability: immutable data structures eliminate whole classes of concurrency bugs
- 18.4.2 Share nothing architecture: isolate state per process/actor rather than sharing with locks
- 18.4.3 Idempotency: design operations so they can be safely retried without unintended side effects
- 18.4.4 Make state machines explicit: if something has lifecycle states, model them as a proper state machine
- 18.4.5 Don't assume ownership of shared/global resources: before writing to any process-wide global or singleton (OTel providers, logging root logger, signal handlers, etc.), check whether it has already been configured by the host environment. Libraries and SDKs must be especially conservative — assume you are one of many components in the same process. Enumerate the range of deployment environments (standalone app, embedded library, CI, test harness) and verify the assumption holds in each.

### 18.5 Documentation
- 18.5.1 Document decisions, not mechanics: ADRs capture why, not what
- 18.5.2 Keep docs close to code: docs far from what they describe go stale fastest
- 18.5.3 Executable documentation: prefer tests and examples that run over prose that drifts

### 18.6 Security (as a design property)
- 18.6.1 Principle of least privilege: every component gets only the access it needs
- 18.6.2 Defence in depth: don't rely on a single layer of protection
- 18.6.3 Fail secure: when something goes wrong, default to the safe state (deny, not allow)
- 18.6.4 Validate at boundaries: trust nothing that crosses a system boundary

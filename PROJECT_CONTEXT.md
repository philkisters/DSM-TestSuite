# Distributed Systems Lab — Project Context

## 1. Overview

This project is a distributed-systems teaching platform for a Master's course.

There are approximately **10 student groups**, each consisting of two students.

Each group has:

- Its own GitLab repository
- Its own VM
- A student-developed **Orchestrator**
- Multiple student-developed **Peer** processes

The teaching infrastructure is provided and runs primarily on a separate **Controller VM**.

The same student system is developed incrementally throughout the course:

1. **P2P / Chord**
2. **Distributed storage, replication, timing and consistency**
3. **Consensus / RAFT**

The goal is to let students spend their time implementing and understanding distributed-systems concepts rather than building testing and infrastructure tooling.

The infrastructure therefore provides a central testing environment that can:

- Start and control distributed-system scenarios
- Manipulate network conditions
- Observe network traffic
- Validate system behaviour
- Measure performance
- Track student/group progress

---

## 2. High-Level Architecture

```text
                                               Controller VM
                                                    |
                +-----------------------------------+---------------------------------+
                |                                   |                                 |
                v                                   v                                 v
          +-----------+                      +-------------+                     +-----------+
          |  WebTool  |                      |    Proxy    |                     | TestSuite |
          +-----------+                      +-------------+                     +-----------+
                                                    |                
                               +- - - - - - - - - - + - - - - - - - - - -+               
                               |                    |                    |               
                               v                    v                    v               
                            Group 1             Group 2             Group 3 ... Group 10 
                              VM                   VM                   VM               
                               |                    |                    |               
                         Orchestrator         Orchestrator          Orchestrator         
                               |                    |                    |               
                           +---+---+            +---+---+            +---+---+           
                           |   |   |            |   |   |            |   |   |           
                          P1  P2  P3           P1  P2  P3           P1  P2  P3                       
```
The three infrastructure components provided by the course staff are:

1. Proxy
2. TestSuite
3. WebTool
4. Migrations for PostgreSQL

The two main components implemented by students are:

1. Orchestrator
2. Peers

### Dependencies

The infrastructure components share a PostgreSQL database. A shared Python
`dsm-db` package should provide the SQLAlchemy models used by the TestSuite and
other Python services. Alembic migrations remain the authoritative history of
schema changes and should be kept alongside or packaged with `dsm-db`. Services
may use other database access methods where appropriate (for example, the
Proxy may retain `asyncpg` for high-volume event recording).

The TestSuite owns the REST API used by the WebTool. It manages groups,
challenges, scenario runs, and results, and coordinates scenario execution
through the Orchestrator and Proxy APIs. Long-running scenarios should execute
as background work; API requests should return a run identifier and expose
run status and results.

The WebTool is a Nuxt/Vue frontend that consumes the TestSuite API. It must not
connect directly to PostgreSQL or depend on Python ORM models. The TestSuite
should publish an OpenAPI schema so TypeScript API types or a client can be
generated from the HTTP contract rather than maintained separately. Nuxt
server-side rendering is optional; the primary UI can be a client-rendered
application, with Nuxt server routes added only if a backend-for-frontend is
needed.


## 3. Infrastructure Component: Proxy

The Proxy is the central communication layer used to simulate and observe the distributed network.

Student peers communicate with the Proxy instead of directly communicating with other peers when proxy-based testing is enabled.
```text
  Peer A
    |
    | TCP / JSON
    v
  +--------+
  | Proxy  |
  +--------+
    |
    | TCP / JSON
    v
  Peer B
```

The Proxy is responsible for:

- Routing messages between peers
- Identifying source and destination peers
- Supporting multiple independent virtual networks
- Introducing artificial network conditions
- Recording network traffic
- Providing timing and message metrics

Supported network conditions may include:

 - Delay
 - Message drops
 - Probabilistic message drops
 - Reordering
 - Network partitions
 - Bandwidth/rate limitations (optional/future)

The Proxy should also act as a network flight recorder.

For each message it should be possible to record information such as:

- Timestamp
- Network ID
- Source Peer ID
- Destination Peer ID
- Message type
- Request/correlation ID
- Message size
- Forwarded/dropped/delayed status
- Actual delay
- Logical addressing

Peers have logical addresses:

`Network ID + Peer ID`

Example:
```text
  networkId = group-04
  peerId = 42
```
The Network ID allows multiple independent student networks to exist simultaneously.

The Peer ID identifies a node inside that network.

The physical TCP host/port should be treated as an implementation detail of the Proxy and infrastructure rather than as the logical identity of a peer.

A peer should not need to know the physical address of another peer.

-------------------------

## 4. Infrastructure Component: TestSuite

The TestSuite is the central test and challenge execution system.

It defines and executes distributed-system scenarios against a student group.

A scenario consists conceptually of:
```text
  Initial State
        +
  Actions
        +
  Network Conditions
        +
  Assertions
        +
  Metrics
```

Example:
```text
  scenario: replication-failure

  initial:
    peers: 5
    replication_factor: 3

  actions:
    - put:
        key: image42
    - kill:
        peer: 3
    - get:
        key: image42

  assertions:
    - value_available: true
    - replicas_remaining: ">= 2"
```

The TestSuite can interact with:

- The student Orchestrator
- The Proxy
- The result database

The TestSuite should support several levels of testing:

1. State / Black-box behaviour

Examples:

- GET returns the correct value
- Data remains available after node failure
- Chord lookup returns the correct node
- Replicas converge

2. Protocol / Message behaviour

Examples:

- Required messages were sent
- A retry occurred after a timeout
- A lookup used the expected routing behaviour
- Replication messages reached the required peers
- RAFT election/vote/append messages occurred

Tests should generally validate observable system properties, not force a particular internal implementation unless explicitly required by the exercise.

3. Performance / Metrics

Examples:

- Lookup latency
- Number of messages
- Number of hops
- Recovery time
- Convergence time
- Throughput
- Number of retries

Correctness is more important than performance.

Performance challenges may optionally be used for benchmarks or leaderboards.

-------------------------

## 5. Infrastructure Component: WebTool

The WebTool is the user interface for students and course staff.

It should provide a simple interface for:

- Selecting a student group
- Starting a scenario/challenge
- Viewing test results
- Viewing progress
- Viewing relevant metrics
- Viewing challenge/benchmark results

The WebTool should primarily be a control and visualization layer.

Testing logic belongs in the TestSuite.

Network simulation belongs in the Proxy.

The WebTool should not contain distributed-system test logic itself.

Example:
```text
Group 4

P2P / Chord
  ✓ Peer lifecycle
  ✓ Join
  ✓ Ring correctness
  ✓ Lookup
  ✓ Finger table
  ○ Churn

Replication
  ○ Basic replication
  ○ Node failure
  ○ Recovery

Consistency
  ○ Delayed updates
  ○ Network partition
  ○ Convergence

Consensus / RAFT
  ○ Leader election
  ○ Log replication
  ○ Leader failure
```

------------

## 6. Student Component: Orchestrator

Each student group implements an Orchestrator running on its VM.

The Orchestrator provides a fixed REST API for controlling local peer processes.

The Orchestrator is responsible for:

- Starting peers
- Stopping/leaving peers
- Killing peers
- Joining peers to the network
- Querying peers
- Performing GET operations
- Performing PUT operations

Conceptually:

```text
TestSuite
    |
    | REST
    v
Orchestrator
    |
    +-- start
    +-- join
    +-- leave
    +-- kill
    +-- get
    +-- put
    |
    v
Local Peer Processes
```

The TestSuite should interact with student systems through this defined interface rather than directly managing individual peer processes.

-----------

## 7. Student Component: Peers

The Peers are the actual distributed-system implementation written by the students.

They are responsible for implementing the concepts taught in the course.

The implementation evolves throughout the course:

```text
P2P / Chord
     |
     v
Distributed Storage
     |
     v
Replication
     |
     v
Timing / Consistency
     |
     v
Failure Handling
     |
     v
Consensus
     |
     v
RAFT
```

Peers communicate using the defined TCP/JSON protocol.

When proxy-based testing is enabled, peer-to-peer communication must go through the central Proxy.

Peers use logical peer identities:

```text
Network ID
Peer ID
```
The physical network address is abstracted by the infrastructure.

------

## 8. Architectural Principles

The following principles should be respected by all implementations.

**Separation of concerns**
WebTool = UI
- TestSuite = scenarios, assertions, results
- Proxy = network routing, simulation and observation
- Orchestrator = local process control
- Peers = distributed-system implementation
- Black-box testing

Whenever possible, tests should evaluate observable behaviour rather than inspect student implementation details.

**Deterministic testing**

Network failures and scenarios should ideally be reproducible.

Where randomness is used, scenarios should support a deterministic seed.

**Protocol stability**

The communication protocols between components should be explicit and versioned where necessary.

**Multiple networks**

The infrastructure must support multiple independent student networks running simultaneously.

Network identity must therefore be part of the logical addressing model.

**Progressive complexity**

The infrastructure should support simple direct communication initially and proxy-based network simulation later.

The student architecture should therefore abstract peer addressing from the beginning.

**Reuse**

The same infrastructure should support:

- Chord
- Replication
- Consistency experiments
- Failure scenarios
- Consensus
- RAFT

Avoid building separate infrastructure for each exercise phase.
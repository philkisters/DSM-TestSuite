# DSM TestSuite

The **DSM TestSuite** is a testing and challenge platform for the *Distributed Systems and Middleware (DSM)* Master's course at the University of Hamburg, offered by the [Distributed Operating Systems group (DOS)](https://www.inf.uni-hamburg.de/en/inst/ab/dos/home.html).

The project provides an environment in which students can test, evaluate, and benchmark their implementations of distributed systems while developing a distributed file-sharing platform as part of the course exercises.

Rather than relying exclusively on manually written tests, the platform offers **automated scenarios and gamified challenges** that help students validate their implementations, explore failure scenarios, and gain practical experience with distributed systems.

## Overview

The platform is designed to support the development of distributed systems incrementally throughout the course, covering topics such as:

- **Peer-to-peer systems:** network formation, node discovery, and distributed lookup using Chord.
- **Replication and fault tolerance:** data availability and recovery when nodes fail.
- **Consistency and network behaviour:** message delays, dropped messages, network partitions, and convergence.
- **Consensus:** coordination and leader election, including RAFT.

The goal is to let students focus on implementing and understanding distributed-systems concepts while providing a common environment for testing and experimentation.

## Architecture

The platform consists of three infrastructure components and two student-developed components.

<!-- Replace these placeholders with the actual image paths once the diagrams and screenshots have been added. -->

![DSM TestSuite architecture](/architecture.png)

### Infrastructure components

- **Proxy:** Routes peer-to-peer messages and can simulate network conditions such as delays, message loss, and partitions. It also records message traces and timing information for analysis.
- **TestSuite:** Executes test scenarios, evaluates assertions, collects metrics, and tracks challenge results and progress.
- **WebTool:** Provides a user interface for launching challenges and inspecting results.

### Student components

- **Orchestrator:** A REST API for controlling local peer processes, including starting, joining, leaving, killing, and querying peers.
- **Peers:** The distributed-system implementation developed by students. Peers communicate using the defined network protocol.

Each student group runs its implementation on its own virtual machine. The central infrastructure can test multiple groups independently.

## Web Interface

The WebTool provides a central interface for interacting with the testing platform.

![DSM TestSuite WebTool](docs/images/webtool.png)

Students can use the platform to run challenges and inspect their results. The infrastructure is designed to support both functional correctness checks and measurable performance challenges.

## Testing and Challenges

Tests are organized as scenarios that combine system actions, network conditions, and assertions.

Depending on the exercise, a scenario can:

1. Start and configure a set of peers.
2. Execute operations against the distributed system.
3. Introduce failures or modify network conditions.
4. Verify the resulting system state and behaviour.
5. Collect metrics such as message counts, latency, recovery time, and convergence time.

This allows the same infrastructure to be reused across different distributed-systems topics without requiring a separate testing platform for each exercise.

## Project Status

The platform is under active development for use in the DSM course. Features, interfaces, and setup instructions may evolve as the exercise infrastructure is developed and extended.

## Getting Started

Setup and deployment instructions will be added here as the project stabilizes.

For development-specific information, see the documentation in the relevant component directories.

To run all components run `docker-compose up`.

## Contributing

Contributions, bug reports, and suggestions are welcome. Please open an issue to discuss larger changes before submitting a pull request.

## License

See [LICENSE](LICENSE) for licensing information.

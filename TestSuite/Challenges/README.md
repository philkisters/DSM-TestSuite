# Challenge schema

A challenge is a YAML file containing metadata and an ordered list of steps.
For example, `01-first-peer.yml` uses the following fields:

```yaml
name: first-peer
description: Start a peer, verify it remains registered, and then stop it.
archived: false

steps:
	- action: start-peer
		peer-name: first-peer
	- action: wait
		duration: 1
	- assert: peer-registered
		peer-name: first-peer
	- assert: peers-registered
		number: 1
	- action: wait
		duration: 10
	- assert: peer-registered
		peer-name: first-peer
	- assert: peers-registered
		number: 1
	- action: stop-peer
		peer-name: first-peer
```

## Top-level fields

- `name`: Short identifier for the challenge.
- `description`: Human-readable explanation of the scenario and intended checks.
- `archived`: Boolean indicating whether the challenge is archived.
- `steps`: Sequence of actions and assertions, executed in order.

## Available Steps

### Actions
Actions are active steps that are executed by the TestSuite over the Orchestrator or via the `Proxy` in form of messages to existing peers.

#### Start Peer
Requires a `peer-name` to start a peer on the orchestrator of the currently logged in group. 
This should start a peer with that name and also that peer should register to the registry provided by the `Proxy`.  

#### Stop Peer
Requires a `peer-name`. This stops an already existing peer via the orchestrator. After before stopping it should undregister from the `Proxy`, but doesn't `leave` the P2P network (See `leave-peer`) 

### Assertions
Assertions check for specific state within the network. For this the TestSuite checks with the `Proxy` the current state of the network and might also send a message and investigate the result of that message. 

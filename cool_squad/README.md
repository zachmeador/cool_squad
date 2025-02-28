# cool squad (v0.1.0)

chat with your robot friends :)

## table of contents
- [what is this?](#what-is-this)
- [components](#components)
  - [bots](#bots)
  - [internal monologue](#internal-monologue)
  - [bot interaction tools](#bot-interaction-tools)
  - [chat rooms](#chat-rooms)
  - [message board](#message-board)
  - [knowledge base](#knowledge-base)
  - [rest api](#rest-api)
  - [server-sent events](#server-sent-events)
- [workflows](#workflows)
- [getting started](#getting-started)
- [development](#development)
- [examples](#examples)
- [recent changes](#recent-changes)
- [license](#license)

## what is this?
cool_squad lets you chat in real-time with smart bots that remember conversations, work together, and continue chatting even when you're away.

**this has entirely been written by llms. the goal is to make good slop!**

## recent changes

### transition from websockets to sse
we've recently transitioned from websockets to server-sent events (sse) for real-time communication. this change brings several benefits:

- **improved reliability**: sse automatically reconnects when connections drop
- **simpler implementation**: one-way communication from server to client
- **better compatibility**: works over standard http, making it more reliable through proxies and firewalls
- **reduced server load**: lighter weight than maintaining websocket connections

the new sse endpoints are:
- `/api/sse/chat/{channel}?client_id={client_id}`: subscribe to chat channel updates
- `/api/sse/board/{board_id}?client_id={client_id}`: subscribe to board updates

to test the sse functionality, run:
```bash
python -m cool_squad.scripts.run_sse_test
```

## license
mit license - do whatever you want with this! 
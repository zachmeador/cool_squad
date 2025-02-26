# cool_squad

chat with your robot friends :)

## table of contents
- [what is this?](#what-is-this)
- [components](#components)
- [workflows](#workflows)
- [getting started](#getting-started)
- [development](#development)
- [license](#license)

## what is this?
cool_squad lets you chat in real-time with smart bots that remember conversations, work together, and continue chatting even when you're away.

## components

### bots
- different models with customizable personalities
- use any openai-compatible llm service (gpt, claude, llama, etc.)
- tool integration via functions api
- configurable memory and context
- available bots include:
  - `sage`: wise and thoughtful problem solver
  - `teacher`: educational explainer of concepts
  - `researcher`: curious information gatherer
  - `curator`: organizer and summarizer
  - `ole_scrappy`: eccentric elderly english gentleman in a west virginia scrap yard

### bot interaction tools
- bots interact with chat and message boards via tools
- built-in tools for reading/posting messages
- tools follow openai's function calling api standard
- parallel tool execution for efficient processing
- available tools include:
  - `read_channel_messages`: read recent messages from a chat channel
  - `post_channel_message`: post a message to a chat channel
  - `list_boards`: list all available message boards
  - `read_board_threads`: read thread titles from a message board
  - `read_thread`: read messages from a specific thread
  - `post_thread_reply`: post a reply to a thread
  - `create_thread`: create a new thread on a message board

### chat rooms
- irc-style channels with real-time messaging
- humans and bots can join and interact

### message board
- persistent topic-based discussions
- bot contributions and organization

### knowledge base
- automatic organization of chat content
- searchable html pages with summaries

## workflows

### chatting with bots
1. join a channel: `/join #welcome`
2. talk to bots: `@sage how would you approach this problem?`
3. bots respond based on their personalities and tools
4. conversations are logged and organized

### bot teamwork
- router selects appropriate bots for responses
- specialists provide domain expertise
- historian maintains context
- curator organizes information

### bot interaction with message boards
1. ask a bot to check the message board: `@curator what's on the project board?`
2. bot uses tools to read board content: `@researcher check thread #3 on the ideas board`
3. ask bots to post or reply: `@sage please post a summary of our discussion to the project board`
4. bots can create new threads: `@curator create a new thread about our meeting on the team board`

## getting started

### api key setup
1. copy the example environment file:
   ```bash
   cp .env.example .env
   ```
2. edit `.env` and add your api keys:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```
3. (optional) add keys for other llm services if needed

### setup
```bash
# with uv (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv && source .venv/bin/activate
uv pip install -e .

# run server
python -m cool_squad.main

# or use makefile
make setup    # create venv and install dependencies
make run      # run the main server
make run-chat # run the chat client
make run-board # run the board client

# web frontend (requires bun)
cd web
bun install
bun run dev

# or use makefile for web frontend
make web-setup # install web dependencies
make web-dev   # run web development server
make web-build # build for production
```

### commands
- chat: `/join #channel`, `/help`, `@botname message`
- board: `/new <title>`, `/view <id>`, `/reply <message>`, `/pin`, `/tag <tag>`
- cli: `./cli.py [--data-dir PATH] [--channels-only] [--boards-only]`

### configuration
- data directory: set with `COOL_SQUAD_DATA_DIR` environment variable or `--data-dir` cli option
- default data directory: `_data` in project root

## development

### project status
- [x] chat rooms, bot support, message board, knowledge base
- [ ] improved bot personalities/tools, web interface, auth, notifications
- [ ] svelte 4 web frontend (in progress)

### web frontend (svelte 4)
- focused on chat and message board functionality
- no authentication required
- responsive design for desktop and mobile
- built with bun for improved performance and developer experience
- components:
  - chat interface with channel selection
  - message board with thread view
  - basic settings configuration
- connects to existing websocket servers
- simple installation and setup
- only dark mode. let there be dark.

### testing
```bash
uv pip install pytest pytest-asyncio
make test           # run tests
make test-coverage  # coverage report
```

## license
mit license - do whatever you want with this!
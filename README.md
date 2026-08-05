# OpenCode for Home Assistant

<p align="center">
  <img src="custom_components/opencode/brand/logo.png" alt="OpenCode" width="320"/>
</p>

![GitHub Release](https://img.shields.io/github/v/release/pranjal-joshi/opencode?style=for-the-badge&logo=github&logoColor=white&label=RELEASE&color=10B981)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/pranjal-joshi/opencode/total?style=for-the-badge&logo=homeassistantcommunitystore&logoColor=2341BDF5&label=HACS%20Downloads&color=341BDF5)
[![License](https://img.shields.io/github/license/pranjal-joshi/opencode?style=for-the-badge&logo=scroll&logoColor=white&label=LICENSE&color=orange)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Docs](https://img.shields.io/badge/docs-github.io-8A2BE2?style=for-the-badge)](https://pranjal-joshi.github.io/opencode/)

**Talk to your home with AI.** OpenCode turns [OpenCode Zen](https://opencode.ai/docs/zen/)
— a curated AI gateway with fast, free, OpenAI-compatible models — into Home
Assistant conversation agents. Add DeepSeek, MiniMax, GLM, Kimi, Big Pickle,
and the free models, then chat with your home from Assist, the voice pipeline,
or the conversation UI.

> 👀 **New here?** Start with the [documentation site](https://pranjal-joshi.github.io/opencode/)
> for a guided tour, or jump straight to [Setup](#setup) below — it only takes a
> few minutes and a free API key.

## Features

- 🤖 **Conversation Agent** — Add unlimited agents, one per model, via config subentries
- ⚙️ **AI Tasks** — Generate structured data on demand via the `ai_task.generate_data` service
- 🎤 **Voice Pipeline Ready** — Works with Assist and the voice pipeline
- 🏠 **Home Assistant Control** — Let the model call tools to control devices & entities
- 📎 **Attachments** — Send images/PDFs with your message
- 💬 **Chat Log Streaming** — Real-time token streaming in the conversation UI
- 🆓 **Free Models** — Use the free OpenCode Zen models out of the box

## Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=pranjal-joshi&repository=opencode&category=integration)

### HACS (Recommended)

1. Open Home Assistant → **HACS** → **Integrations** → **⋮** → **Custom repositories**
2. Add `https://github.com/pranjal-joshi/opencode` with category **Integration**
3. Click **Install** → **Restart Home Assistant**

### Manual

1. [Download the latest release](https://github.com/pranjal-joshi/opencode/releases)
2. Extract `custom_components/opencode` into `config/custom_components/`
3. Restart Home Assistant

## Setup

1. Get a free API key from [opencode.ai/auth](https://opencode.ai/auth)
2. Go to **Settings → Devices & Services → Add Integration → OpenCode**
3. Enter your API key (optionally override the Zen endpoint)
4. Click **Add conversation agent**, pick a model, and you're done
5. (Optional) Click **Add AI task**, pick a model for structured data generation

## Documentation

Full instructions, screenshots, and troubleshooting are available on the
[documentation site](https://pranjal-joshi.github.io/opencode/).

## License

MIT — see [LICENSE](LICENSE).

# Whatslang documentation

> Modular WhatsApp bots with a sleek admin console. This is the
> long-form documentation. For the elevator pitch, see the
> [project README](../README.md).

<p align="center">
  <img src="images/hero.svg" alt="Whatslang">
</p>

---

## Read in this order

1. **[Project README](../README.md)** — what Whatslang is and why.
2. **[USAGE.md](../USAGE.md)** — guided tour with screenshots: log in,
   sync chats, start a bot, tune it, read the logs.
3. **[architecture.md](architecture.md)** — what's actually happening
   under the hood. Process model, threading, persistence,
   per-message lifecycle.
4. **[bots.md](bots.md)** — write your own bot. `BotSpec` field
   reference, `MediaMode` enum, prompt cookbook, custom runners.
5. **[configuration.md](configuration.md)** — every environment
   variable, every default, examples per provider.
6. **[deployment.md](deployment.md)** — Docker, Compose, Nixpacks,
   Railpack, bare metal, reverse proxies, healthchecks, sizing.
7. **[api.md](api.md)** — full REST API reference with curl examples.
8. **[security.md](security.md)** — threat model, defences in the
   codebase, operator checklist. Read **before** exposing the service.
9. **[troubleshooting.md](troubleshooting.md)** — when things go
   sideways.

---

## I just want to…

| Goal | Doc |
|---|---|
| **…try it locally in 5 minutes** | [README ▸ Quick start](../README.md#-quick-start) |
| **…deploy it to my server** | [deployment.md](deployment.md) |
| **…understand the dashboard** | [USAGE.md](../USAGE.md) |
| **…write a bot** | [bots.md](bots.md) |
| **…look up an env var** | [configuration.md](configuration.md) |
| **…hit the API from a script** | [api.md](api.md) |
| **…harden it before going live** | [security.md](security.md) |
| **…debug a not-replying bot** | [troubleshooting.md ▸ "Bots aren't replying"](troubleshooting.md#bots-arent-replying) |
| **…understand failure modes & limits** | [architecture.md ▸ Failure modes & limits](architecture.md#failure-modes--limits) |

---

## At a glance

<table>
  <tr>
    <td><img src="images/dashboard-light.svg" alt="Dashboard"></td>
    <td><img src="images/chats.svg" alt="Chats"></td>
  </tr>
  <tr>
    <td><img src="images/chat-detail.svg" alt="Chat detail"></td>
    <td><img src="images/bots.svg" alt="Bots catalog"></td>
  </tr>
  <tr>
    <td><img src="images/diagnostics.svg" alt="Diagnostics"></td>
    <td><img src="images/whatsapp-conversation.svg" alt="WhatsApp conversation"></td>
  </tr>
</table>

> The full screenshot set lives in [`docs/images/`](images/).

---

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for the local setup and the
quality bar (ruff, tsc, vite build).

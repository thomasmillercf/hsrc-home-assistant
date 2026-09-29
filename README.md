# Hemel Ski Race Club for Home Assistant

A HACS integration that reads [hsrc.info](https://hsrc.info) and tracks EARLY Monday training: which sessions are on sale and which ones you've booked.

hsrc.info has no API, so the integration signs in and reads the shop's HTML. It checks once a week, and the automations refresh it before they act.

## Entities

| Entity | What it shows |
| --- | --- |
| `binary_sensor.hsrc_next_early_session_booked` | Whether the next EARLY session is booked, with its date, places left and booking link |
| `sensor.hsrc_unbooked_early_sessions` | How many upcoming EARLY sessions are on sale but not booked, each listed with a booking link |
| `sensor.hsrc_next_booked_early_session` | When the next booked EARLY session starts |
| `calendar.hsrc_early_training` | Every booked EARLY session, 6:00pm to 7:25pm |
| `button.hsrc_add_unbooked_early_sessions_to_basket` | Adds every unbooked EARLY session with places left to your hsrc.info basket, as a Full member |

Refunded orders don't count as bookings.

The basket belongs to your hsrc.info account, so what the button adds shows up when you sign in on any device. Paying still happens on hsrc.info.

## Install

1. In HACS, add `https://github.com/thomasmillercf/hsrc-home-assistant` as a custom integration repository and download it.
2. Restart Home Assistant, then add **Hemel Ski Race Club** under Settings → Devices & services and sign in with your hsrc.info login.
3. Paste [`automations/hsrc.yaml`](automations/hsrc.yaml) into `automations.yaml`, or create each automation in the UI's YAML mode.

The automations:

- add newly released unbooked sessions to your basket and tell you
- at 6pm on Friday, if Monday isn't booked, add it to your basket and remind you
- tell you at 3pm on Monday whether tonight is booked

## Develop

```sh
uv sync
uv run pytest
uvx ruff check .
```

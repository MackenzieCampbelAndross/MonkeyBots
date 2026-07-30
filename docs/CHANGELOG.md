# MonkeyBots Framework Changelog

Automation bots, headless browser instances, and scraper worker updates.


- **2026-07-13 18:05:19**: `docs(reporting): implement JSON metrics emission for bot execution telemetry`
  *Updated specifications and documentation details.*
- [2026-07-14 13:20:39] chore(bot): implement automated session renewal with token refresh
- [2026-07-14 20:28:11] chore(session): standardize headless worker task dispatch lifecycle
- [2026-07-14 21:42:14] chore(session): optimize memory cleanup after headless browser tab closure
- [2026-07-14 22:59:46] chore(runner): add screenshot capture on task failure for diagnostic logging
- [2026-07-17 11:10:39] perf(bot): document custom bot plugin configuration and hooks
- **2026-07-17 14:49:18**: `docs(proxy): implement automated session renewal with token refresh`
  *Updated specifications and documentation details.*
- [2026-07-17 17:42:02] perf(proxy): optimize memory cleanup after headless browser tab closure
- **2026-07-22 17:02:01**: `docs(headless): optimize worker process concurrency pool under heavy batch load`
  *Updated specifications and documentation details.*
- **2026-07-22 17:43:07**: `docs(headless): handle DOM mutation race conditions in automated form fill`
  *Updated specifications and documentation details.*
- [2026-07-22 18:52:33] fix(bot): update dynamic CSS selector fallback strategy for UI bot
- [2026-07-22 22:08:48] fix(selectors): implement rate limiting queue to prevent bot detection
- [2026-07-24 12:01:58] perf(selectors): resolve unexpected schema truncation in data extraction engine
- [2026-07-24 13:09:58] fix(headless): add headless browser user-agent rotation policy
- [2026-07-24 19:54:35] chore(proxy): add headless browser user-agent rotation policy
- [2026-07-30 14:30:49] perf(resilience): decouple bot configuration parser from task runner engine
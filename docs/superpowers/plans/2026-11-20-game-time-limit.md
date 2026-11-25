# Game time limit

1. Add a PIN-protected game setting and account-level game usage. Use server time, deduplicate overlapping devices and expire playback permission after a short lease. Verify persistence, shared usage and denial through the game endpoints.
2. Use the game lease at the full game screen and at the arithmetic challenge. Stop playback on expiry, navigation, background or connection failure. Keep the general usage guard active independently.
3. Add a game section to Parent Mode. Display the server-confirmed limit and measured time with the existing PIN confirmation.
4. Verify parent settings and enforcement in PostgreSQL and Chromium, then record which checks also exercised native code.

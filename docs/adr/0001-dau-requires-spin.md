# DAU counts only Players who completed at least one Spin

A Player is Active on a given day only if they completed at least one Spin — not merely logged in. This means Players who open the app solely to collect a daily bonus are excluded from DAU.

We chose this definition because login-based DAU conflates passive bonus collection with genuine gameplay engagement. In a slot machine game, a Spin is the atomic unit of play; anything less is not engagement. This makes DAU a signal of actual game usage, not app opens.

## Considered options

- **Login-based DAU** — any session counts. Simpler, but inflates the number and obscures the difference between engaged players and bonus farmers.
- **Spin-based DAU (chosen)** — at least one Spin completed. Stricter, but directly tied to the core game loop.

# FFXIV Journey

![Title](image.png)

Sveltekit static site for tracking FFXIV MSQ quest progress.

The goal is to provide a **simple but well enough designed** way to track your progress whilst being **easy to update through datamined** sources.

## TODO

- [ ] Bug: Some MSQ ARR quests are missing.
- [ ] Must do: Replace the usage of old XIVAPI with the new one for unlocks
- [ ] Nice to do: Remove XIVAPI, entirely. Use the datamined data directly. (we use it for unlocks and assets)

Extra:

- [ ] Post-expansion quest separation (labels?)
- [ ] Quest graph viewer?

## Development & Deploy

Check `package.json` for the available scripts.

Deployed to GitHub Pages on push to `main`.

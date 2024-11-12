# FFXIV Journey Tracker

Sveltekit static site for tracking FFXIV MSQ quest progress.

The goal is to provide a **simple but well enough designed** way to track your progress whilst being **easy to update through datamined** sources.

### Preview

<img width="1512" alt="image" src="https://github.com/user-attachments/assets/65e66547-d92b-4ba7-9207-ce187eaa6b9f">
<img width="1510" alt="image" src="https://github.com/user-attachments/assets/4024fd1d-d236-4b5b-bba3-b13a49d47977">

## Dev

Build frontent sveletekit app:

```sh
npm run dev
```

Generate datamined data:

```sh
npm run quests
```

## TODO

- [ ] Convert to new format: `https://beta.xivapi.com/api/1/asset?path=ui%2Ficon%2F100000%2F100064_hr1.tex&format=png`
- [ ] Bug: Some MSQ ARR quests are missing.
- [ ] Must do: Replace the usage of old XIVAPI with the new one for unlocks
- [ ] Nice to do: Remove XIVAPI, entirely. Use the datamined data directly. (we use it for unlocks and assets)

Extra:

- [ ] Post-expansion quest separation (labels?)
- [ ] Quest graph viewer?

## Development & Deploy

Check `package.json` for the available scripts.

Deployed to GitHub Pages on push to `main`.

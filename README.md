# FFXIV Journey - MSQ Tracker

Sveltekit static site app for tracking FFXIV MSQ quest progress.

The goal is to provide a **simple but well enough designed** way to track your progress whilst being **easy to update through datamined** sources.

### Preview

<img width="1742" height="1139" alt="image" src="https://github.com/user-attachments/assets/24162406-44d4-404a-b044-d088f1830a36" />
<img width="1740" height="1165" alt="image" src="https://github.com/user-attachments/assets/f222f383-5b66-47c5-9819-fc8184d8b8cc" />

## Dev

Build and serve app:

```sh
npm run dev
```

Generate datamined data:

```sh
npm run quests
```

## TODO

- [ ] Improve performance, the app, really, should be lightning fast. Currently: acceptable!

Extra:

- [ ] Post-expansion quest separation (labels?)
- [ ] Quest graph viewer? (nah)

## Development & Deploy

Check `package.json` for the available scripts.

Deployed to GitHub Pages on push to `main`.

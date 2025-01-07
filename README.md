# FFXIV Journey Tracker

Sveltekit static site app for tracking FFXIV MSQ quest progress.

The goal is to provide a **simple but well enough designed** way to track your progress whilst being **easy to update through datamined** sources.

### Preview

![ffxiv-journey-1](https://github.com/user-attachments/assets/d4878269-3600-4e64-9dda-79aceebcb2d9)
![ffxiv-journey-2](https://github.com/user-attachments/assets/461c7ebf-842a-4212-81a2-01913a36a22e)

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

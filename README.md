# FFXIV Journey Tracker

Sveltekit static site app for tracking FFXIV MSQ quest progress.

The goal is to provide a **simple but well enough designed** way to track your progress whilst being **easy to update through datamined** sources.

### Preview

<img width="1512" alt="image" src="https://github.com/user-attachments/assets/65e66547-d92b-4ba7-9207-ce187eaa6b9f">
<img width="1510" alt="image" src="https://github.com/user-attachments/assets/4024fd1d-d236-4b5b-bba3-b13a49d47977">

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

- [ ] Bug: Very very few MSQ ARR quests are missing and there are duplicate quests.
- [ ] Improve the 'tree/separator' layout to be more intuitive or add more actions.
- [ ] Improve performance, the app, really, should be lightning fast. Currently: acceptable!

Extra:

- [ ] Post-expansion quest separation (labels?)
- [ ] Quest graph viewer? (nah)

## Development & Deploy

Check `package.json` for the available scripts.

Deployed to GitHub Pages on push to `main`.

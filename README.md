# FFXIV Journey - MSQ Tracker

> [!NOTE]
> The quest list used by the app is updated weekly by a cron parsing datamined sources.

The goal is to provide a super simple way to share and track your MSQ progress, **kupo**.

## Preview

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

## Todo?

- [ ] Improve performance, the app, really, should be lightning fast. Currently: acceptable!
- [ ] Post-expansion quest separation (labels?)
- [ ] Quest graph viewer? (nah)

# How does this work?

The idea of this script is to pre-process Quest data from the datamining repository and convert it into a format that can be used by the application.

### Why?

The goal is to not rely on XIVAPI for quest data, pre-processing data also makes loading faster and for fun; trying to understand how the data is structured.

### Doesn't that mean you have to re-build the application every time the data changes?

Yes.

## Usage

Prepare a python3 venv,

```sh
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
.\.venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

then run,

```sh
cd .. # must be in the root directory
npm run quests
```

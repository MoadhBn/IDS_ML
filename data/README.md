# Data

The raw data is not stored in this repository (course rule: raw data is never versioned). This file explains how to get it.

## Dataset

UNSW-NB15, created by the Cyber Range Lab of UNSW Canberra (Moustafa and Slay, 2015). We use the two official partition files, which are already split by the authors and already contain the flow features:

- `UNSW_NB15_training-set.csv` (about 175,000 flows)
- `UNSW_NB15_testing-set.csv` (about 82,000 flows)

Watch out for the names: the "training" file is the bigger one.

## Where to download

Official page: https://research.unsw.edu.au/projects/unsw-nb15-dataset

Follow the download link on that page, open the folder named "Training and Testing Sets" and download the two CSV files above. The same two files are also mirrored on Kaggle (dataset "UNSW_NB15" by mrwellsdavid) if the official link is slow.

## Where to put the files

Copy both CSV files, without renaming them, into:

```
data/raw/
```

Then check them from the project root:

```
python scripts/check_data.py
```

## Folders

`raw/` holds the files exactly as downloaded. We never edit them by hand.

`processed/` will hold the cleaned versions produced by the notebook. They can always be rebuilt from `raw/`.

import splitfolders

splitfolders.ratio(
    "DatasetWebTech",
    output="output",
    seed=42,
    ratio=(0.7, 0.15, 0.15)
)
# Food Anticipatory Behaviour on European Seabass in Sea Cages: Activity-, Positioning and Density-based approaches

This repository: [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7977064.svg)](https://doi.org/10.5281/zenodo.7977064)

The paper using this repository: [![DOI](https://zenodo.org/badge/DOI/10.3389/fmars.2023.1168953.svg)](https://doi.org/10.3389/fmars.2023.1168953)

The dataset needed to run the code can be found under the DOI: [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.7900273.svg)](https://doi.org/10.5281/zenodo.7900273)

## Installation 

For installation, run:
```
pip install git+https://github.com/I-HaoChen/Food-Anticipatory-Behaviour.git
```
or clone the repository locally and install with
```
git@github.com:I-HaoChen/Food-Anticipatory-Behaviour.git
cd Food-Anticipatory-Behaviour; pip install -e .
```
Now open the python console.
To plot the Figures (the ones who use data) from the paper run:
```
from src.create_figures import create_all_paper_figures
create_all_paper_figures()
```

## License
This repository is licensed under the [Apache 2.0 license](LICENSE).

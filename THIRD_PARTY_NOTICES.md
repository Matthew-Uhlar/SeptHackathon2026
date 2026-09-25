# Third-party notices

SignalReady is built on open-source software and one public dataset. The hackathon rules allow open-source libraries "with proper attribution and in compliance with their licenses". This file provides that attribution.

The repository does not copy or modify any library source code. Libraries are installed by the user from the Python Package Index through requirements.txt and keep their own license files in each installed package folder. The only third-party content stored in this repository is the UCI dataset file described first.

License information below was read from the package metadata of the versions installed from requirements.txt on September 25 2026 (Linux / Python 3.11.15). It is a summary. The license text shipped with each package is authoritative.

## Dataset

**AI4I 2020 Predictive Maintenance Dataset**

| Attribution element | Value |
|---|---|
| Title | AI4I 2020 Predictive Maintenance Dataset |
| Creator | Stephan Matzka |
| Year | 2020 |
| Publisher | UCI Machine Learning Repository |
| DOI / link | https://doi.org/10.24432/C5HS5C |
| License | Creative Commons Attribution 4.0 International (CC BY 4.0) https://creativecommons.org/licenses/by/4.0/ |
| File in this repository | data/ai4i2020.csv |
| Changes | None. The file is the original download (SHA-256 dc6630cd9b1f0f853922fad78a1b6436570d3f1ec863f1dd5c4340ac56bc8a8e on September 25 2026). The app removes columns and repeated rows in memory only. |

Suggested citation: Matzka S. (2020). AI4I 2020 Predictive Maintenance Dataset [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5HS5C

The dataset is provided by its creator as-is under CC BY 4.0. Its creator and UCI do not endorse SignalReady. The readings are synthetic and were generated to reflect real predictive maintenance data. The CC BY 4.0 license of this file is not changed by the Apache 2.0 license of the SignalReady source code (see LICENSE and NOTICE).

data/bad_sample.csv is not a copy of UCI rows. It uses the same column names so the checks can be demonstrated. Its 56 readings were written for this project. None of its reading combinations match a row in data/ai4i2020.csv.

## Direct dependencies

Pinned in requirements.txt or imported directly by app.py / core.py.

| Package | Version | License | Project |
|---|---|---|---|
| Streamlit | 1.64.0 | Apache-2.0 | https://streamlit.io |
| scikit-learn | 1.9.1 | BSD-3-Clause | https://scikit-learn.org |
| pandas | 3.0.6 | BSD-3-Clause | https://pandas.pydata.org |
| joblib | 1.6.0 | BSD-3-Clause | https://joblib.readthedocs.io |
| pytest (tests only) | 9.1.1 | MIT | https://docs.pytest.org |
| NumPy (imported directly, installed with the pins) | 2.4.6 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 (bundled components) | https://numpy.org |
| Vega-Altair (imported directly, installed with Streamlit) | 6.3.0 | BSD-3-Clause | https://github.com/vega/altair |
| Python | 3.11 or later | PSF-2.0 | https://www.python.org |

Streamlit's web front end also bundles third-party JavaScript and fonts. Their notices ship inside the installed streamlit package.

## Other packages installed by requirements.txt

These are pulled in by the packages above. SignalReady does not import them directly. The list is the full dependency closure on Linux.

| Package | Version | License |
|---|---|---|
| anyio | 4.15.1 | MIT |
| attrs | 26.1.0 | MIT |
| certifi | 2026.7.22 | MPL-2.0 |
| charset-normalizer | 3.5.1 | MIT |
| click | 8.5.0 | BSD-3-Clause |
| cloudpickle | 3.1.2 | BSD-3-Clause |
| h11 | 0.16.0 | MIT |
| httptools | 0.8.0 | MIT |
| idna | 3.20 | BSD-3-Clause |
| iniconfig | 2.3.0 | MIT |
| itsdangerous | 2.2.0 | BSD-3-Clause |
| Jinja2 | 3.1.6 | BSD-3-Clause |
| jsonschema | 4.26.0 | MIT |
| jsonschema-specifications | 2025.9.1 | MIT |
| MarkupSafe | 3.0.3 | BSD-3-Clause |
| narwhals | 2.26.0 | MIT |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause |
| pillow | 12.3.0 | MIT-CMU |
| pluggy | 1.6.0 | MIT |
| protobuf | 7.36.2 | BSD-3-Clause |
| pyarrow | 25.0.1 | Apache-2.0 |
| pydeck | 0.9.3 | Apache-2.0 |
| Pygments | 2.21.0 | BSD-2-Clause |
| python-dateutil | 2.9.0.post0 | Apache-2.0 OR BSD-3-Clause (dual) |
| python-multipart | 0.0.32 | Apache-2.0 |
| referencing | 0.37.0 | MIT |
| requests | 2.34.2 | Apache-2.0 |
| rpds-py | 2026.6.3 | MIT |
| SciPy | 1.17.1 | BSD-3-Clause |
| six | 1.17.0 | MIT |
| starlette | 1.7.0 | BSD-3-Clause |
| threadpoolctl | 3.7.0 | BSD-3-Clause |
| toml | 0.10.2 | MIT |
| typing_extensions | 4.16.0 | PSF-2.0 |
| urllib3 | 2.8.0 | MIT |
| uvicorn | 0.54.0 | BSD-3-Clause |
| watchdog | 6.0.0 | Apache-2.0 |
| websockets | 16.1.1 | BSD-3-Clause |

On Windows pip also installs colorama (required by click and pytest on Windows, BSD-3-Clause) and tzdata (required by pandas on Windows, Apache-2.0). These two were not present in the Linux environment used to prepare this list. Check their installed versions with `pip list` on Windows.

The prebuilt NumPy and SciPy packages also bundle compiled math libraries. Their license files list OpenBLAS (BSD-3-Clause) / LAPACK (BSD-3-Clause-Open-MPI) / the GCC runtime library (GPL-3.0-or-later WITH GCC-exception-3.1). The Linux NumPy package also lists libquadmath (LGPL-2.1-or-later). The GCC Runtime Library Exception exists so that programs which merely use these runtime files are not bound by the GPL. LGPL libraries may be used by programs under any license when they are linked dynamically and left unmodified as they are here. SignalReady uses the packages as installed and does not redistribute them. Windows builds of these packages may bundle a different set of libraries. Their license files are in each package's dist-info folder.

The package-level licenses are permissive except certifi (MPL-2.0). MPL-2.0 applies file by file to certifi's own files. SignalReady does not modify or redistribute certifi so it places no obligation on this project's code.

## Tools used during development but not required to run SignalReady

Playwright (Apache-2.0) was used in a separate environment to drive a headless browser for manual interface checks. It is not in requirements.txt and is not needed to install / run / test the app.

## License compatibility summary

Every dependency uses a permissive license (Apache-2.0 / BSD / MIT / PSF / MIT-CMU / Zlib / CC0) or MPL-2.0 for an unmodified package. The GCC runtime bundled inside the NumPy and SciPy packages carries the GCC Runtime Library Exception. None of these requires SignalReady's own code to use a particular license. Any common open-source license for the SignalReady code (for example MIT or Apache-2.0) is compatible. The dataset keeps its CC BY 4.0 terms and needs the attribution above wherever the file is shared.

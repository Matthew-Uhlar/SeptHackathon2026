"""Download the original UCI sample without modifying its readings."""
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile
from io import BytesIO
URL='https://archive.ics.uci.edu/static/public/601/ai4i+2020+predictive+maintenance+dataset.zip'
if __name__ == '__main__':
    with urlopen(URL, timeout=60) as response:
        archive=ZipFile(BytesIO(response.read()))
    name=next(n for n in archive.namelist() if n.endswith('ai4i2020.csv'))
    out=Path(__file__).parent/'data/ai4i2020.csv'
    out.parent.mkdir(exist_ok=True)
    out.write_bytes(archive.read(name))
    print(f'Saved sample to {out}')

# PyPipeline
[![PyPI version](https://badge.fury.io/py/py-pipeline.svg)](https://badge.fury.io/py/py-pipeline)
![Supported versions](https://img.shields.io/badge/python-3.10+-blue.svg)
[![Downloads](https://static.pepy.tech/badge/py-pipeline)](https://pepy.tech/project/py-pipeline)
[![license](https://img.shields.io/github/license/zigai/py-pipeline.svg)](https://github.com/zigai/py-pipeline/blob/main/LICENSE)

```PyPipeline``` is a simple Python framework for building data processing pipelines.

# Overview     
- Pipelines are built by chaining multiple ```Actions``` and evaluating them on data
- Two types of ```Actions```:
	- ```Filters``` discard pipeline items based on provided conditions. Discarded items are ignored by subsequent actions
	- ```Transformers``` modify item data
- Easily create CLIs for you pipeline
- Use multiple CPU cores for processing

# Installation
#### From PyPi
```
pip install py-pipeline
```
#### From source
```
pip install git+https://github.com/zigai/py-pipeline.git
```
# License
[MIT License](https://github.com/zigai/py-pipeline/blob/master/LICENSE)

# gentle-python-pptx

This library is created for repetitive processing large pptx presentations more CPU- and memory- effective than [python-pptx](https://github.com/scanny/python-pptx) library.


## Persisting cache feature

The library caches all properties calculated from the xml and allows to save the cache and restore it on the second pptx-file load.


## PPTX parsing status

`gentle-python-pptx` handles but `python-pptx` don't:
- Colors
- Nested text formatting
- Shapes adding/removal/duplication
- Slides adding/removal/duplication

`python-pptx` handles but `gentle-python-pptx` don't:
- Specification-right pptx parsing
- Tables
- Charts
- Notes slides


## How to use

```python
from gpptx.load import PresentationContainer

with open('file.pptx', mode='rb') as f:
    container = PresentationContainer(f)
    presentation = container.presentation
    # ...
```

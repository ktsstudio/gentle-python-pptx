import re
from typing import Optional

SLIDES_PATH_PREFIX = 'ppt/slides/'
SLIDES_PATH_PREFIX_WITH_FILE = 'ppt/slides/slide'
SLIDE_MASTERS_PATH_PREFIX = 'ppt/slideMasters/'
SLIDE_MASTERS_PATH_PREFIX_WITH_FILE = 'ppt/slideMasters/slideMaster'
SLIDE_LAYOUTS_PATH_PREFIX = 'ppt/slideLayouts/'
SLIDE_LAYOUTS_PATH_PREFIX_WITH_FILE = 'ppt/slideLayouts/slideLayout'
THEMES_PATH_PREFIX = 'ppt/theme/theme'
THEMES_PATH_PREFIX_WITH_FILE = 'ppt/theme/theme'
MEDIA_PATH_PREFIX = 'ppt/media/'
MEDIA_IMAGES_PATH_PREFIX = 'ppt/media/image/'
ROOT_RELS_PATH_PREFIX = 'ppt/_rels/'
PRESENTATION_PATH = 'ppt/presentation.xml'
CONTENT_TYPES_PATH = '[Content_Types].xml'

_PATH_DIR_NAME_REGEX = re.compile('^(ppt.*)/([^/]+)$')


def pptx_join_path(*parts: str) -> str:
    return '/'.join(part.strip('/') for part in parts)


def make_slide_path(index: int) -> str:
    return f'{SLIDES_PATH_PREFIX}slide{index}.xml'


def make_slide_master_path(index: int) -> str:
    return f'{SLIDE_MASTERS_PATH_PREFIX}slideMaster{index}.xml'


def make_slide_layout_path(index: int) -> str:
    return f'{SLIDE_LAYOUTS_PATH_PREFIX}slideLayout{index}.xml'


def make_theme_path(index: int) -> str:
    return f'{THEMES_PATH_PREFIX}theme{index}.xml'


def make_rels_path(filepath: str) -> Optional[str]:
    match = _PATH_DIR_NAME_REGEX.match(filepath)
    dir_ = match.group(1)
    name = match.group(2)
    return f'{dir_}/_rels/{name}.rels'


def absolutize_filepath_relatively_to_content_dirs(filepath: str) -> str:
    return filepath.replace('../', 'ppt/')


def absolutize_filepath_relatively_to_root(filepath: str) -> str:
    return f'ppt/{filepath}'


def relativize_filepath_relatively_to_content_dirs(filepath: str) -> str:
    return filepath.replace('ppt/', '../')


def relativize_filepath_relatively_to_root(filepath: str) -> str:
    return filepath.replace('ppt/', '')


def find_last_index_of_content(loader, content_name: str, dir_name: Optional[str] = None) -> int:
    if dir_name is None:
        dir_name = f'{content_name}s'

    path_index_regex = re.compile(rf'^ppt/{dir_name}/{content_name}(\d+)')

    last_index = 0

    for filename in loader.get_filelist():
        if not filename.startswith(f'ppt/{dir_name}/'):
            continue
        if filename.endswith('.rels'):
            continue
        result = path_index_regex.match(filename)
        index = int(result.group(1))
        last_index = max(last_index, index)

    return last_index

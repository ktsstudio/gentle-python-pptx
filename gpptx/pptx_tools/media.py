from gpptx.pptx_tools.paths import MEDIA_PATH_PREFIX
from gpptx.pptx_tools.rels import get_all_relation_paths_in_rels
from gpptx.storage.pptx.loader import Loader


def delete_unused_media(loader: Loader) -> None:
    media_filepaths = [it for it in loader.get_filelist() if it.startswith(MEDIA_PATH_PREFIX) and not it.endswith('.rels')]
    rels_filepaths = [it for it in loader.get_filelist() if it.endswith('.rels')]

    media_used_filepaths = set()

    for rels_filepath in rels_filepaths:
        relation_paths = get_all_relation_paths_in_rels(loader=loader, rels_filepath=rels_filepath)
        for it in relation_paths:
            media_used_filepaths.add(it)

    for media_filepath in media_filepaths:
        if media_filepath not in media_used_filepaths:
            loader.delete_file(media_filepath)

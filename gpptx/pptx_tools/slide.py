from gpptx.pptx_tools.content_type import delete_mention_in_content_type
from gpptx.pptx_tools.media import delete_unused_media
from gpptx.pptx_tools.paths import make_slide_path, make_rels_path, PRESENTATION_PATH, find_last_index_of_content
from gpptx.pptx_tools.presentation import delete_slide_mention_in_presentation
from gpptx.pptx_tools.rels import find_relation_id_in_rels, delete_mention_in_rels
from gpptx.pptx_tools.xml_namespaces import pptx_xml_ns
from gpptx.storage.pptx.loader import Loader


def delete_mention_in_slide(loader: Loader, slide_id: int, slide_id_to_delete: int):
    slide_filepath_to_delete = f'slide{slide_id_to_delete}.xml'
    slide_filepath = make_slide_path(slide_id)
    slide_rels_filepath = make_rels_path(slide_filepath)
    r_id = find_relation_id_in_rels(loader=loader, rels_filepath=slide_rels_filepath, filepath=slide_filepath_to_delete)
    if r_id is None:
        return
    delete_shapes_with_relation(loader=loader, slide_filepath=slide_filepath, r_id_to_delete=r_id)
    delete_mention_in_rels(loader=loader, rels_filepath=slide_rels_filepath, relation_id=r_id)


def delete_shapes_with_relation(loader: Loader, slide_filepath: str, r_id_to_delete: str):
    xml = loader.get_file_xml(slide_filepath)

    items_xml = xml.xpath(f'.//p:sp//*[@r_for_ids:id="{r_id_to_delete}"]/ancestor-or-self::p:sp', namespaces=pptx_xml_ns)
    for it in items_xml:
        it.getparent().remove(it)

    loader.save_file_xml(slide_filepath, xml)


def delete_slide(loader: Loader, slide_index: int, do_garbage_collection: bool = True):
    slide_filepath = make_slide_path(slide_index)
    slide_rels_filepath = make_rels_path(slide_filepath)
    presentation_rels_filepath = make_rels_path(PRESENTATION_PATH)

    # delete slide xml
    try:
        loader.delete_file(slide_filepath)
    except KeyError:
        return
    loader.delete_file(slide_rels_filepath)

    # delete relations
    if do_garbage_collection:
        delete_unused_media(loader=loader)

    last_pptx_slide_index = find_last_index_of_content(loader=loader, content_name='slide')
    for i in range(1, last_pptx_slide_index + 1):
        delete_mention_in_slide(loader=loader, slide_id=i, slide_id_to_delete=slide_index)

    # update presentation xml
    slide_relation_id = find_relation_id_in_rels(loader=loader,
                                                 rels_filepath=presentation_rels_filepath,
                                                 filepath=slide_filepath)
    assert slide_relation_id is not None
    delete_mention_in_rels(loader=loader, rels_filepath=presentation_rels_filepath, relation_id=slide_relation_id)
    delete_slide_mention_in_presentation(loader=loader, relation_id=slide_relation_id)

    # update content type xml
    delete_mention_in_content_type(loader=loader, filepath=slide_filepath)


def delete_all_slides_except(loader: Loader, slide_index: int) -> None:
    last_slide_index = find_last_index_of_content(loader=loader, content_name='slide')

    for i in reversed(range(1, last_slide_index + 1)):
        if i == slide_index:
            continue
        delete_slide(loader=loader, slide_index=i, do_garbage_collection=False)

    delete_unused_media(loader=loader)

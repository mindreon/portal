"""列表分页：默认每页 10 条，单次最多 100 条，避免一次把整表拖进内存。"""

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100


def clamp_page(page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> tuple[int, int, int]:
    """把页码、每页条数夹到合法范围，并算出 SQL OFFSET。"""
    page = max(1, page)
    page_size = min(max(1, page_size), MAX_PAGE_SIZE)
    offset = (page - 1) * page_size
    return page, page_size, offset

from pydantic import BaseModel


class PageOut[T](BaseModel):
    """列表接口统一翻页形状。items 是当前页，total 是符合筛选的总条数。"""

    items: list[T]
    total: int
    page: int
    page_size: int

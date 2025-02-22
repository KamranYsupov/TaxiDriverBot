import math
from typing import Sequence


class Paginator:
    def __init__(
        self,
        array: Sequence,
        page_number: int = 1,
        per_page: int = 1,
    ):
        self.array = array
        self.page_number = page_number
        self.per_page = per_page
        self.pages = math.ceil(len(self.array) / self.per_page)

    def get_page(self):
        begin = (self.page_number - 1) * self.per_page
        end = begin + self.per_page
        return self.array[begin: end]

    def has_next(self):
        return self.page_number < self.pages

    def has_previous(self):
        return self.page_number > 1
    
    
def get_pagination_buttons(paginator: Paginator, prefix: str) -> dict:
    buttons = {}
    
    if paginator.has_previous():
        buttons['◀️ Пред.'] = f'{prefix}_{paginator.page_number - 1}'
    if paginator.has_next():
        buttons['След. ▶️'] = f'{prefix}_{paginator.page_number + 1}'
    
    
        
    return buttons
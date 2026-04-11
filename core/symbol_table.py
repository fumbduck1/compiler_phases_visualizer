from typing import Dict, Optional, Any


class SymbolTable:
    def __init__(self):
        self.symbols: Dict[int, Dict[str, Any]] = {}
        self.name_to_index: Dict[str, int] = {}
        self._next_index = 1

    def add(
        self, name: str, token_type: str = "id", dtype: Optional[str] = None
    ) -> int:
        if name in self.name_to_index:
            return self.name_to_index[name]

        index = self._next_index
        self._next_index += 1

        self.symbols[index] = {
            "name": name,
            "type": token_type,
            "dtype": dtype,
            "value": None,
        }
        self.name_to_index[name] = index
        return index

    def get(self, name: str) -> Optional[Dict[str, Any]]:
        if name in self.name_to_index:
            idx = self.name_to_index[name]
            return self.symbols[idx]
        return None

    def get_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        return self.symbols.get(index)

    def update(self, name: str, **kwargs):
        if name in self.name_to_index:
            idx = self.name_to_index[name]
            self.symbols[idx].update(kwargs)

    def to_list(self):
        return [{"index": idx, **sym} for idx, sym in self.symbols.items()]

    def clear(self):
        self.symbols.clear()
        self.name_to_index.clear()
        self._next_index = 1

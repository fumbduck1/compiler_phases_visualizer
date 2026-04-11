from typing import List, Optional
from utils.token import Token


class ErrorRecovery:
    @staticmethod
    def panic_mode(tokens: List[Token], error_token_idx: int, valid_tokens: set) -> int:
        idx = error_token_idx + 1
        while idx < len(tokens) and tokens[idx].type not in valid_tokens:
            if tokens[idx].type == "SEMICOLON" or tokens[idx].type == "EOF":
                break
            idx += 1
        return min(idx, len(tokens) - 1)

    @staticmethod
    def statement_mode(tokens: List[Token], error_token_idx: int) -> int:
        for i in range(error_token_idx + 1, len(tokens)):
            if tokens[i].type == "SEMICOLON":
                return i
        return len(tokens) - 1

    @staticmethod
    def skip_to_synchronization(
        tokens: List[Token], start_idx: int, follow_set: set
    ) -> int:
        idx = start_idx
        while idx < len(tokens):
            if tokens[idx].type in follow_set:
                break
            idx += 1
        return idx

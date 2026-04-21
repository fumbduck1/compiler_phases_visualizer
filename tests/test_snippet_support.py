import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.lexer import lex
from core.parser import parse
from core.semantic import analyze_semantics
from core.intermediate import generate_intermediate_code
from core.optimizer import optimize
from core.codegen import generate_code
from utils.token import TokenType


def test_lexer_recognizes_for_loop_tokens():
    source = "for(int i=0;i<=100;i++){x=x+i;}"
    tokens, _, errors = lex(source)

    assert not errors
    assert tokens[0].type == TokenType.KEYWORD and tokens[0].lexeme == "for"
    assert any(token.type == TokenType.LE for token in tokens)
    assert any(token.type == TokenType.INC for token in tokens)
    assert any(token.type == TokenType.LBRACE for token in tokens)
    assert any(token.type == TokenType.RBRACE for token in tokens)


def test_parser_builds_program_and_for_node():
    source = "for(int i=0;i<=100;i++){x=x+i;}"
    tokens, symbol_table, _ = lex(source)
    ast, parse_errors = parse(tokens, symbol_table)

    assert not parse_errors
    assert ast is not None
    assert ast.node_type == "program"
    assert len(ast.children) == 1
    assert ast.children[0].node_type == "for"


def test_full_pipeline_handles_loop_snippet():
    source = "for(int i=0;i<=100;i++){x=x+i;}"
    tokens, symbol_table, lex_errors = lex(source)
    ast, parse_errors = parse(tokens, symbol_table)
    semantic_ast, sem_errors, coercions = analyze_semantics(ast, symbol_table)
    tac = generate_intermediate_code(semantic_ast)
    optimized = optimize(tac)
    assembly = generate_code(optimized)

    assert not lex_errors
    assert not parse_errors
    assert not sem_errors
    assert semantic_ast is not None
    assert coercions is not None
    assert any(instr.op == "label" for instr in tac)
    assert any(instr.op == "jz" for instr in tac)
    assert any(line.endswith(":") for line in assembly)
    assert any("JMP" in line for line in assembly)
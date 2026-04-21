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
from gui.visual_helpers import VisualHelpers
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


def test_tac_for_loop_flow_is_init_cond_body_step():
    source = "for(int i=0;i<=3;i++){x=x+i;}"
    tokens, symbol_table, _ = lex(source)
    ast, _ = parse(tokens, symbol_table)
    semantic_ast, _, _ = analyze_semantics(ast, symbol_table)
    tac = generate_intermediate_code(semantic_ast)

    text_lines = [str(instr) for instr in tac]

    cond_idx = next(i for i, line in enumerate(text_lines) if line.startswith("label for_cond_"))
    body_idx = next(i for i, line in enumerate(text_lines) if line.startswith("label for_body_"))
    step_idx = next(i for i, line in enumerate(text_lines) if line.startswith("label for_step_"))
    end_idx = next(i for i, line in enumerate(text_lines) if line.startswith("label for_end_"))

    assert cond_idx < body_idx < step_idx < end_idx
    assert any(line.startswith("jz ") and "for_end_" in line for line in text_lines)
    assert any(line == "id1 = id1 + 1" for line in text_lines)


def test_tac_string_has_no_type_suffix_annotations():
    source = "int x=1;"
    tokens, symbol_table, _ = lex(source)
    ast, _ = parse(tokens, symbol_table)
    semantic_ast, _, _ = analyze_semantics(ast, symbol_table)
    tac = generate_intermediate_code(semantic_ast)
    optimized = optimize(tac)

    tac_text = [str(instr) for instr in tac]
    optimized_text = [str(instr) for instr in optimized]

    assert all(":int" not in line and ":float" not in line for line in tac_text)
    assert all(":int" not in line and ":float" not in line for line in optimized_text)


def _collect_tree_labels(tree):
    labels = [tree.get("label", "")]
    for child in tree.get("children", []):
        labels.extend(_collect_tree_labels(child))
    return labels


def test_tree_literal_labels_omit_num_prefix():
    source = "for(int i=0;i<=3;i++){x=x+i;}"
    tokens, symbol_table, _ = lex(source)
    ast, _ = parse(tokens, symbol_table)
    semantic_ast, _, _ = analyze_semantics(ast, symbol_table)

    syntax_tree = VisualHelpers._to_syntax_tree_model(ast, symbol_table)
    semantic_tree = VisualHelpers._to_tree_model(
        semantic_ast, include_types=False, semantic=True, symbol_table=symbol_table
    )

    syntax_labels = _collect_tree_labels(syntax_tree)
    semantic_labels = _collect_tree_labels(semantic_tree)

    assert all("num:" not in label for label in syntax_labels)
    assert all("num:" not in label for label in semantic_labels)
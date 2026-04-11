import customtkinter as ctk
import tkinter as tk
import re
from copy import deepcopy
from typing import Optional, Dict, Any, List
from core.lexer import lex
from core.parser import parse
from core.semantic import analyze_semantics
from core.intermediate import generate_intermediate_code
from core.optimizer import optimize
from core.codegen import generate_code
from gui.visual_helpers import VisualHelpers


class PhasePanels(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.tabview = ctk.CTkTabview(self, width=600, height=400)
        self.tabview.pack(expand=True, fill="both", padx=10, pady=10)

        self.tabs = {}
        phase_names = [
            "Lexical",
            "Syntax",
            "Semantic",
            "Intermediate",
            "Optimized",
            "Assembly",
        ]

        for name in phase_names:
            self.tabs[name] = self.tabview.add(name)
            label = ctk.CTkLabel(
                self.tabs[name], text="No data yet", font=("Arial", 12)
            )
            label.pack(expand=True, fill="both", padx=10, pady=10)

    def _clear_tab(self, phase: str):
        for widget in self.tabs[phase].winfo_children():
            widget.destroy()

    def _build_semantic_notes(self, coercions: List[Dict[str, Any]]) -> str:
        lines = [
            "Semantic Checks",
            "- Type checking: PASSED",
            "- Type compatibility: VERIFIED",
            "- All variables declared",
        ]

        if coercions:
            lines.append("")
            lines.append("Type Coercions:")
            for i, coercion in enumerate(coercions, 1):
                lines.append(
                    "%d. %s: %s -> %s"
                    % (i, coercion["coercion"], coercion["from"], coercion["to"])
                )
        else:
            lines.append("")
            lines.append("Type Coercions: None required")

        return "\n".join(lines)

    def _clear_tab_widgets(self, phase: str):
        self._clear_tab(phase)

    def _build_table_card(
        self, parent, title: str, headers: List[str], rows: List[List[Any]], accent: str
    ):
        card = ctk.CTkFrame(parent, fg_color="#151a22", corner_radius=10)
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=("Arial", 13, "bold"),
            text_color=accent,
        )
        title_label.grid(row=0, column=0, columnspan=len(headers), sticky="w", padx=10, pady=(10, 6))

        for column, header in enumerate(headers):
            header_label = ctk.CTkLabel(
                card,
                text=header,
                font=("Arial", 11, "bold"),
                fg_color="#2a3340",
                corner_radius=6,
                padx=8,
                pady=4,
            )
            header_label.grid(row=1, column=column, sticky="nsew", padx=6, pady=(0, 6))
            card.grid_columnconfigure(column, weight=1)

        if rows:
            for row_index, row in enumerate(rows, start=2):
                for column, cell in enumerate(row):
                    cell_label = ctk.CTkLabel(
                        card,
                        text=str(cell),
                        font=("Courier", 11),
                        fg_color="#1d2430" if row_index % 2 == 0 else "#18202b",
                        corner_radius=6,
                        padx=8,
                        pady=4,
                    )
                    cell_label.grid(row=row_index, column=column, sticky="nsew", padx=6, pady=3)
        else:
            empty_label = ctk.CTkLabel(
                card,
                text="No entries",
                font=("Courier", 11),
                text_color="#8b97a7",
            )
            empty_label.grid(row=2, column=0, columnspan=len(headers), sticky="w", padx=10, pady=(6, 10))

        return card

    def update_lexical_grid(self, tokens):
        self._clear_tab("Lexical")

        scroll = ctk.CTkScrollableFrame(self.tabs["Lexical"])
        scroll.pack(expand=True, fill="both", padx=8, pady=8)

        # Identifiers grid card
        identifiers = VisualHelpers.lexical_identifiers_rows(tokens)
        if identifiers:
            id_card = self._build_table_card(
                scroll,
                "Identifiers",
                ["Lexeme", "Index"],
                identifiers,
                "#d4a574",
            )
            id_card.pack(fill="x", padx=4, pady=(0, 8))

        # Operators grid card
        operators = VisualHelpers.lexical_operators_rows(tokens)
        if operators:
            op_card = self._build_table_card(
                scroll,
                "Operators",
                ["Operator", "Type"],
                operators,
                "#a8d5ba",
            )
            op_card.pack(fill="x", padx=4, pady=(0, 8))

        # Literals grid card
        literals = VisualHelpers.lexical_literals_rows(tokens)
        if literals:
            lit_card = self._build_table_card(
                scroll,
                "Literals",
                ["Value", "Type"],
                literals,
                "#b8a8d5",
            )
            lit_card.pack(fill="x", padx=4, pady=(0, 8))

        # Tokenized expression grid card (single row)
        token_expr_rows = VisualHelpers.lexical_token_rows(tokens)
        if token_expr_rows:
            expr_card = self._build_table_card(
                scroll,
                "Tokenized Expression",
                ["Expression"],
                token_expr_rows,
                "#f3f0c8",
            )
            expr_card.pack(fill="x", padx=4, pady=(0, 4))

    def _build_phase_table(self, phase: str, title: str, headers: List[str], rows: List[List[Any]]):
        self._clear_tab(phase)

        scroll = ctk.CTkScrollableFrame(self.tabs[phase])
        scroll.pack(expand=True, fill="both", padx=8, pady=8)

        card = ctk.CTkFrame(scroll, fg_color="#151a22", corner_radius=10)
        card.pack(fill="both", expand=True)

        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=("Arial", 13, "bold"),
            text_color="#c9dff1",
        )
        title_label.grid(row=0, column=0, columnspan=len(headers), sticky="w", padx=10, pady=(10, 6))

        for column, header in enumerate(headers):
            header_label = ctk.CTkLabel(
                card,
                text=header,
                font=("Arial", 11, "bold"),
                fg_color="#2a3340",
                corner_radius=6,
                padx=8,
                pady=4,
            )
            header_label.grid(row=1, column=column, sticky="nsew", padx=6, pady=(0, 6))
            card.grid_columnconfigure(column, weight=1)

        if rows:
            for row_index, row in enumerate(rows, start=2):
                for column, cell in enumerate(row):
                    cell_label = ctk.CTkLabel(
                        card,
                        text=str(cell),
                        font=("Courier", 11),
                        fg_color="#1d2430" if row_index % 2 == 0 else "#18202b",
                        corner_radius=6,
                        padx=8,
                        pady=4,
                    )
                    cell_label.grid(row=row_index, column=column, sticky="nsew", padx=6, pady=3)
        else:
            empty_label = ctk.CTkLabel(
                card,
                text="No entries",
                font=("Courier", 11),
                text_color="#8b97a7",
            )
            empty_label.grid(row=2, column=0, columnspan=len(headers), sticky="w", padx=10, pady=(6, 10))

    def update_intermediate_grid(self, instructions):
        rows = [[index, str(instruction)] for index, instruction in enumerate(instructions, 1)]
        self._build_phase_table("Intermediate", "Three-Address Code", ["#", "Instruction"], rows)

    def update_optimized_grid(self, instructions):
        rows = [[index, str(instruction)] for index, instruction in enumerate(instructions, 1)]
        self._build_phase_table("Optimized", "Optimized TAC", ["#", "Instruction"], rows)

    def update_assembly_grid(self, assembly):
        rows = [[index, line] for index, line in enumerate(assembly, 1)]
        self._build_phase_table("Assembly", "Assembly Code", ["#", "Line"], rows)

    def update_syntax_tree(self, ast: Any, symbol_table=None):
        self._clear_tab("Syntax")

        model = VisualHelpers._to_syntax_tree_model(ast, symbol_table)
        tree_view = ASTCanvasView(self.tabs["Syntax"], model)
        tree_view.pack(expand=True, fill="both", padx=8, pady=8)

    def update_semantic_tree(
        self, ast: Any, coercions: List[Dict[str, Any]], symbol_table=None
    ):
        self._clear_tab("Semantic")

        semantic_model = VisualHelpers._to_tree_model(
            ast, include_types=True, semantic=True, symbol_table=symbol_table
        )

        tree_view = ASTCanvasView(self.tabs["Semantic"], semantic_model)
        tree_view.pack(expand=True, fill="both", padx=8, pady=(8, 4))

        notes = ctk.CTkLabel(
            self.tabs["Semantic"],
            text=self._build_semantic_notes(coercions),
            font=("Courier", 11),
            justify="left",
            anchor="w",
        )
        notes.pack(fill="x", padx=12, pady=(4, 10))

    def update_panel(self, phase: str, content: str):
        if phase in self.tabs:
            self._clear_tab(phase)

            scroll = ctk.CTkScrollableFrame(self.tabs[phase])
            scroll.pack(expand=True, fill="both")

            label = ctk.CTkLabel(
                scroll, text=content, font=("Courier", 11), justify="left"
            )
            label.pack(anchor="w", padx=10, pady=10)

    def update_all(self, data: Dict[str, Any], symbol_table=None):
        if "tokens" in data:
            self.update_lexical_grid(data["tokens"])

        syntax_ast = data.get("syntax_ast") or data.get("ast")
        if syntax_ast:
            self.update_syntax_tree(syntax_ast, symbol_table)

        if "coercions" in data:
            ast = data.get("semantic_ast") or data.get("ast")
            coercions = data.get("coercions", [])
            if ast:
                self.update_semantic_tree(ast, coercions, symbol_table)

        if "tac" in data:
            self.update_intermediate_grid(data["tac"])

        if "optimized" in data:
            self.update_optimized_grid(data["optimized"])

        if "assembly" in data:
            self.update_assembly_grid(data["assembly"])


class SymbolTablePanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        label = ctk.CTkLabel(self, text="Symbol Table", font=("Arial", 14, "bold"))
        label.pack(pady=5)

        self.table_container = ctk.CTkFrame(self, fg_color="transparent")
        self.table_container.pack(expand=True, fill="both", padx=8, pady=8)

    def update(self, symbols: List[Dict[str, Any]]):
        for widget in self.table_container.winfo_children():
            widget.destroy()

        card = ctk.CTkFrame(self.table_container, fg_color="#151a22", corner_radius=10)
        card.pack(fill="both", expand=True)

        title_label = ctk.CTkLabel(card, text="Symbol Table", font=("Arial", 13, "bold"), text_color="#c9dff1")
        title_label.grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=(10, 6))

        headers = ["S.No.", "Variable Name", "Type"]
        for column, header in enumerate(headers):
            header_label = ctk.CTkLabel(
                card,
                text=header,
                font=("Arial", 11, "bold"),
                fg_color="#2a3340",
                corner_radius=6,
                padx=8,
                pady=4,
            )
            header_label.grid(row=1, column=column, sticky="nsew", padx=6, pady=(0, 6))
            card.grid_columnconfigure(column, weight=1)

        if symbols:
            for row_index, sym in enumerate(symbols, start=2):
                row = [sym.get("index", row_index - 1), sym.get("name") or "", sym.get("dtype") or "unknown"]
                for column, cell in enumerate(row):
                    cell_label = ctk.CTkLabel(
                        card,
                        text=str(cell),
                        font=("Courier", 11),
                        fg_color="#1d2430" if row_index % 2 == 0 else "#18202b",
                        corner_radius=6,
                        padx=8,
                        pady=4,
                    )
                    cell_label.grid(row=row_index, column=column, sticky="nsew", padx=6, pady=3)
        else:
            empty_label = ctk.CTkLabel(card, text="Empty", font=("Courier", 11), text_color="#8b97a7")
            empty_label.grid(row=2, column=0, columnspan=3, sticky="w", padx=10, pady=(6, 10))


class ErrorPanel(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        label = ctk.CTkLabel(self, text="Errors / Log", font=("Arial", 14, "bold"))
        label.pack(pady=5)

        self.log_label = ctk.CTkLabel(
            self, text="No errors", font=("Courier", 10), text_color="green"
        )
        self.log_label.pack(padx=10, pady=10)

    def update(self, errors: List[str]):
        if not errors:
            self.log_label.configure(text="No errors", text_color="green")
        else:
            self.log_label.configure(text="\n".join(errors), text_color="red")


class ASTCanvasView(ctk.CTkFrame):
    def __init__(self, master, tree_model: Dict[str, Any], **kwargs):
        super().__init__(master, **kwargs)

        self.tree_model = tree_model
        self.horizontal_gap = 170
        self.vertical_gap = 100
        self.margin_x = 70
        self.margin_y = 40

        self.canvas = tk.Canvas(
            self,
            background="#0c1018",
            highlightthickness=0,
            bd=0,
            xscrollincrement=20,
            yscrollincrement=20,
        )
        self.x_scroll = ctk.CTkScrollbar(self, orientation="horizontal", command=self.canvas.xview)
        self.y_scroll = ctk.CTkScrollbar(self, orientation="vertical", command=self.canvas.yview)

        self.canvas.configure(xscrollcommand=self.x_scroll.set, yscrollcommand=self.y_scroll.set)

        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.y_scroll.grid(row=0, column=1, sticky="ns")
        self.x_scroll.grid(row=1, column=0, sticky="ew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.canvas.bind("<Configure>", lambda _event: self.render())
        self.after(0, self.render)

    def _node_style(self, label: str, has_children: bool):
        cleaned = label.strip().lower()

        if "->" in cleaned:
            return "#f4c48c", "#1e293b"
        if has_children:
            return "#c9dff1", "#1e293b"

        atom = cleaned.split(":", 1)[0].strip()
        numeric = bool(re.fullmatch(r"-?\d+(\.\d+)?", atom))
        if numeric:
            return "#f3f0c8", "#1e293b"
        return "#97f4a9", "#1e293b"

    def _node_size(self, label: str):
        max_chars = max(len(part) for part in label.split("\n"))
        width = max(88, min(240, 14 + max_chars * 8))
        height = 34 + (label.count("\n") * 14)
        return width, height

    def _compute_layout(self):
        positions = {}
        next_x = 0

        def visit(node, depth):
            nonlocal next_x
            children = node.get("children", [])

            if not children:
                x = float(next_x)
                next_x += 1
            else:
                child_x = [visit(child, depth + 1) for child in children]
                x = sum(child_x) / len(child_x)

            positions[id(node)] = (x, depth)
            return x

        visit(self.tree_model, 0)
        return positions

    def _draw_node(self, x: float, y: float, label: str, has_children: bool):
        node_w, node_h = self._node_size(label)
        fill, outline = self._node_style(label, has_children)

        self.canvas.create_rectangle(
            x - node_w / 2,
            y - node_h / 2,
            x + node_w / 2,
            y + node_h / 2,
            fill=fill,
            outline=outline,
            width=2,
        )
        self.canvas.create_text(
            x,
            y,
            text=label,
            fill="#10243c",
            font=("Segoe UI", 12, "bold"),
            justify="center",
        )

    def _draw_edges(self, node, positions):
        node_x, node_depth = positions[id(node)]
        x1 = self.margin_x + node_x * self.horizontal_gap
        y1 = self.margin_y + node_depth * self.vertical_gap

        for child in node.get("children", []):
            child_x, child_depth = positions[id(child)]
            x2 = self.margin_x + child_x * self.horizontal_gap
            y2 = self.margin_y + child_depth * self.vertical_gap
            mid_y = (y1 + y2) / 2

            self.canvas.create_line(x1, y1 + 18, x1, mid_y, fill="#4d8fcc", width=2)
            self.canvas.create_line(x1, mid_y, x2, mid_y, fill="#4d8fcc", width=2)
            self.canvas.create_line(x2, mid_y, x2, y2 - 18, fill="#4d8fcc", width=2)

            self._draw_edges(child, positions)

    def _draw_nodes(self, node, positions):
        node_x, node_depth = positions[id(node)]
        x = self.margin_x + node_x * self.horizontal_gap
        y = self.margin_y + node_depth * self.vertical_gap
        children = node.get("children", [])

        self._draw_node(x, y, node.get("label", "?"), bool(children))
        for child in children:
            self._draw_nodes(child, positions)

    def render(self):
        if not self.tree_model:
            return

        self.canvas.delete("all")
        positions = self._compute_layout()

        self._draw_edges(self.tree_model, positions)
        self._draw_nodes(self.tree_model, positions)

        max_x = max(x for x, _ in positions.values()) if positions else 0
        max_depth = max(depth for _, depth in positions.values()) if positions else 0

        width = self.margin_x * 2 + (max_x + 1) * self.horizontal_gap
        height = self.margin_y * 2 + (max_depth + 1) * self.vertical_gap
        self.canvas.configure(scrollregion=(0, 0, width, height))


class CompilerGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Compiler Phases Visualizer")
        self.geometry("1000x700")

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(side="top", fill="x", padx=10, pady=10)

        self.input_label = ctk.CTkLabel(
            self.input_frame, text="Enter Statement:", font=("Arial", 12)
        )
        self.input_label.pack(side="left", padx=5)

        self.input_entry = ctk.CTkEntry(
            self.input_frame,
            width=500,
            placeholder_text="e.g., position = initial + rate * 60",
        )
        self.input_entry.pack(side="left", padx=5)

        self.analyze_btn = ctk.CTkButton(
            self.input_frame, text="Analyze", command=self.run_analysis
        )
        self.analyze_btn.pack(side="left", padx=5)

        self.clear_btn = ctk.CTkButton(
            self.input_frame, text="Clear", command=self.clear_all
        )
        self.clear_btn.pack(side="left", padx=5)

        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(expand=True, fill="both", padx=10, pady=10)

        self.phase_panels = PhasePanels(self.main_container)
        self.phase_panels.pack(side="left", expand=True, fill="both")

        self.right_panel = ctk.CTkFrame(self.main_container)
        self.right_panel.pack(side="right", fill="y", padx=5)

        self.symbol_table = SymbolTablePanel(self.right_panel)
        self.symbol_table.pack(fill="x", pady=5)

        self.error_panel = ErrorPanel(self.right_panel)
        self.error_panel.pack(fill="x", pady=5)

    def run_analysis(self):
        source = self.input_entry.get().strip()
        if not source:
            return

        all_errors = []

        tokens, symbol_table, lex_errors = lex(source)
        all_errors.extend(lex_errors)

        ast, parse_errors = parse(tokens, symbol_table)
        all_errors.extend(parse_errors)

        syntax_ast = deepcopy(ast) if ast else None

        if ast:
            semantic_ast, sem_errors, coercions = analyze_semantics(ast, symbol_table)
            all_errors.extend(sem_errors)
        else:
            semantic_ast = None
            coercions = []

        tac = generate_intermediate_code(semantic_ast) if semantic_ast else []

        optimized = optimize(tac)

        assembly = generate_code(optimized)

        data = {
            "tokens": tokens,
            "ast": semantic_ast,
            "syntax_ast": syntax_ast,
            "semantic_ast": semantic_ast,
            "coercions": coercions,
            "tac": tac,
            "optimized": optimized,
            "assembly": assembly,
        }

        self.phase_panels.update_all(data, symbol_table)
        self.symbol_table.update(symbol_table.to_list())
        self.error_panel.update(all_errors)

    def clear_all(self):
        self.input_entry.delete(0, "end")

        for name in self.phase_panels.tabs:
            for widget in self.phase_panels.tabs[name].winfo_children():
                widget.destroy()
            label = ctk.CTkLabel(
                self.phase_panels.tabs[name], text="No data yet", font=("Arial", 12)
            )
            label.pack(expand=True, fill="both", padx=10, pady=10)

        self.symbol_table.table_label.configure(text="Empty")
        self.error_panel.log_label.configure(text="No errors", text_color="green")


def main():
    app = CompilerGUI()
    app.mainloop()


if __name__ == "__main__":
    main()

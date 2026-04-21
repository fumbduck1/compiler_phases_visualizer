# Compiler Phases Visualizer

A desktop GUI application that visualizes how source code moves through compiler phases: lexical analysis, syntax parsing, semantic analysis, intermediate TAC generation, optimization, and assembly code output.

## Features

- **Floating-point assembly view** - Visualize floating-point operations in generated assembly.
- **Full compiler pipeline** - Follow code from input to pseudo-assembly output.
- **Phase-specific views** - Token and code views for lexical, TAC, optimized TAC, and assembly; tree canvas for syntax and semantic ASTs.
- **Simple TAC format** - ITAC and OTAC are displayed as clean numbered lines without datatype suffix clutter.
- **Clear tree literals** - Numeric literals are shown as plain values in both syntax and semantic trees.
- **Type coercion visibility** - See implicit conversions like `inttofloat()`.
- **Symbol table and errors** - Live panels for symbols and diagnostics.

## Tech Stack

- Python 3
- CustomTkinter for UI
- Modular compiler phases in `core/`

## Installation

```bash
pip install -r requirements.txt
python main.py
```

## Project Structure

```
compiler_phases_visualizer/
├── core/               # Compiler phases
│   ├── lexer.py        # Tokenization
│   ├── parser.py       # AST generation
│   ├── semantic.py     # Type checking & coercion
│   ├── intermediate.py # TAC generation
│   ├── optimizer.py    # TAC optimization
│   ├── codegen.py      # Assembly code generation
│   └── symbol_table.py
├── gui/                # GUI components
│   ├── main_window.py
│   └── visual_helpers.py
├── utils/              # Utilities
├── tests/              # Test suite and screenshots
├── main.py             # Entry point
└── requirements.txt
```

## Example

Input expression:

`position = initial + rate * 60;`

More examples:

- `result = a + 4 * (c - d) - ((a + c) - b) * d;`
- `for(int i=0; i<=100; i++) { x = x + i; }`

| Phase | Screenshot |
|-------|------------|
| Lexical Analysis | ![Lexical](tests/images/lex.png) |
| Syntax Analysis | ![Syntax](tests/images/syntax.png) |
| Semantic Analysis | ![Semantic](tests/images/semantics.png) |
| Intermediate TAC | ![TAC](tests/images/itac.png) |
| Optimized TAC | ![Optimized](tests/images/otac.png) |
| Assembly | ![Assembly](tests/images/assembly.png) |

## Usage

1. Enter code in the input box.
2. Click **Analyze**.
3. Explore each phase tab:
	- `Lexical`: token groups and tokenized expression
	- `Syntax` and `Semantic`: AST views
	- `Intermediate` and `Optimized`: numbered TAC output
	- `Assembly`: generated pseudo-assembly

Use **Clear** to reset input and panel outputs.
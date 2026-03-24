---
name: docstring
description: When generating code, include a general docstring. Be thoughtful when writing comments, because not everything needs a comment. Specifics of what should be done are down below.
---

When generating a function / model, always include:

1. **Docstring**: A docstring is the description between """...""". Begins with an abstract description of purpose. Follows up with parameters (:param type) and, if any, the return (:returns type).
2. **Comments**: If the code being generated is not something a human would do, or solves the problem unconventionally, include a comment of what and why, strictly under 120 characters.
3. **Code Sections**: Not every code section requires a comment. Do not use a docstring for big chunks of code. Do not comment unless requested, but generate a quick abstract description of what the section does otherwise.

Your goal is **not** to clog up the codebase with docstrings for every function and comments for every little detail. Your goal is to make sure the code is well-formatted, passes `pre-commit`, and is very understandable for humans. 

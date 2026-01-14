Explain the code at the specified location.

## Arguments

`$ARGUMENTS`

## Usage
- `/explain` - Explain the current file or selection
- `/explain path/to/file.py` - Explain a specific file
- `/explain path/to/file.py:functionName` - Explain a specific function
- `/explain path/to/file.py:123` - Explain code around line 123
- `/explain path/to/file.py:100-150` - Explain lines 100-150

## What to Explain

1. **High-level purpose**: What does this code do? Why does it exist?

2. **Key components**:
   - Main functions/classes and their roles
   - Important data structures
   - Core algorithms or patterns used

3. **Control flow**: How does execution flow through this code?

4. **Dependencies**: What does this code depend on? What depends on it?

5. **Non-obvious details**:
   - Tricky logic that needs explanation
   - Performance considerations
   - Edge cases handled
   - Why certain approaches were chosen

## Output Format

### Overview
[1-2 sentence summary of what this code does]

### Purpose
[Why this code exists, what problem it solves]

### How It Works
[Step-by-step explanation of the logic]

### Key Details
[Important things to know: edge cases, assumptions, gotchas]

### Dependencies
[What this code uses, what uses this code]

### Example Usage (if applicable)
[How to use this code]

Keep explanations clear and concise. Focus on the "why" not just the "what".
Use code snippets to illustrate points when helpful.
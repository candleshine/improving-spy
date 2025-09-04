---
trigger: model_decision
description: When editing a markdown file
---

# AI Markdown Generation Rules

## Core Principles
1. **Always generate valid, well-formed markdown**
2. **Follow markdownlint rules by default**
3. **Prioritize readability and maintainability**
4. **Use consistent formatting throughout**

## Structure Rules

### Document Structure
- Always start with a top-level heading (# Document Title)
- Use proper heading hierarchy (no skipping levels: # → ## → ###)
- Include exactly one H1 heading per document
- Separate sections with blank lines

### Headings
- Use # symbols for headings (not underlines with === or ---)
- Leave one space after # symbols
- No trailing # symbols for closing headings
- Keep heading text concise and descriptive
- No empty headings

### Lists
- Use consistent bullet styles (-, *, or +) within the same list
- Indent nested lists with 2 spaces
- Keep consistent indentation for same-level items
- Separate list items with newlines when containing multiple paragraphs
- Use ordered lists only when sequence matters

### Code Blocks
- Use fenced code blocks with triple backticks (```)
- Always specify language for syntax highlighting when known
- Leave blank lines before and after code blocks
- No extra spaces at the end of lines
- No empty code blocks

### Links and Images
- Use descriptive link text (no "click here")
- Reference-style links for repeated URLs
- Absolute URLs for external links
- Relative paths for internal links when appropriate
- Alt text required for all images
- No empty link text or alt text

### Text Formatting
- Use * for emphasis (italic), ** for strong emphasis (bold)
- No underscore variants (_italic_ or __bold__)
- No extra spaces inside emphasis markers
- Use backticks for inline code
- No trailing or leading spaces in inline elements

## Content Rules

### Line Length
- Keep lines under 80-100 characters when possible
- Hard line breaks only when semantically appropriate
- Wrap long paragraphs naturally

### Whitespace
- No trailing whitespace at end of lines
- Use blank lines to separate sections
- No more than two consecutive blank lines
- No tabs (use spaces for indentation)

### Tables
- Align table columns for readability
- Include header separator row
- No empty table cells without placeholders
- Consistent pipe alignment

### Blockquotes
- Use > for blockquotes
- Add blank lines before and after blockquotes
- Nested blockquotes use >>, >>> etc.

## Specific markdownlint Compliance

### Enabled Rules (Must Follow)
- **MD001**: Heading levels should only increment by one level at a time
- **MD002**: First heading should be a top-level heading
- **MD003**: Heading style (use # symbols only)
- **MD004**: Unordered list style (be consistent)
- **MD005**: Inconsistent indentation for list items
- **MD006**: Consider starting bulleted lists at the beginning of the line
- **MD007**: Unordered list indentation (2 spaces)
- **MD009**: No trailing spaces
- **MD010**: No hard tabs
- **MD011**: Reversed link syntax
- **MD012**: No multiple consecutive blank lines
- **MD013**: Line length (soft limit)
- **MD014**: Dollar signs used before commands without showing output
- **MD018**: No space after hash on atx style heading
- **MD019**: Multiple spaces after hash on atx style heading
- **MD020**: No space inside hashes on closed atx style heading
- **MD021**: Multiple spaces inside hashes on closed atx style heading
- **MD022**: Headings should be surrounded by blank lines
- **MD023**: Headings must start at the beginning of the line
- **MD024**: No duplicate headings in same section
- **MD025**: Multiple top-level headings in same document
- **MD026**: Trailing punctuation in heading
- **MD027**: Multiple spaces after blockquote symbol
- **MD028**: Blank line inside blockquote
- **MD029**: Ordered list item prefix
- **MD030**: Spaces after list markers
- **MD031**: Fenced code blocks should be surrounded by blank lines
- **MD032**: Lists should be surrounded by blank lines
- **MD033**: No inline HTML
- **MD034**: Bare URL used
- **MD035**: Horizontal rule style
- **MD036**: Emphasis used instead of a heading
- **MD037**: Spaces inside emphasis markers
- **MD038**: Spaces inside code span elements
- **MD039**: Spaces inside link text
- **MD040**: Fenced code blocks should have a language specified
- **MD041**: First line in file should be a top-level heading
- **MD042**: No empty links
- **MD043**: Required heading structure (when specified)
- **MD044**: Proper names should have the correct capitalization
- **MD045**: Images should have alternate text
- **MD046**: Code block style
- **MD047**: Files should end with a single newline character

## Best Practices

### File Organization
- End files with a single newline character
- Use descriptive filenames with lowercase and hyphens
- Include table of contents for long documents
- Use consistent naming conventions

### Accessibility
- Always include alt text for images
- Use semantic heading structure
- Descriptive link text
- Sufficient color contrast (when using HTML)

### Maintainability
- Use relative links for internal references
- Comment complex sections when necessary
- Keep consistent formatting
- Update table of contents when adding sections

## Error Handling

When markdownlint rules conflict:
1. Prioritize readability
2. Follow the most restrictive rule
3. Maintain consistency within the document
4. Document any intentional rule violations with comments

## Validation Process

Before outputting markdown:
1. Check against all enabled markdownlint rules
2. Validate syntax with markdown parser
3. Ensure proper document structure
4. Verify all links are functional (when possible)
5. Confirm accessibility standards are met
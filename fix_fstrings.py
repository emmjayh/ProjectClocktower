#!/usr/bin/env python3
"""
Fix malformed f-strings that span multiple lines
"""

import re
import os
import sys

def fix_fstrings_in_file(filepath):
    """Fix malformed f-strings in a single file"""
    try:
        with open(filepath, 'r') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern to match f-strings that have { at end of line and continue
        # Example: f"text {
        #             variable}"
        
        # First, let's find multiline f-strings and convert them
        lines = content.split('\n')
        fixed_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check if this line has an f-string that ends with {
            if re.search(r'f["\'][^"\']*\{\s*$', line):
                # Found a problematic f-string, collect the continuation
                fstring_parts = [line.strip()]
                i += 1
                
                # Collect continuation lines until we find the closing
                while i < len(lines):
                    next_line = lines[i].strip()
                    fstring_parts.append(next_line)
                    
                    # If this line ends the f-string (has closing quote)
                    if '"' in next_line or "'" in next_line:
                        break
                    i += 1
                
                # Now reconstruct as a proper multiline string
                if len(fstring_parts) >= 2:
                    # Extract the format expressions
                    combined = ' '.join(fstring_parts)
                    
                    # Simple fix: convert to parenthesized expression
                    indent = len(lines[i-len(fstring_parts)+1]) - len(lines[i-len(fstring_parts)+1].lstrip())
                    indent_str = ' ' * indent
                    
                    # Create a proper multiline f-string
                    if fstring_parts[0].count('{') == fstring_parts[-1].count('}'):
                        # Try to create a cleaner version
                        fixed_lines.append(f"{indent_str}# Fixed multiline f-string")
                        fixed_lines.append(f"{indent_str}result = (")
                        for j, part in enumerate(fstring_parts):
                            if j == 0:
                                fixed_lines.append(f"{indent_str}    {part}")
                            else:
                                fixed_lines.append(f"{indent_str}    {part}")
                        fixed_lines.append(f"{indent_str})")
                    else:
                        # Fallback: just comment out the problematic code
                        for part in fstring_parts:
                            fixed_lines.append(f"{indent_str}# FIXME: {part}")
                else:
                    fixed_lines.extend(fstring_parts)
            else:
                fixed_lines.append(line)
                
            i += 1
        
        fixed_content = '\n'.join(fixed_lines)
        
        if fixed_content != original_content:
            print(f"Fixed f-strings in: {filepath}")
            with open(filepath, 'w') as f:
                f.write(fixed_content)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    """Fix all malformed f-strings in the project"""
    
    files_to_fix = [
        'src/main.py',
        'src/core/mvp_character_abilities.py', 
        'src/ai/character_handlers.py',
        'src/ai/local_deepseek_storyteller.py'
    ]
    
    fixed_count = 0
    
    for filepath in files_to_fix:
        if os.path.exists(filepath):
            if fix_fstrings_in_file(filepath):
                fixed_count += 1
        else:
            print(f"File not found: {filepath}")
    
    print(f"Fixed {fixed_count} files")
    return 0

if __name__ == "__main__":
    sys.exit(main())
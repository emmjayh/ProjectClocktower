#!/usr/bin/env python3
"""
Fix all broken multiline f-strings in the codebase
"""

import re
import os

def fix_broken_fstrings(content):
    """Fix broken f-strings that span multiple lines"""
    
    # Pattern to match f-strings that end with { and continue on next line
    # Example: f"text {
    #             variable}"
    
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this line has an f-string that ends with {
        if re.search(r'f"[^"]*\{\s*$', line):
            # Found a broken f-string, collect all parts
            original_indent = len(line) - len(line.lstrip())
            indent = ' ' * original_indent
            
            # Extract the beginning part
            match = re.search(r'(.*)f"([^"]*)\{\s*$', line)
            if match:
                prefix = match.group(1)
                fstring_start = match.group(2)
                
                # Collect continuation lines
                continuation_parts = []
                i += 1
                
                while i < len(lines):
                    next_line = lines[i].strip()
                    
                    # If this line ends the f-string (has closing quote and })
                    if next_line.endswith('}"') or next_line.endswith('}'):
                        # This is the end
                        if next_line.endswith('}"'):
                            # Remove the }" and add the content
                            continuation_parts.append(next_line[:-2])
                        else:
                            continuation_parts.append(next_line[:-1])
                        break
                    elif '"' in next_line and '}' in next_line:
                        # Complex ending
                        # Find where the f-string ends
                        if '}"' in next_line:
                            parts = next_line.split('}"')
                            continuation_parts.append(parts[0])
                            # Add any remaining content after the f-string
                            if len(parts) > 1 and parts[1]:
                                remaining = '}"'.join(parts[1:])
                                continuation_parts.append(f'REMAINING: {remaining}')
                        break
                    else:
                        continuation_parts.append(next_line)
                        i += 1
                
                # Now reconstruct as a proper f-string
                if continuation_parts:
                    # Join all parts
                    full_content = fstring_start + ''.join(continuation_parts)
                    
                    # Create a clean f-string
                    fixed_line = f'{prefix}f"{full_content}"'
                    
                    # If it's too long, split it properly
                    if len(fixed_line) > 120:
                        # Split into multiple f-strings
                        words = full_content.split()
                        chunks = []
                        current_chunk = ""
                        
                        for word in words:
                            if len(current_chunk + word) < 80:
                                current_chunk += word + " "
                            else:
                                if current_chunk:
                                    chunks.append(current_chunk.strip())
                                current_chunk = word + " "
                        
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        
                        # Create multiline f-string
                        if len(chunks) > 1:
                            fixed_lines.append(f'{prefix}(')
                            for j, chunk in enumerate(chunks):
                                if j == 0:
                                    fixed_lines.append(f'{indent}    f"{chunk} "')
                                elif j == len(chunks) - 1:
                                    fixed_lines.append(f'{indent}    f"{chunk}"')
                                else:
                                    fixed_lines.append(f'{indent}    f"{chunk} "')
                            fixed_lines.append(f'{indent})')
                        else:
                            fixed_lines.append(fixed_line)
                    else:
                        fixed_lines.append(fixed_line)
                else:
                    # Fallback: keep original line but commented
                    fixed_lines.append(f'# BROKEN: {line}')
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
        
        i += 1
    
    return '\n'.join(fixed_lines)

def main():
    """Fix all f-strings in the project"""
    
    files_to_fix = [
        'src/main.py',
        'src/core/timing_config.py',
        'src/speech/speech_handler.py',
        'src/speech/enhanced_storyteller_tts.py',
        'src/gui/storyteller_dashboard.py',
        'src/game/rule_engine.py',
        'src/game/simple_botc_test.py',
        'src/game/live_game_monitor.py',
        'src/game/character_abilities.py',
        'src/game/game_persistence.py',
        'src/ai/storyteller_ai.py',
        'src/ai/local_deepseek_storyteller.py',
        'src/ai/mock_deepseek.py',
        'src/ai/narrator_integration.py'
    ]
    
    for filepath in files_to_fix:
        if os.path.exists(filepath):
            print(f"Fixing {filepath}...")
            
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                
                fixed_content = fix_broken_fstrings(content)
                
                if fixed_content != content:
                    with open(filepath, 'w') as f:
                        f.write(fixed_content)
                    print(f"  ✅ Fixed {filepath}")
                else:
                    print(f"  ℹ️  No changes needed in {filepath}")
                    
            except Exception as e:
                print(f"  ❌ Error fixing {filepath}: {e}")
        else:
            print(f"  ⚠️  File not found: {filepath}")

if __name__ == "__main__":
    main()
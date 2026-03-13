import os
import re
import tokenize
import io
import ast

def remove_emojis(text):
    return re.sub(r'[^\x00-\x7F\u00A0-\u024F\u1E00-\u1EFF]', '', text)

def minify_python(content):
    try:
        result = []
        tokens = tokenize.generate_tokens(io.StringIO(content).readline)
        last_lineno = -1
        last_col = 0


        docstring_ranges = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                    doc = ast.get_docstring(node, clean=False)
                    if doc:
                        pass
        except:
            pass

        new_lines = []
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith('#'):
                continue

            new_line = ""
            in_string = None
            i = 0
            while i < len(line):
                char = line[i]
                if in_string:
                    if char == in_string:
                        if i > 0 and line[i-1] == '\\':
                            pass
                        else:
                            in_string = None
                    new_line += char
                else:
                    if char in ('"', "'", '`'):
                        in_string = char
                        new_line += char
                    elif char == '#':
                        break
                    else:
                        new_line += char
                i += 1
            new_lines.append(new_line.rstrip())

        return "\n".join(new_lines)
    except:
        return content

def minify_js_ts(content):
    new_content = ""
    in_string = None
    in_multiline_comment = False
    i = 0
    while i < len(content):
        if in_multiline_comment:
            if content[i:i+2] == '*/':
                in_multiline_comment = False
                i += 2
                continue
            i += 1
            continue

        if in_string:
            if content[i] == in_string:
                if i > 0 and content[i-1] == '\\':
                    pass
                else:
                    in_string = None
            new_content += content[i]
            i += 1
            continue

        if content[i:i+2] == '/*':
            in_multiline_comment = True
            i += 2
        elif content[i:i+2] == '//':
            while i < len(content) and content[i] != '\n':
                i += 1
        elif content[i] in ('"', "'", '`'):
            in_string = content[i]
            new_content += content[i]
            i += 1
        else:
            new_content += content[i]
            i += 1
    return new_content

def process_file(filepath):
    _, ext = os.path.splitext(filepath)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    content = remove_emojis(content)

    if ext == '.py':
        content = minify_python(content)
    elif ext in ('.js', '.ts'):
        content = minify_js_ts(content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

def main():
    targets = ['app', 'tests', 'scripts']
    for target in targets:
        for root, dirs, files in os.walk(target):
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.sh')):
                    process_file(os.path.join(root, file))

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
Convert all Markdown files in the docs directory to HTML.
Creates HTML files with the same basename as the source .md files.
Embeds images as base64 data URIs for self-contained HTML files.

Requires: markdown library
Install with: pip install markdown
"""

import os
import sys
from pathlib import Path
import markdown
import base64
import mimetypes
import re


def embed_images_as_base64(html_content, base_dir):
    """
    Find all image references in HTML and replace with base64 data URIs.

    Args:
        html_content: HTML string with image tags
        base_dir: Directory containing the HTML file (for resolving relative paths)

    Returns:
        HTML string with embedded base64 images
    """
    # Find all <img> tags with src attribute
    img_pattern = r'<img\s+([^>]*?)src=["\']([^"\']+)["\']([^>]*?)>'

    def replace_image(match):
        before_src = match.group(1)
        img_path = match.group(2)
        after_src = match.group(3)

        # Skip if already a data URI
        if img_path.startswith('data:'):
            return match.group(0)

        # Skip absolute URLs
        if img_path.startswith(('http://', 'https://')):
            return match.group(0)

        # Resolve relative path
        full_img_path = base_dir / img_path

        if not full_img_path.exists():
            print(f"    ⚠️  Warning: Image not found: {img_path}")
            return match.group(0)

        try:
            # Read image file
            with open(full_img_path, 'rb') as img_file:
                img_data = img_file.read()

            # Encode to base64
            img_base64 = base64.b64encode(img_data).decode('utf-8')

            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(full_img_path)
            if not mime_type:
                mime_type = 'image/png'  # Default fallback

            # Create data URI
            data_uri = f"data:{mime_type};base64,{img_base64}"

            print(f"    ✓ Embedded image: {img_path} ({len(img_data)} bytes)")

            # Return modified img tag
            return f'<img {before_src}src="{data_uri}"{after_src}>'

        except Exception as e:
            print(f"    ⚠️  Error embedding {img_path}: {e}")
            return match.group(0)

    return re.sub(img_pattern, replace_image, html_content)


def convert_md_to_html(md_file_path):
    """
    Convert a single Markdown file to HTML.

    Args:
        md_file_path: Path object pointing to the .md file

    Returns:
        Path object pointing to the created .html file
    """
    # Read the Markdown content
    with open(md_file_path, 'r', encoding='utf-8') as f:
        md_content = f.read()

    # Convert to HTML with extensions for better formatting
    html_content = markdown.markdown(
        md_content,
        extensions=['tables', 'fenced_code', 'codehilite', 'toc']
    )

    # Embed images as base64 data URIs
    base_dir = md_file_path.parent
    html_content = embed_images_as_base64(html_content, base_dir)

    # Create a complete HTML document with styling
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{md_file_path.stem}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
            background-color: #f5f5f5;
        }}
        .content {{
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1, h2, h3, h4, h5, h6 {{
            color: #2c3e50;
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }}
        h1 {{
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 8px;
        }}
        code {{
            background-color: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 0.9em;
        }}
        pre {{
            background-color: #2d2d2d;
            color: #f8f8f2;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        pre code {{
            background-color: transparent;
            padding: 0;
            color: #f8f8f2;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        blockquote {{
            border-left: 4px solid #3498db;
            margin: 20px 0;
            padding: 10px 20px;
            background-color: #f0f7fb;
        }}
        a {{
            color: #3498db;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        ul, ol {{
            margin: 10px 0;
            padding-left: 30px;
        }}
        li {{
            margin: 5px 0;
        }}
        hr {{
            border: none;
            border-top: 2px solid #e0e0e0;
            margin: 30px 0;
        }}
        img {{
            max-width: 100%;
            height: auto;
            display: block;
            margin: 20px auto;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-radius: 4px;
        }}
    </style>
    <script type="module">
        import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
        mermaid.initialize({{ startOnLoad: true }});
    </script>
</head>
<body>
    <div class="content">
{html_content}
    </div>
</body>
</html>
"""

    # Create output HTML file path
    html_file_path = md_file_path.with_suffix('.html')

    # Write the HTML content
    with open(html_file_path, 'w', encoding='utf-8') as f:
        f.write(full_html)

    return html_file_path


def main():
    """
    Find all .md files in the docs directory and convert them to HTML.
    """
    # Get the docs directory (where this script is located)
    docs_dir = Path(__file__).parent

    # Find all .md files
    md_files = list(docs_dir.glob('*.md'))

    if not md_files:
        print("No Markdown files found in the docs directory.")
        return

    print(f"Found {len(md_files)} Markdown file(s) to convert:")

    # Convert each file
    converted_files = []
    for md_file in md_files:
        print(f"  Converting: {md_file.name}...", end=" ")
        try:
            html_file = convert_md_to_html(md_file)
            converted_files.append(html_file)
            print(f"✓ Created: {html_file.name}")
        except Exception as e:
            print(f"✗ Error: {e}")

    print(f"\nSuccessfully converted {len(converted_files)} file(s)!")


if __name__ == '__main__':
    main()

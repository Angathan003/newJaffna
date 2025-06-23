#!/usr/bin/env python3
"""
article.py

Command-line script to:
  1. Extract articles (headings, paragraphs, images) from all PDFs in "data/".
  2. Export Markdown and images under "html_output/<slug>/articles".
  3. Copy assets into "html_output/assets".
  4. Render Markdown to HTML pages and an index.html.

Usage:
  python article.py
"""

import fitz
import os
import re
import csv
import shutil
import urllib.parse
import zipfile
import markdown
from pathlib import Path

# --- Helper Functions ---

def slugify(s: str, maxlen: int = 50) -> str:
    s = s.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "_", s)
    return s.strip("_")[:maxlen] or "article"


def find_heading(blocks, page_height,
                 size_thresh: float = 18,
                 y_margin_frac: float = 0.15,
                 min_chars: int = 10) -> str:
    y_limit = page_height * y_margin_frac
    for blk in blocks:
        if blk.get("type") != 0:
            continue
        _, y0, _, _ = blk.get("bbox", [0,0,0,0])
        if y0 > y_limit:
            continue
        spans = [span for line in blk.get("lines", []) for span in line.get("spans", [])]
        if not spans or max(span.get("size", 0) for span in spans) < size_thresh:
            continue
        text = " ".join(span.get("text","").strip() for span in spans)
        text = re.sub(r"\s+", ' ', text).strip()
        if len(text) >= min_chars:
            return text
    return None

from pathlib import Path
import fitz
import shutil
import csv
import re
import urllib.parse

def extract_to_markdown(pdf_path: Path, out_dir: Path) -> None:
    """
    Extracts articles by heading from a PDF, and writes:
      - output.csv
      - images under out_dir/images_out/
      - Markdown files under out_dir/articles/
    """
    # Open PDF
    doc = fitz.open(str(pdf_path))
    articles = []
    current = { 'id': 1, 'title': None, 'start_page': None, 'end_page': None, 'paragraphs': [] }

    img_root = out_dir / "images_out"
    md_root  = out_dir / "articles"
    csv_path = out_dir / "output.csv"

    # Clean and recreate output dirs
    if out_dir.exists():
        shutil.rmtree(out_dir)
    img_root.mkdir(parents=True)
    md_root.mkdir(parents=True)

    def slugify(s: str, maxlen: int = 50) -> str:
        s = s.lower()
        s = re.sub(r"[^\w\s-]", "", s)
        s = re.sub(r"[\s_-]+", "_", s)
        return s.strip("_")[:maxlen] or "article"

    def find_heading(blocks, page_height,
                     size_thresh: float = 18,
                     y_margin_frac: float = 0.15,
                     min_chars: int = 10) -> str:
        y_limit = page_height * y_margin_frac
        for blk in blocks:
            if blk.get("type") != 0:
                continue
            _, y0, _, _ = blk.get("bbox", [0,0,0,0])
            if y0 > y_limit:
                continue
            spans = [span for line in blk.get("lines", []) for span in line.get("spans", [])]
            if not spans or max(span.get("size",0) for span in spans) < size_thresh:
                continue
            text = " ".join(span.get("text","").strip() for span in spans)
            text = re.sub(r"\s+", " ", text).strip()
            if len(text) >= min_chars:
                return text
        return None

    # Walk pages
    for pageno, page in enumerate(doc, start=1):
        blocks  = page.get_text("dict").get("blocks", [])
        heading = find_heading(blocks, page.rect.height)
        if heading:
            if current['title']:
                current['end_page'] = pageno - 1
                articles.append(current)
                current = { 'id': current['id']+1, 'title': None, 'start_page': None, 'end_page': None, 'paragraphs': [] }
            current['title']      = heading
            current['start_page'] = pageno

        if not current['title']:
            current['title']      = f"article_{current['id']}"
            current['start_page'] = 1

        # Extract paragraphs
        page_text = page.get_text().strip()
        paras = [p for p in page_text.split("\n\n") if p.strip()]
        for p in paras:
            current['paragraphs'].append({'text': p, 'images': []})

        # Extract images, handling CMYK → RGB conversion if needed
        for idx, imginfo in enumerate(page.get_images(full=True), start=1):
            xref = imginfo[0]
            pix = fitz.Pixmap(doc, xref)
            
            # Handle different color formats
            try:
                if pix.n > 4:  # CMYK or other multi-channel formats
                    if pix.colorspace and pix.colorspace.n > 1:
                        pix0 = fitz.Pixmap(fitz.csRGB, pix)
                        pix = pix0
                elif pix.n == 1:  # Grayscale
                    # Convert grayscale to RGB for JPEG compatibility
                    if pix.colorspace:
                        pix0 = fitz.Pixmap(fitz.csRGB, pix)
                        pix = pix0
                elif pix.n == 2:  # Grayscale with alpha
                    # Convert to RGB with alpha
                    if pix.colorspace:
                        pix0 = fitz.Pixmap(fitz.csRGB, pix)
                        pix = pix0
            except Exception as e:
                print(f"Warning: Color conversion failed for image {idx}: {e}")
                # Continue with original pixmap
            
            # determine extension by alpha channel
            ext = 'png' if pix.alpha else 'jpg'
            folder = img_root / f"{current['id']:03d}_{slugify(current['title'])}"
            folder.mkdir(parents=True, exist_ok=True)
            img_path = folder / f"p{pageno:03d}_i{idx}.{ext}"
            
            try:
                pix.save(str(img_path))
            except Exception as e:
                # If saving fails, try converting to PNG instead
                print(f"Warning: Failed to save {img_path} as {ext}: {e}")
                img_path = img_path.with_suffix('.png')
                try:
                    pix.save(str(img_path))
                except Exception as e2:
                    print(f"Error: Failed to save image {img_path}: {e2}")
                    continue
            
            pix = None
            current['paragraphs'][-1]['images'].append(str(img_path))

    # Finalize last article
    if current['title']:
        current['end_page'] = doc.page_count
        articles.append(current)

    # Write summary CSV
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['id','title','start_page','end_page','image_count'])
        for art in articles:
            count = sum(len(p['images']) for p in art['paragraphs'])
            writer.writerow([art['id'], art['title'], art['start_page'], art['end_page'], count])

    # Write Markdown files
    for art in articles:
        fname   = f"{art['id']:03d}_{slugify(art['title'])}.md"
        md_file = md_root / fname
        with open(md_file, 'w', encoding='utf-8') as md:
            md.write(f"# {art['title']}\n\n")
            for para in art['paragraphs']:
                md.write(para['text'] + "\n\n")
                for img in para['images']:
                    # link from articles/ back to images_out/
                    rel = Path(img).relative_to(out_dir).as_posix()
                    url = urllib.parse.quote(rel)
                    md.write(f"![{Path(img).name}]({url})\n\n")


# --- HTML Generation ---


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="preconnect" href="https://fonts.gstatic.com/" crossorigin="" />
    <link
      rel="stylesheet"
      href="https://fonts.googleapis.com/css2?display=swap&amp;family=Newsreader%3Awght%40400%3B500%3B700%3B800&amp;family=Noto+Sans%3Awght%40400%3B500%3B700%3B900"
    />

    <title>{title}</title>
    <link rel="icon" type="image/x-icon" href="data:image/x-icon;base64," />

    <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
    <link rel="stylesheet" href="../assets/styles.css">
    <style>
        .prose img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            margin: 2rem 0;
        }}
        .prose h1, .prose h2, .prose h3 {{
            color: #1c170d;
            margin-top: 2rem;
            margin-bottom: 1rem;
        }}
        .prose p {{
            margin-bottom: 1.5rem;
            line-height: 1.7;
        }}
    </style>
  </head>
  <body class="bg-[#fcfbf8] font-['Newsreader','Noto_Sans',sans-serif]">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b border-[#f3f0e7] sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center py-4">
                <div class="flex items-center space-x-4">
                    <a href="../index.html" class="flex items-center space-x-4 hover:opacity-80 transition-opacity">
                        <div class="w-12 h-12 bg-[#9b844b] rounded-full flex items-center justify-center">
                            <span class="text-white font-bold text-xl">JM</span>
                        </div>
                        <div>
                            <h1 class="text-2xl font-bold text-[#1c170d]">Jaffna Monitor</h1>
                            <p class="text-sm text-[#9b844b]">News & Publications</p>
                        </div>
                    </a>
                </div>
                <nav class="hidden md:flex space-x-8">
                    <a href="../index.html" class="text-[#1c170d] hover:text-[#9b844b] transition-colors">Home</a>
                    <a href="#" class="text-[#1c170d] hover:text-[#9b844b] transition-colors">News</a>
                    <a href="#" class="text-[#1c170d] hover:text-[#9b844b] transition-colors">About</a>
                    <a href="#" class="text-[#1c170d] hover:text-[#9b844b] transition-colors">Contact</a>
                </nav>
            </div>
        </div>
    </header>

    <!-- Breadcrumb -->
    <div class="bg-white border-b border-[#f3f0e7]">
        <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
            <nav class="flex" aria-label="Breadcrumb">
                <ol class="flex items-center space-x-2">
                    <li>
                        <a href="../index.html" class="text-[#9b844b] hover:text-[#1c170d] transition-colors text-sm">
                            Home
                        </a>
                    </li>
                    <li>
                        <svg class="w-4 h-4 text-gray-400" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd"></path>
                        </svg>
                    </li>
                    <li>
                        <span class="text-gray-500 text-sm">{title}</span>
                    </li>
                </ol>
            </nav>
        </div>
    </div>

    <!-- Main Content -->
    <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <article class="bg-white rounded-lg shadow-lg overflow-hidden">
            <!-- Article Header -->
            <div class="p-8 border-b border-[#f3f0e7]">
                <h1 class="text-3xl md:text-4xl font-bold text-[#1c170d] mb-4 leading-tight">{title}</h1>
                <div class="flex items-center text-[#9b844b] text-sm mb-4">
                    <span>By {author}</span>
                    <span class="mx-2">•</span>
                    <span>Published {date}</span>
                </div>
                <div class="flex items-center space-x-4">
                    <div class="flex items-center space-x-2">
                        <svg class="w-4 h-4 text-[#9b844b]" fill="currentColor" viewBox="0 0 20 20">
                            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clip-rule="evenodd"></path>
                        </svg>
                        <span class="text-sm text-[#9b844b]">5 min read</span>
                    </div>
                </div>
            </div>

            <!-- Article Content -->
            <div class="p-8">
                <div class="prose prose-lg max-w-none">
                    {content}
                </div>
            </div>

            <!-- Article Footer -->
            <div class="p-8 border-t border-[#f3f0e7] bg-gray-50">
                <div class="flex flex-wrap items-center justify-between">
                    <div class="mb-4 md:mb-0">
                        <h4 class="text-sm font-semibold text-[#1c170d] mb-2">Tags:</h4>
                        <div class="flex flex-wrap gap-2">
                            {tag_elements}
                        </div>
                    </div>
                    <div class="flex space-x-4">
                        <a href="../index.html" 
                           class="inline-flex items-center px-4 py-2 bg-[#9b844b] text-white rounded-lg hover:bg-[#1c170d] transition-colors text-sm font-medium">
                            <svg class="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"></path>
                            </svg>
                            Back to Home
                        </a>
                    </div>
                </div>
            </div>
        </article>
    </main>

    <!-- Footer -->
    <footer class="bg-[#1c170d] text-white py-12 mt-16">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div>
                    <h3 class="text-xl font-bold mb-4">Jaffna Monitor</h3>
                    <p class="text-gray-300">
                        Dedicated to bringing you the latest news and insights from Jaffna and beyond.
                    </p>
                </div>
                <div>
                    <h4 class="text-lg font-semibold mb-4">Contact</h4>
                    <p class="text-gray-300">hellojaffnamonitor@gmail.com</p>
                    <p class="text-gray-300">Jaffna, Sri Lanka</p>
                </div>
                <div>
                    <h4 class="text-lg font-semibold mb-4">Follow Us</h4>
                    <div class="flex space-x-4">
                        <a href="#" class="text-gray-300 hover:text-white transition-colors">
                            <span class="sr-only">Facebook</span>
                            <svg class="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                            </svg>
                        </a>
                        <a href="#" class="text-gray-300 hover:text-white transition-colors">
                            <span class="sr-only">Twitter</span>
                            <svg class="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/>
                            </svg>
                        </a>
                    </div>
                </div>
            </div>
            <div class="border-t border-gray-700 mt-8 pt-8 text-center">
                <p class="text-gray-300">&copy; 2024 Jaffna Monitor. All rights reserved.</p>
            </div>
        </div>
    </footer>
  </body>
</html>
"""

INDEX_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jaffna Monitor - News & Publications</title>
    <link rel="preconnect" href="https://fonts.gstatic.com/" crossorigin="" />
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?display=swap&amp;family=Newsreader%3Awght%40400%3B500%3B700%3B800&amp;family=Noto+Sans%3Awght%40400%3B500%3B700%3B900" />
    <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
    <link rel="stylesheet" href="assets/styles.css">
    <style>
        .news-card {{
            transition: all 0.3s ease;
        }}
        .news-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }}
        .gradient-bg {{
            background: linear-gradient(135deg, #fcfbf8 0%, #f3f0e7 100%);
        }}
    </style>
</head>
<body class="bg-[#fcfbf8] font-['Newsreader','Noto_Sans',sans-serif]">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b border-[#f3f0e7] sticky top-0 z-50">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between items-center py-4">
                <div class="flex items-center space-x-4">
                    <div class="w-12 h-12 bg-[#9b844b] rounded-full flex items-center justify-center">
                        <span class="text-white font-bold text-xl">JM</span>
                    </div>
                    <div>
                        <h1 class="text-2xl font-bold text-[#1c170d]">Jaffna Monitor</h1>
                        <p class="text-sm text-[#9b844b]">News & Publications</p>
                    </div>
                </div>
                <nav class="hidden md:flex space-x-8">
                    <a href="index.html" class="text-[#1c170d] hover:text-[#9b844b] transition-colors">Home</a>
                    <a href="#" class="text-[#1c170d] hover:text-[#9b844b] transition-colors">News</a>
                    <a href="#" class="text-[#1c170d] hover:text-[#9b844b] transition-colors">About</a>
                    <a href="#" class="text-[#1c170d] hover:text-[#9b844b] transition-colors">Contact</a>
                </nav>
            </div>
        </div>
    </header>
    <section class="gradient-bg py-16">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h2 class="text-4xl md:text-6xl font-bold text-[#1c170d] mb-6">Latest News from Jaffna</h2>
            <p class="text-xl text-[#9b844b] max-w-3xl mx-auto">Stay informed with the latest stories, insights, and developments from the heart of Jaffna</p>
        </div>
    </section>
    <section class="py-16">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {cards}
            </div>
        </div>
    </section>
    <footer class="bg-[#1c170d] text-white py-12">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div>
                    <h3 class="text-xl font-bold mb-4">Jaffna Monitor</h3>
                    <p class="text-gray-300">Dedicated to bringing you the latest news and insights from Jaffna and beyond.</p>
                </div>
                <div>
                    <h4 class="text-lg font-semibold mb-4">Contact</h4>
                    <p class="text-gray-300">hellojaffnamonitor@gmail.com</p>
                    <p class="text-gray-300">Jaffna, Sri Lanka</p>
                </div>
                <div>
                    <h4 class="text-lg font-semibold mb-4">Follow Us</h4>
                    <div class="flex space-x-4">
                        <a href="#" class="text-gray-300 hover:text-white transition-colors">
                            <span class="sr-only">Facebook</span>
                            <svg class="h-6 w-6" fill="currentColor" viewBox="0 0 24 24"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>
                        </a>
                        <a href="#" class="text-gray-300 hover:text-white transition-colors">
                            <span class="sr-only">Twitter</span>
                            <svg class="h-6 w-6" fill="currentColor" viewBox="0 0 24 24"><path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/></svg>
                        </a>
                    </div>
                </div>
            </div>
            <div class="border-t border-gray-700 mt-8 pt-8 text-center">
                <p class="text-gray-300">&copy; 2024 Jaffna Monitor. All rights reserved.</p>
            </div>
        </div>
    </footer>
</body>
</html>
"""



IMAGE_BASE = 'assets/images'


def fix_image_paths(md_text: str) -> str:
    return re.sub(r'!\[(.*?)\]\((.*?)\)',
                  lambda m: f"![{m.group(1)}]({IMAGE_BASE}/{m.group(2).split('images_out/')[-1]})",
                  md_text)


def extract_metadata(md_text: str):
    title=author=date='Unknown'
    for line in md_text.splitlines()[:20]:
        if line.startswith('# '): title=line[2:]
        elif 'Jaffna Monitor' in line: author='Jaffna Monitor'
        elif re.match(r'\d{4}-\d{2}-\d{2}', line): date=line
    return title, author, date


def extract_first_image(md_text: str):
    m = re.search(r'!\[.*?\]\((.*?)\)', md_text)
    return m.group(1) if m else None


def generate_tags(md_text: str):
    stop={'the','and','of','in','to','a','was','as','for','with','on','by','at','is','that','this','it','from','an'}
    words=re.findall(r'\b\w+\b', md_text.lower())
    freq={}
    for w in words:
        if w not in stop and len(w)>3: freq[w]=freq.get(w,0)+1
    return sorted(freq, key=freq.get, reverse=True)[:5]


def generate_html(output_root: Path):
    """Generate HTML from existing html_output structure"""
    print(f"Processing existing structure in: {output_root}")
    
    # Create assets folder structure
    assets = output_root / 'assets'
    imgs = assets / 'images'
    imgs.mkdir(parents=True, exist_ok=True)
    
    # Copy CSS file if it exists
    css_source = Path('assets/styles.css')
    if css_source.exists():
        shutil.copy2(css_source, assets / 'styles.css')
    else:
        # Create a basic CSS file
        basic_css = """/* Custom styles for Jaffna Monitor */
.news-card { transition: all 0.3s ease; }
.news-card:hover { transform: translateY(-4px); box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1); }
.gradient-bg { background: linear-gradient(135deg, #fcfbf8 0%, #f3f0e7 100%); }
.prose img { max-width: 100%; height: auto; border-radius: 8px; margin: 2rem 0; }
.tag { background: #f3f0e7; padding: 4px 8px; border-radius: 12px; font-size: 0.875rem; margin: 2px; }
"""
        (assets / 'styles.css').write_text(basic_css, encoding='utf-8')
    
    all_articles = []
    
    # Process each e_books_jaffna_monitor folder
    for monitor_folder in output_root.glob('e_books_jaffna_monitor_*'):
        print(f"Processing: {monitor_folder.name}")
        
        # Copy images from this monitor folder
        images_source = monitor_folder / 'images_out'
        if images_source.exists():
            for img_file in images_source.rglob('*.*'):
                if img_file.is_file() and img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    # Create relative path structure
                    rel_path = img_file.relative_to(images_source)
                    dest_path = imgs / rel_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(img_file, dest_path)
                    print(f"  Copied: {rel_path}")
        
        # Process markdown files
        articles_folder = monitor_folder / 'articles'
        if articles_folder.exists():
            for md_file in articles_folder.glob('*.md'):
                print(f"  Processing: {md_file.name}")
                
                # Read and process markdown
                text = md_file.read_text(encoding='utf-8')
                
                # Fix image paths to point to assets/images
                text = re.sub(r'!\[(.*?)\]\((images_out/.*?)\)',
                             lambda m: f"![{m.group(1)}](assets/images/{m.group(2).split('images_out/')[-1]})",
                             text)
                
                # Extract metadata
                title, author, date = extract_metadata(text)
                html_content = markdown.markdown(text)
                tags = generate_tags(text)
                tag_elements = ''.join(f'<span class="tag">{t}</span>' for t in tags)
                first_img = extract_first_image(text)
                summary = re.sub(r'<.*?>', '', html_content)[:180] + '...' if len(html_content) > 180 else html_content
                
                # Create article link
                article_id = md_file.stem.split('_')[0]  # Get the numeric ID
                link = f"articles/{md_file.stem}.html"
                
                # Write HTML article
                out_html = output_root / link
                out_html.parent.mkdir(parents=True, exist_ok=True)
                out_html.write_text(
                    HTML_TEMPLATE.format(
                        title=title,
                        author=author,
                        date=date,
                        content=html_content,
                        tag_elements=tag_elements
                    ),
                    encoding='utf-8'
                )
                
                # Add to articles list
                all_articles.append({
                    'title': title,
                    'author': author,
                    'date': date,
                    'summary': summary,
                    'image': first_img,
                    'link': link,
                    'id': article_id
                })
    
    # Sort articles by ID
    all_articles.sort(key=lambda x: int(x['id']) if x['id'].isdigit() else 999)
    
    # Generate index page with cards
    cards = []
    for art in all_articles:
        if art['image']:
            img_html = f'<img src="{art["image"]}" alt="{art["title"]}" class="w-full h-48 object-cover rounded-t-lg">'
        else:
            img_html = '<div class="h-48 bg-gradient-to-br from-[#9b844b] to-[#1c170d] flex items-center justify-center"><span class="text-white text-4xl font-bold">JM</span></div>'
        
        card = f'''
        <article class="news-card bg-white rounded-lg overflow-hidden shadow-lg flex flex-col">
            {img_html}
            <div class="p-6 flex-1 flex flex-col">
                <div class="flex items-center text-sm text-[#9b844b] mb-2">
                    <span>{art["date"]}</span>
                    <span class="mx-2">•</span>
                    <span>{art["author"]}</span>
                </div>
                <h3 class="text-xl font-bold text-[#1c170d] mb-3 line-clamp-2">{art["title"]}</h3>
                <p class="text-gray-600 mb-4 line-clamp-3">{art["summary"]}</p>
                <a href="{art["link"]}" class="inline-flex items-center text-[#9b844b] hover:text-[#1c170d] transition-colors font-medium mt-auto">
                    Read More
                    <svg class="ml-2 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                    </svg>
                </a>
            </div>
        </article>
        '''
        cards.append(card)
    
    # Write index.html
    index_html = INDEX_TEMPLATE.format(cards='\n'.join(cards))
    (output_root / 'index.html').write_text(index_html, encoding='utf-8')
    
    print(f"Generated {len(all_articles)} articles")
    print(f"Created index.html with {len(cards)} cards")
    print(f"Assets copied to: {assets}")

# --- Main Execution ---

def main():
    # data=Path('data')
    out=Path('html_output')
    # if out.exists(): shutil.rmtree(out)
    # for pdf in data.glob('*.pdf'):
    #     extract_to_markdown(pdf, out/slugify(pdf.stem))
    generate_html(out)
    print("Finished: 'html_output' folder contains site files.")

if __name__=='__main__':
    main()

import os
import re
import markdown
import shutil

MD_FOLDER = "markdown_files"
ASSETS_FOLDER = "assets"
IMAGE_BASE_RELATIVE_PATH = "assets/images"

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

def fix_image_paths(md_text):
    pattern = r'!\[(.*?)\]\((.*?)\)'
    def repl(m):
        alt, path = m.group(1), m.group(2)
        if path.startswith("../images_out/"):
            path = IMAGE_BASE_RELATIVE_PATH + "/" + path.split("../images_out/")[1]
        elif path.startswith("images_out/"):
            path = IMAGE_BASE_RELATIVE_PATH + "/" + path.split("images_out/")[1]
        return f"![{alt}]({path})"
    return re.sub(pattern, repl, md_text)

def extract_metadata(md_text):
    title = author = date = "Unknown"
    lines = md_text.splitlines()
    for line in lines[:20]:
        if line.startswith("# "):
            title = line[2:].strip()
        elif "Jaffna Monitor" in line:
            author = "Jaffna Monitor"
        elif re.match(r'\d{4}|\d{2}', line):
            date = line.strip()
    return title, author, date

def extract_first_image(md_text):
    match = re.search(r'!\[.*?\]\((.*?)\)', md_text)
    if match:
        path = match.group(1)
        if path.startswith("../images_out/"):
            return IMAGE_BASE_RELATIVE_PATH + "/" + path.split("../images_out/")[1]
        elif path.startswith("images_out/"):
            return IMAGE_BASE_RELATIVE_PATH + "/" + path.split("images_out/")[1]
        else:
            return path
    return None

def generate_tags(md_text):
    stopwords = set(["the","and","of","in","to","a","was","as","for","with","on","by","at","is","that","this","it","from","an"])
    words = re.findall(r'\b\w+\b', md_text.lower())
    freq = {}
    for w in words:
        if w not in stopwords and len(w)>3:
            freq[w] = freq.get(w, 0) +1
    tags = sorted(freq, key=freq.get, reverse=True)[:5]
    return tags

def generate_tag_elements(tags):
    tag_elements = []
    for tag in tags:
        tag_elements.append(f'<span class="tag">{tag}</span>')
    return '\n'.join(tag_elements)

def setup_assets_folder():
    """Create assets folder structure and copy files"""
    # Create assets folder
    os.makedirs(ASSETS_FOLDER, exist_ok=True)
    os.makedirs(os.path.join(ASSETS_FOLDER, "images"), exist_ok=True)
    
    # Copy CSS file
    if os.path.exists("html_output/styles.css"):
        shutil.copy("html_output/styles.css", os.path.join(ASSETS_FOLDER, "styles.css"))
    
    # Copy images
    if os.path.exists("images_out"):
        for root, dirs, files in os.walk("images_out"):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    # Get relative path from images_out
                    rel_path = os.path.relpath(root, "images_out")
                    # Create destination directory
                    dest_dir = os.path.join(ASSETS_FOLDER, "images", rel_path)
                    os.makedirs(dest_dir, exist_ok=True)
                    # Copy file
                    src_file = os.path.join(root, file)
                    dest_file = os.path.join(dest_dir, file)
                    shutil.copy2(src_file, dest_file)

def main():
    # Setup assets folder
    setup_assets_folder()
    
    # Create articles folder
    articles_folder = "articles"
    os.makedirs(articles_folder, exist_ok=True)
    
    articles = []
    for mdfile in os.listdir(MD_FOLDER):
        if not mdfile.endswith(".md"):
            continue
        with open(os.path.join(MD_FOLDER, mdfile), encoding="utf-8") as f:
            md_text = f.read()

        md_text = fix_image_paths(md_text)
        title, author, date = extract_metadata(md_text)
        html_content = markdown.markdown(md_text)
        tags = generate_tags(md_text)
        tag_elements = generate_tag_elements(tags)
        first_image = extract_first_image(md_text)
        summary = re.sub(r'<.*?>', '', html_content)[:180] + '...' if len(html_content) > 180 else html_content
        outname = mdfile.replace(".md", ".html")
        
        final_html = HTML_TEMPLATE.format(
            title=title,
            author=author,
            date=date,
            content=html_content,
            tag_elements=tag_elements
        )
        
        # Save to articles folder
        outpath = os.path.join(articles_folder, outname)
        with open(outpath, "w", encoding="utf-8") as outf:
            outf.write(final_html)
        
        articles.append({
            "title": title,
            "author": author,
            "date": date,
            "tags": tags,
            "summary": summary,
            "image": first_image,
            "link": f"articles/{outname}"
        })
        print(f"Processed {mdfile} -> {outpath}")

    # Generate index.html in root
    cards = []
    for art in articles:
        img_html = f'<img src="{art["image"]}" alt="{art["title"]}" class="w-full h-48 object-cover rounded-t-lg">' if art["image"] else '<div class="h-48 bg-gradient-to-br from-[#9b844b] to-[#1c170d] flex items-center justify-center"><span class="text-white text-4xl font-bold">JM</span></div>'
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
                <a href="{art["link"]}" class="inline-flex items-center text-[#9b844b] hover:text-[#1c170d] transition-colors font-medium mt-auto">Read More<svg class="ml-2 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path></svg></a>
            </div>
        </article>
        '''
        cards.append(card)
    
    index_html = INDEX_TEMPLATE.format(cards='\n'.join(cards))
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    
    print("Generated index.html in root directory")
    print("Generated articles in articles/ folder")
    print("Generated assets in assets/ folder")

if __name__ == "__main__":
    main()
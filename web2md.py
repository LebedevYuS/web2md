import os
import re
import time
import random
import string
import urllib.parse
from datetime import datetime

import requests
from readability import Document
from bs4 import BeautifulSoup, NavigableString


def sanitize_filename(filename):
    filename = re.sub(r'[\\/*?:"<>|]', '', filename)
    filename = re.sub(r'\s+', '_', filename)
    filename = re.sub(r'_+', '_', filename)
    return filename.strip('_')


def generate_random_suffix(length=5):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def convert_html_to_markdown(element):
    """Рекурсивно преобразует HTML-элементы в Markdown"""
    markdown = []

    for child in element.children:
        if isinstance(child, NavigableString):
            text = str(child).strip()
            if text:
                markdown.append(text)
            continue

        tag = child.name
        if tag is None:
            continue

        # Обработка заголовков
        if tag.startswith('h') and len(tag) == 2 and tag[1].isdigit():
            level = int(tag[1])
            header = '#' * level + ' ' + child.get_text().strip()
            markdown.append(f"\n{header}\n")

        elif tag == 'p':
            text = child.get_text().strip()
            if text:
                markdown.append(f"\n{text}\n")

        elif tag == 'ul':
            for li in child.find_all('li', recursive=False):
                markdown.append(f"- {li.get_text().strip()}\n")
            markdown.append("\n")

        elif tag == 'ol':
            for i, li in enumerate(child.find_all('li', recursive=False), 1):
                markdown.append(f"{i}. {li.get_text().strip()}\n")
            markdown.append("\n")

        elif tag in ['strong', 'b']:
            markdown.append(f"**{child.get_text().strip()}**")

        elif tag in ['em', 'i']:
            markdown.append(f"*{child.get_text().strip()}*")

        elif tag == 'a':
            href = child.get('href', '')
            text = child.get_text().strip()
            markdown.append(f"[{text}]({href})")

        elif tag == 'code':
            markdown.append(f"`{child.get_text().strip()}`")

        elif tag == 'pre':
            code_text = child.get_text().strip()
            lang = ''
            if 'class' in child.attrs:
                for cls in child.attrs['class']:
                    if cls.startswith('language-'):
                        lang = cls.split('-', 1)[1]
                        break
            markdown.append(f"\n```{lang}\n{code_text}\n```\n")

        elif tag == 'blockquote':
            lines = child.get_text().strip().split('\n')
            quoted = '\n'.join([f"> {line}" for line in lines])
            markdown.append(f"\n{quoted}\n")

        else:
            nested_md = convert_html_to_markdown(child)
            if nested_md:
                markdown.append(nested_md)

    return '\n'.join(markdown).replace('\n \n', '\n\n').strip()


def read_urls_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return urls


def download_page(url, output_dir):
    try:
        print(f"Обрабатывается URL: {url}")
        time.sleep(1)

        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        response.raise_for_status()

        doc = Document(response.text)
        title = doc.title() or url.split('//')[-1].split('/')[0]
        soup = BeautifulSoup(doc.summary(), "html.parser")

        # Обработка изображений
        for img in soup.find_all("img"):
            img_url = img.get("src")
            if not img_url:
                continue

            if not img_url.startswith(("http://", "https://")):
                img_url = urllib.parse.urljoin(url, img_url)

            try:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                img_ext = os.path.splitext(img_url)[1][:4] or '.png'
                img_name = f"Pasted image {timestamp}_{generate_random_suffix()}{img_ext}"

                img_data = requests.get(img_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10).content
                with open(os.path.join(output_dir, img_name), "wb") as f:
                    f.write(img_data)

                obsidian_link = f"![[{img_name}]]"
                img.replace_with(obsidian_link)

            except Exception as e:
                print(f"Ошибка загрузки изображения {img_url}: {e}")
                img.replace_with(f"[Изображение]({img_url})")

        # Преобразуем в чистый Markdown
        markdown_content = convert_html_to_markdown(soup)

        # Создаём Markdown-документ
        md_content = f"# {title}\n\nURL: {url}\n\n{markdown_content}"
        md_content = re.sub(r'\n{3,}', '\n\n', md_content.strip())

        # Сохраняем файл
        counter = 0
        base_name = sanitize_filename(title)
        md_filename = f"{base_name}.md"
        while os.path.exists(os.path.join(output_dir, md_filename)):
            counter += 1
            md_filename = f"{base_name}_{counter}.md"

        with open(os.path.join(output_dir, md_filename), "w", encoding="utf-8") as f:
            f.write(md_content)

        print(f"Создан файл: {md_filename}")

    except Exception as e:
        print(f"Не удалось обработать {url}: {e}")


def main(urls_file, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    try:
        urls = read_urls_from_file(urls_file)
        if not urls:
            print(f"Файл {urls_file} не содержит допустимых URL")
            return

        print(f"Найдено URL для обработки: {len(urls)}")

        for url in urls:
            download_page(url, output_dir)

        print("✅ Обработка завершена")

    except FileNotFoundError:
        print(f"❌ Файл {urls_file} не найден")
    except Exception as e:
        print(f"❌ Ошибка: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Архивация веб-страниц в формате Markdown/Obsidian")
    parser.add_argument("--urls-file", required=True, help="Путь к файлу со списком URL (по одному на строке)")
    parser.add_argument("--output-dir", required=True, help="Каталог для сохранения .md файлов и изображений")

    args = parser.parse_args()

    main(args.urls_file, args.output_dir)
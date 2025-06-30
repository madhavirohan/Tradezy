import requests
from bs4 import BeautifulSoup, Tag
import pandas as pd
import re
import time
import sys

BASE_URL = "https://www.abf.gov.au/importing-exporting-and-manufacturing/tariff-classification/current-tariff/schedule-3"

def get_chapter_urls():
    section_names = [
        'i', 'ii', 'iii', 'iv', 'v', 'vi', 'vii', 'viii', 'ix', 'x',
        'xi', 'xii', 'xiii', 'xiv', 'xv', 'xvi', 'xvii', 'xviii', 'xix', 'xx', 'xxi'
    ]
    section_chapter_ranges = [
        (1, 5), (6, 14), (15, 15), (16, 24), (25, 27), (28, 38), (39, 40), (41, 43), (44, 46), (47, 49),
        (50, 63), (64, 67), (68, 70), (71, 71), (72, 83), (84, 85), (86, 89), (90, 92), (93, 93), (94, 96), (97, 99)
    ]
    urls = []
    for section, (start_chap, end_chap) in zip(section_names, section_chapter_ranges):
        for chap in range(start_chap, end_chap + 1):
            url = f"https://www.abf.gov.au/importing-exporting-and-manufacturing/tariff-classification/current-tariff/schedule-3/section-{section}/chapter-{chap}"
            urls.append((url, chap))
    return urls

def parse_chapter_page(url, chapter_num):
    resp = requests.get(url)
    soup = BeautifulSoup(resp.text, "html.parser")
    tables = soup.find_all("table")
    rows = []
    for table in tables:
        if not isinstance(table, Tag):
            continue
        for tr in table.find_all("tr"):
            if not isinstance(tr, Tag):
                continue
            tds = tr.find_all(["td", "th"])
            if len(tds) < 4:
                continue
            code = tds[0].get_text(strip=True)
            description = tds[3].get_text(strip=True)
            # Determine hierarchy by code format
            if re.fullmatch(r"\d{2}", code):
                # Chapter level (shouldn't appear here, but just in case)
                heading = subheading = ""
            elif re.fullmatch(r"\d{4}", code):
                heading = code
                subheading = ""
            elif re.fullmatch(r"\d{6,8}", code):
                heading = code[:4]
                subheading = code
            else:
                # Sometimes codes like '0101.2' or '0101.21.00' (with dots)
                code_digits = re.sub(r"\D", "", code)
                if len(code_digits) == 4:
                    heading = code_digits
                    subheading = ""
                elif len(code_digits) >= 6:
                    heading = code_digits[:4]
                    subheading = code_digits
                else:
                    continue
            rows.append({
                "Chapter": str(chapter_num).zfill(2),
                "Heading": heading if heading else "",
                "Subheading": subheading if subheading else "",
                "Description": description
            })
    return rows

def main():
    print("Fetching chapter URLs...")
    chapter_urls = get_chapter_urls()
    print(f"Found {len(chapter_urls)} chapter URLs.")
    all_rows = []
    for url, chapnum in chapter_urls:
        print(f"Parsing {url}")
        try:
            rows = parse_chapter_page(url, chapnum)
            all_rows.extend(rows)
            time.sleep(0.2)
        except Exception as e:
            print(f"Failed to parse {url}: {e}")
    print(f"Total rows scraped: {len(all_rows)}")
    if not all_rows:
        print("No data was scraped. Please check if the website structure has changed or if there is a connectivity issue.")
        sys.exit(1)
    print("Sample scraped rows:")
    for row in all_rows[:5]:
        print(row)
    df = pd.DataFrame(all_rows)
    print(f"DataFrame columns: {df.columns.tolist()}")
    df = df.sort_values(["Chapter", "Heading", "Subheading"])
    df.to_excel("hs_code_tree.xlsx", index=False)
    print("Exported to hs_code_tree.xlsx")

if __name__ == "__main__":
    main() 
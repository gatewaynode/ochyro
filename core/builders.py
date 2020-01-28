import os
import sys
import requests
import shutil
from bs4 import BeautifulSoup
import logging
import traceback
from pprint import pprint

# For SO snippet
import errno

# Stack overflow snippet from https://stackoverflow.com/questions/23793987/write-file-to-a-directory-that-doesnt-exist
# Taken from https://stackoverflow.com/a/600612/119527
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def safe_open_w(path):
    """ Open "path" for writing, creating any parent directories as needed.
    """
    mkdir_p(os.path.dirname(path))
    return open(path, "w")


# with safe_open_w('/Users/bill/output/output-text.txt') as f:
#     f.write(...)
# End Stack Overflow snippet


def capture_page(domain="http://localhost:5000", uri=""):
    """Simple GET or fail wrapper"""
    try:
        url = f"{domain}{uri}"
        r = requests.get(url)
        return r.text
    except Exception as e:
        logging.error(traceback.format_exc())
        sys.exit(1)


def find_links(page_data):
    """Find all <a> tag href values"""
    links = []
    soup = BeautifulSoup(page_data, "html.parser")
    for link in soup.find_all("a"):
        link_href = link.get("href")
        if (
            link_href.startswith("/")
            and link_href != "/index"
            and link_href != "/"
            and link_href not in links
        ):
            links.append(link_href)

    if links:
        return links
    else:
        return False


def find_and_crawl(pages, links):
    start_state = len(pages)
    new_pages = {}
    for page, data in pages.items():
        found_links = find_links(data["page_content"])
        if found_links:
            for new_link in found_links:
                if new_link not in links:
                    links.append(new_link)
                    new_pages[new_link] = {
                        "page_file_name": f"{new_link}.html",
                        "page_content": capture_page(
                            uri=new_link
                        ),  # Again need to add base here
                    }
    updated_pages = {**pages, **new_pages}

    stop_state = len(updated_pages)
    if stop_state != start_state:
        return find_and_crawl(updated_pages, links)
    else:  # Exit condition
        return updated_pages


def spider_pages(index_url):
    """Set the base condition for the recursive crawl"""
    links = []
    # collect index
    if index_url:
        pages = {
            index_url: {
                "page_file_name": "/index.html",
                "page_content": capture_page(uri=index_url),
            }
        }
    else:  # Assume the front page is the index
        pages = {
            "_index_": {
                "page_file_name": "/index.html",
                "page_content": capture_page(uri=index_url),
            }
        }

    returned_pages = find_and_crawl(pages=pages, links=links)

    return returned_pages


def htmlify_links(page_data):
    soup = BeautifulSoup(page_data, "html.parser")
    for link in soup.find_all("a"):
        if link["href"].startswith("/") and link["href"] != "/":
            # So convoluted, I kind of like it
            link["href"] = link["href"].replace(link["href"], f'{link["href"]}.html')
    return str(soup)


def build_static_site(data):
    """Build a static site"""

    index_page = ""
    pages_to_build = spider_pages(index_page)

    if pages_to_build:
        # Change a links to point to html pages
        for key, value in pages_to_build.items():
            pages_to_build[key]["page_content"] = htmlify_links(value["page_content"])

        # validate the build dir exists wipe it and rebuild at this endpoint
        if data["local_build_dir"] and os.path.isdir(data["local_build_dir"]):
            try:
                shutil.rmtree(data["local_build_dir"])
            except Exception as e:
                logging.error("There has been a problem removing the old site build.")
                logging.error(traceback.format_exc())
                return "Build Failed"

        # Create new build directory
        try:
            os.makedirs(data["local_build_dir"])
        except Exception as e:
            logging.error(traceback.format_exc())
            return "Build Failed"

        # Copy over the static files directory
        try:
            shutil.copytree(
                data["static_files_dir"], f"{data['local_build_dir']}/static"
            )
        except Exception as e:
            logging.error(traceback.format_exc())
            return "Build Failed"

        # Loop through the pages dict and create each page in the correct build dir
        for key, page in pages_to_build.items():
            print(f"{data['local_build_dir']}{page['page_file_name']}")
            with safe_open_w(
                f"{data['local_build_dir']}{page['page_file_name']}"
            ) as file:
                file.write(page["page_content"])

    return "Site build received"

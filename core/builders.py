import os
import sys
import requests
import shutil
from bs4 import BeautifulSoup
import logging
import traceback
from pprint import pprint


def capture_page(domain="http://localhost:5000", uri=""):
    try:
        url = f"{domain}{uri}"
        r = requests.get(url)
        return r.text
    except Exception as e:
        logging.error(traceback.format_exc())
        sys.exit(1)


def find_links(page_data):
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
    print(f"Start state: {start_state}")
    for page, data in pages.items():
        found_links = find_links(data["page_content"])
        print(f"Found Links: {found_links}")
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
    else:
        return updated_pages


def spider_pages(index_url):
    links = []
    # collect index
    if index_url:
        pages = {
            index_url: {
                "page_file_name": "index.html",
                "page_content": capture_page(uri=index_url),
            }
        }
    else:  # Assume the front page is the index
        pages = {
            "_index_": {
                "page_file_name": "index.html",
                "page_content": capture_page(uri=index_url),
            }
        }

    returned_pages = find_and_crawl(pages=pages, links=links)

    return returned_pages


def htmlify_links(page_data):
    links = []
    soup = BeautifulSoup(page_data, "html.parser")
    for link in soup.find_all("a"):
        if link["href"].startswith("/") and link["href"] != "/":
            # So convoluted, I kind of like it
            link["href"] = link["href"].replace(link["href"], f'{link["href"]}.html')
    return str(soup)


def change_login(page_data):
    pass


def build_static_site(data):
    """Build a static site"""

    index_page = ""
    pages_to_build = spider_pages(index_page)

    # Change a links to point to html pages
    for key, value in pages_to_build.items():
        pages_to_build[key]["page_content"] = htmlify_links(value["page_content"])

    # Replace the login link with the project link

    # if data["local_build_dir"] and os.path.isdir(
    #     data["local_build_dir"]
    # ):  # validate the build dir exists
    #     # wipe it and rebuild at this endpoint
    #
    #     try:
    #         shutil.rmtree(data["local_build_dir"])
    #     except Exception as e:
    #         logging.error("There has been a problem removing the old site build.")
    #         logging.error(traceback.format_exc())
    #         return "Build Failed"
    #
    # try:
    #     os.makedirs(data["local_build_dir"])
    # except Exception as e:
    #     logging.error(traceback.format_exc())
    #     return "Build Failed"
    #
    # try:
    #     r = requests.get(
    #         "http://localhost:5000"
    #     )  # Cheating here, seems the index field needs to be more requests centric
    #     index_page = r.text
    # except Exception as e:
    #     logging.error(traceback.format_exc())
    #     return "Build Failed"
    #
    # try:
    #     shutil.copytree(data["static_files_dir"], f"{data['local_build_dir']}/static")
    # except Exception as e:
    #     logging.error(traceback.format_exc())
    #     return "Build Failed"
    #
    # try:
    #     with open(f"{data['local_build_dir']}/index.html", "w") as file:
    #         file.write(index_page)
    # except Exception as e:
    #     logging.error(traceback.format_exc())
    #     return "Build Failed"

    # Spider links
    # if index_page:
    #     soup = BeautifulSoup(index_page, "html.parser")
    #     links = []
    #     for link in soup.find_all("a"):
    #         link_href = link.get("href")
    #         if link_href.startswith("/") and link_href != "/index" and link_href != "/":
    #             print(link.get("href"))

    return "Site build received"

import os
from typing import Dict, Any, List

from dotenv import load_dotenv
from notion_client import Client


load_dotenv()


NOTION_TOKEN = os.getenv("NOTION_TOKEN")


if not NOTION_TOKEN:
    raise RuntimeError(
        "NOTION_TOKEN is missing from the .env file."
    )


notion = Client(auth=NOTION_TOKEN)


def search_notion(query: str) -> List[Dict[str, Any]]:
    """
    Search the Notion workspace for pages matching a query.
    """

    if not query or not query.strip():
        raise ValueError(
            "Notion search query cannot be empty."
        )

    response = notion.search(
        query=query.strip()
    )

    results = []

    for item in response.get("results", []):

        if item.get("object") != "page":
            continue

        page_id = item.get("id")

        properties = item.get(
            "properties",
            {}
        )

        title = extract_page_title(
            properties
        )

        results.append(
            {
                "id": page_id,
                "title": title,
                "url": item.get("url"),
            }
        )

    return results


def extract_page_title(
    properties: Dict[str, Any]
) -> str:
    """
    Extract the title from a Notion page.
    """

    for property_data in properties.values():

        if property_data.get("type") != "title":
            continue

        title_items = property_data.get(
            "title",
            []
        )

        title = "".join(
            item.get("plain_text", "")
            for item in title_items
        )

        if title:
            return title

    return "Untitled"


def get_page_blocks(
    page_id: str
) -> List[Dict[str, Any]]:
    """
    Retrieve all blocks belonging to a Notion page.
    """

    if not page_id:
        raise ValueError(
            "Notion page ID cannot be empty."
        )

    blocks = []

    response = notion.blocks.children.list(
        block_id=page_id
    )

    blocks.extend(
        response.get("results", [])
    )

    # Handle pagination.
    while response.get("has_more"):

        response = notion.blocks.children.list(
            block_id=page_id,
            start_cursor=response.get(
                "next_cursor"
            ),
        )

        blocks.extend(
            response.get("results", [])
        )

    return blocks


def block_to_text(
    block: Dict[str, Any]
) -> str:
    """
    Convert a Notion block into plain text.
    """

    block_type = block.get(
        "type",
        ""
    )

    data = block.get(
        block_type,
        {}
    )

    rich_text = data.get(
        "rich_text",
        []
    )

    text = "".join(
        item.get("plain_text", "")
        for item in rich_text
    )

    return text.strip()


def get_page_content(
    page_id: str
) -> str:
    """
    Retrieve and convert a Notion page into plain text.
    """

    blocks = get_page_blocks(
        page_id
    )

    lines = []

    for block in blocks:

        text = block_to_text(
            block
        )

        if text:
            lines.append(text)

    return "\n".join(lines)


def get_project_from_notion(
    project_name: str
) -> Dict[str, Any]:
    """
    Search for a project and retrieve its content.
    """

    if not project_name or not project_name.strip():
        raise ValueError(
            "Project name cannot be empty."
        )

    search_results = search_notion(
        project_name
    )

    if not search_results:
        return {
            "found": False,
            "project_name": project_name,
            "results": [],
        }

    projects = []

    for result in search_results:

        content = get_page_content(
            result["id"]
        )

        projects.append(
            {
                "id": result["id"],
                "title": result["title"],
                "url": result["url"],
                "content": content,
            }
        )

    return {
        "found": True,
        "project_name": project_name,
        "results": projects,
    }


if __name__ == "__main__":

    print("=" * 60)
    print("NOTION TOOL TEST")
    print("=" * 60)

    project_name = "Project X"

    print()
    print(f"Searching Notion for: {project_name}")

    result = get_project_from_notion(
        project_name
    )

    print()
    print(f"Found: {result['found']}")

    if result["found"]:

        for project in result["results"]:

            print()
            print(
                f"Title: {project['title']}"
            )

            print(
                f"URL: {project['url']}"
            )

            print()
            print("Content:")
            print(
                project["content"]
            )

    else:

        print(
            "Project was not found in Notion."
        )
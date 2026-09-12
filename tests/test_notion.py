from app.tools.notion import (
    search_notion,
    get_project_from_notion,
)


def test_notion_search():

    results = search_notion(
        "Project X"
    )

    assert isinstance(
        results,
        list
    )


def test_project_x_retrieval():

    result = get_project_from_notion(
        "Project X"
    )

    assert "found" in result
    assert "project_name" in result
    assert "results" in result

    assert result["project_name"] == "Project X"

    if result["found"]:

        assert len(
            result["results"]
        ) > 0

        first_result = result["results"][0]

        assert "id" in first_result
        assert "title" in first_result
        assert "content" in first_result
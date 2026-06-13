"""GitHub Profile Stats Generator.

Fetches contribution and language statistics from the GitHub GraphQL API
and renders them into an SVG card using a Jinja2 template.
"""

import os
import sys
from collections import defaultdict

import requests
from jinja2 import Environment, FileSystemLoader

GITHUB_API_URL = "https://api.github.com/graphql"

# Initial query: profile, contributions, first page of repositories
INITIAL_QUERY = """
query {
  viewer {
    login
    name
    contributionsCollection {
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      restrictedContributionsCount
    }
    repositories(first: 100, ownerAffiliations: OWNER, orderBy: {field: CREATED_AT, direction: DESC}) {
      totalCount
      nodes {
        name
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node { name color }
          }
        }
      }
      pageInfo { hasNextPage endCursor }
    }
  }
}
"""

# Pagination query for remaining repositories
PAGINATION_QUERY = """
query($cursor: String!) {
  viewer {
    repositories(first: 100, ownerAffiliations: OWNER, after: $cursor, orderBy: {field: CREATED_AT, direction: DESC}) {
      nodes {
        name
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node { name color }
          }
        }
      }
      pageInfo { hasNextPage endCursor }
    }
  }
}
"""


def fetch_graphql(query: str, variables: dict | None = None, *, token: str) -> dict:
    """Execute a GraphQL query against the GitHub API."""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    resp = requests.post(
        GITHUB_API_URL,
        json={"query": query, "variables": variables},
        headers=headers,
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"Error: API returned status {resp.status_code}", file=sys.stderr)
        print(resp.text, file=sys.stderr)
        sys.exit(1)

    data = resp.json()
    if "errors" in data:
        print("Error: GraphQL errors:", file=sys.stderr)
        for err in data["errors"]:
            print(f"  - {err.get('message')}", file=sys.stderr)
        sys.exit(1)

    return data["data"]


def format_number(n: int) -> str:
    """Format a number with comma separators (e.g. 1,234)."""
    return f"{n:,}"


def main() -> None:
    token = os.environ.get("PERSONAL_ACCESS_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        print(
            "Error: PERSONAL_ACCESS_TOKEN or GITHUB_TOKEN environment variable is required.",
            file=sys.stderr,
        )
        sys.exit(1)

    # ── Fetch data ──────────────────────────────────────────────
    print("Fetching stats from GitHub GraphQL API...")
    data = fetch_graphql(INITIAL_QUERY, token=token)

    viewer = data.get("viewer")
    if not viewer:
        print("Error: Failed to fetch viewer data.", file=sys.stderr)
        sys.exit(1)

    login = viewer["login"]
    contribs = viewer.get("contributionsCollection", {})
    commits = contribs.get("totalCommitContributions", 0)
    prs = contribs.get("totalPullRequestContributions", 0)
    issues = contribs.get("totalIssueContributions", 0)
    private_contribs = contribs.get("restrictedContributionsCount", 0)
    total_contributions = commits + prs + issues + private_contribs

    # Collect all repositories (with pagination)
    repos_data = viewer.get("repositories", {})
    repos: list[dict] = list(repos_data.get("nodes", []))
    page_info = repos_data.get("pageInfo", {})
    total_repos = repos_data.get("totalCount", len(repos))

    while page_info.get("hasNextPage"):
        cursor = page_info["endCursor"]
        print(f"  Fetching more repositories (cursor: {cursor[:12]}...)...")
        page_data = fetch_graphql(PAGINATION_QUERY, variables={"cursor": cursor}, token=token)
        page_repos = page_data["viewer"]["repositories"]
        repos.extend(page_repos.get("nodes", []))
        page_info = page_repos.get("pageInfo", {})

    print(f"  Fetched {len(repos)}/{total_repos} repositories.")

    # ── Aggregate stats ─────────────────────────────────────────
    total_stars = 0
    lang_agg: dict[str, dict] = defaultdict(lambda: {"size": 0, "color": None})

    for repo in repos:
        total_stars += repo.get("stargazerCount", 0)
        for edge in (repo.get("languages") or {}).get("edges", []):
            node = edge["node"]
            name = node["name"]
            lang_agg[name]["size"] += edge["size"]
            if node.get("color"):
                lang_agg[name]["color"] = node["color"]

    total_size = sum(v["size"] for v in lang_agg.values())
    languages: list[dict] = []
    if total_size > 0:
        for name, info in lang_agg.items():
            languages.append({
                "name": name,
                "percentage": (info["size"] / total_size) * 100,
                "color": info["color"] or "#8b949e",
            })
        languages.sort(key=lambda x: x["percentage"], reverse=True)

    # ── Render SVG ──────────────────────────────────────────────
    print("Rendering SVG...")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env = Environment(
        loader=FileSystemLoader(script_dir),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template(os.path.join("templates", "stats.svg.j2"))

    svg = template.render(
        login=login,
        total_contributions=format_number(total_contributions),
        commits=format_number(commits),
        prs=format_number(prs),
        private_contribs=format_number(private_contribs),
        stars=format_number(total_stars),
        languages=languages,
    )

    output = os.path.join(script_dir, "github-stats.svg")
    with open(output, "w", encoding="utf-8") as f:
        f.write(svg)

    print(f"Done → {output}")


if __name__ == "__main__":
    main()

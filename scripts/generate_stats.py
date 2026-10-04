import json
import os
import urllib.request
import urllib.error


GITHUB_API = "https://api.github.com/graphql"


QUERY = """
query {
  viewer {
    login
    name
    publicRepositories: repositories(
      ownerAffiliations: OWNER
      first: 100
      privacy: PUBLIC
    ) {
      totalCount
      nodes {
        name
        stargazerCount
        forkCount
      }
    }
  }
}
"""


def github_graphql(token: str, query: str) -> dict:
    """Send a GraphQL query to GitHub."""

    payload = json.dumps({
        "query": query
    }).encode("utf-8")

    request = urllib.request.Request(
        GITHUB_API,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "SRINATHsupes-profile",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request) as response:
            result = json.load(response)

    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8")
        raise RuntimeError(
            f"GitHub API returned HTTP {error.code}:\n{body}"
        ) from error

    if "errors" in result:
        raise RuntimeError(
            "GitHub GraphQL returned errors:\n"
            + json.dumps(result["errors"], indent=2)
        )

    return result["data"]


def main() -> None:
    token = os.environ.get("GITHUB_TOKEN")

    if not token:
        raise RuntimeError(
            "GITHUB_TOKEN is not set."
        )

    print("Connecting to GitHub GraphQL API...")

    data = github_graphql(
        token,
        QUERY,
    )

    viewer = data["viewer"]
    repositories = viewer["publicRepositories"]

    print()
    print("GitHub account")
    print("----------------")
    print(f"Login: {viewer['login']}")
    print(f"Name:  {viewer['name']}")
    print(f"Public repositories: {repositories['totalCount']}")

    print()
    print("Repositories")
    print("----------------")

    for repo in repositories["nodes"]:
        print(
            f"{repo['name']}: "
            f"{repo['stargazerCount']} stars, "
            f"{repo['forkCount']} forks"
        )


if __name__ == "__main__":
    main()

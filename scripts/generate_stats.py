import json
import os
import urllib.request
import urllib.error


GITHUB_API = "https://api.github.com/graphql"


QUERY = """
query($login: String!) {
  user(login: $login) {
    login
    name

    repositories(
      first: 100
      ownerAffiliations: OWNER
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


def github_graphql(token: str, login: str) -> dict:
    """Send a GraphQL query to GitHub."""

    payload = json.dumps({
        "query": QUERY,
        "variables": {
            "login": login,
        },
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
    login = os.environ.get("GH_LOGIN")

    if not token:
        raise RuntimeError(
            "GITHUB_TOKEN is not set."
        )

    if not login:
        raise RuntimeError(
            "GH_LOGIN is not set."
        )

    print("Connecting to GitHub GraphQL API...")
    print(f"Querying profile: {login}")

    data = github_graphql(
        token,
        login,
    )

    user = data["user"]
    repositories = user["repositories"]

    print()
    print("GitHub account")
    print("----------------")
    print(f"Login: {user['login']}")
    print(f"Name:  {user['name']}")
    print(
        f"Public repositories: "
        f"{repositories['totalCount']}"
    )

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

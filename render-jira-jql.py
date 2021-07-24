import os

from dotenv import load_dotenv
from jira import JIRA


def sanitize_issue_key(issue_key):
    return "\"" + issue_key + "\""


# Simple object to write down a single issue, being able to write it out to graphviz.
class GraphIssue:
    def __init__(self, issue, jira_url):
        self.issue_key = issue.key
        self.link = jira_url + "/browse/" + issue.key
        self.color = issue.fields.status.statusCategory.colorName

    def __str__(self):
        attrs = [
            "color=" + self.color.replace("blue-gray", "blue"),
            "href=\"" + self.link + "\"",
        ]

        return sanitize_issue_key(self.issue_key) + "[" + ", ".join(attrs) + "]"


# Simple object to write down, who is blocked by whom (one to one).
class BlockedBy:
    def __init__(self, source, target):
        self.source = source
        self.target = target

    def __str__(self):
        return sanitize_issue_key(self.source) + " -> " + sanitize_issue_key(self.target)


# Login to Jira, run the JQL and find the links between the found issues.
def find_issues_and_blocked_by_links(jira_url, jira_user, jira_password, jql):
    jira = JIRA(
        jira_url,
        {},
        (
            jira_user,
            jira_password
        )
    )

    result = jira.search_issues(
        jql,
        0,
        1000
    )

    for issue in result:
        links = issue.fields.issuelinks
        blocked_by_key = []

        # Write down the issue key, we want to have them included in the graph.
        allIssues.append(GraphIssue(issue, jira_url))

        # Scan the links.
        for issue_key in links:
            # Is it an inward link?
            if not hasattr(issue_key, 'inwardIssue'):
                continue

            # Does it match the defined text?
            if issue_key.type.inward != os.getenv('JIRA_INWARD_LINK'):
                continue

            # It's a match, so link them in the graph.
            blocked_by_key.append(issue_key.inwardIssue.key)

        if len(blocked_by_key) == 0:
            continue

        for issue_key in blocked_by_key:
            allBlocks.append(BlockedBy(issue.key, issue_key))


# Write out the graphviz dot file.
def write_graphviz_file(label):
    file_content = [
        "digraph {",
        "label = \"" + label + "\""
    ]

    # Define all found issues.
    for issue_key in allIssues:
        file_content.append(issue_key.__str__())

    # Define all found "blocked by" links.
    for block_entry in allBlocks:
        file_content.append(block_entry.__str__())

    file_content.append("}")

    file = open("input.dot", "w")
    file.write("\n".join(file_content))
    file.close()


# Load environment variables from .env file.
load_dotenv()

# Create container for "blocked by" links.
allBlocks = []
# Create container for "all found issues".
allIssues = []

find_issues_and_blocked_by_links(
    os.getenv('JIRA_URL'),
    os.getenv('JIRA_USER'),
    os.getenv('JIRA_PASSWORD'),
    os.getenv('JIRA_JQL')
)

write_graphviz_file(os.getenv('JIRA_JQL').replace("\"", "\\\""))

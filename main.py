from praw import Reddit
from praw.models.reddit.subreddit import Subreddit
from praw.models.reddit.submission import Submission
from praw.models.reddit.redditor import Redditor
from praw.models.reddit.comment import Comment
from dotenv import load_dotenv

from enum import Enum
from datetime import datetime, timedelta
from typing import TypedDict
import os


class UserSort(Enum):
    BY_POST = 'posts'
    BY_COMMENTS = 'comments'


class UserActivity(TypedDict):
    user: Redditor
    posts: int
    comments: int


class RedditClient:
    SUBMISSION_LIMIT: int = 20
    client: Reddit
    subreddit: Subreddit
    submissions: list[Submission]
    comments: list[Comment]
    users: dict[Redditor, UserActivity]

    def __init__(
            self,
            client_id: str | None,
            client_secret: str | None,
            user_agent: str | None
            ) -> None:
        self.client = Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent,
        )
        self.users = dict()

    def get_users_top(
            self, sort: UserSort = UserSort.BY_POST,
            limit: int = 5) -> list[tuple[Redditor, UserActivity]]:
        return sorted(
            self.users.items(), key=lambda x: x[1][sort.value], reverse=True
            )[:limit]

    def get_subreddit(self, name: str) -> None:
        self.subreddit = self.client.subreddit(name)

    def get_submissions(self, last_days: int = 3) -> None:
        self.submissions = []
        last_days_date = datetime.now() - timedelta(days=last_days)

        for submission in self.subreddit.new(limit=self.SUBMISSION_LIMIT):
            created_at = datetime.fromtimestamp(submission.created_utc)
            if created_at < last_days_date:
                break
            self.submissions.append(submission)

    def get_comments(self, submission: Submission) -> list[Comment]:
        submission.comments.replace_more()
        return submission.comments.list()

    def get_all_submission_authors(self) -> None:
        for submission in self.submissions:
            author = submission.author
            if author not in self.users:
                self.users.update({author: {'posts': 0, 'comments': 0}})
            self.users[author]["posts"] += 1

    def get_all_comment_authors(self) -> None:
        for submission in self.submissions:
            comments = self.get_comments(submission)
            for comment in comments:
                author = comment.author
                if author not in self.users:
                    self.users.update({author: {'posts': 0, 'comments': 0}})
                self.users[author]["comments"] += 1


def main() -> None:
    load_dotenv()
    reddit_client = RedditClient(
        client_id=os.getenv("client_id"),
        client_secret=os.getenv("client_secret"),
        user_agent=os.getenv("user_agent"),
    )
    reddit_client.get_subreddit('python')
    reddit_client.get_submissions(last_days=3)
    reddit_client.get_all_submission_authors()
    reddit_client.get_all_comment_authors()
    print(reddit_client.get_users_top(sort=UserSort.BY_POST, limit=3))
    print(reddit_client.get_users_top(sort=UserSort.BY_COMMENTS, limit=3))


if __name__ == '__main__':
    main()

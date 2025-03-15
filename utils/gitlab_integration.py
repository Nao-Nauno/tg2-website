import gitlab
import os
from datetime import datetime, timezone

class GitLabIntegration:
    def __init__(self, url='https://gitlab.com', private_token=None, project_id=None):
        self.url = url
        self.private_token = private_token or os.environ.get('GITLAB_API_TOKEN')
        self.project_id = project_id or os.environ.get('GITLAB_PROJECT_ID', 'fajeth-modpack/megamodpack-reforged')
        self.gl = None
        self.project = None
        
    def connect(self):
        """Connect to GitLab API"""
        try:
            self.gl = gitlab.Gitlab(self.url, private_token=self.private_token)
            self.gl.auth()
            self.project = self.gl.projects.get(self.project_id)
            return True
        except Exception as e:
            print(f"GitLab connection error: {str(e)}")
            return False

    def get_top_contributors(self, count=5):
        """Get top contributors with more detailed information"""
        if not self.project:
            if not self.connect():
                return None
        
        try:
            # Try to get repository contributors
            contributors = self.project.repository_contributors(all=True)
            
            # Sort contributors by number of commits
            top_contributors = sorted(contributors, key=lambda x: x['commits'], reverse=True)[:count]
            
            # Calculate total commits for percentage calculation
            total_commits = sum(contributor['commits'] for contributor in top_contributors)
            
            return [
                {
                    'name': contributor['name'],
                    'avatar': self._get_gravatar_url(contributor.get('email', ''), size=120),
                    'commits': contributor['commits'],
                    'commit_percentage': round((contributor['commits'] / total_commits) * 100, 1),
                    'username': contributor.get('username', contributor['name'].lower().replace(' ', '_'))
                }
                for contributor in top_contributors
            ]
        except Exception as e:
            print(f"Error fetching top contributors: {str(e)}")
            return []
            
    def get_latest_commit(self):
        """Get the latest commit information"""
        if not self.project:
            if not self.connect():
                return None
                
        try:
            # Added get_all=False to suppress the warning
            commits = self.project.commits.list(per_page=1, get_all=False)
            if commits:
                commit = commits[0]
                return {
                    'id': commit.id,
                    'short_id': commit.short_id,
                    'title': commit.title,
                    'author_name': commit.author_name,
                    'created_at': commit.created_at,
                    'time_ago': self._time_ago(commit.created_at)
                }
        except Exception as e:
            print(f"Error fetching commits: {str(e)}")
        return None
    
    def get_project_stats(self):
        """Get project statistics"""
        if not self.project:
            if not self.connect():
                return None
                
        try:
            # Added get_all=False to suppress the warning
            branches = self.project.branches.list(all=True, get_all=False)
            branch_count = len(branches)
            
            # Get commit count (this might not be efficient for large repos)
            commit_count = 0
            try:
                # Try to get from repository_data if available
                commit_count = self.project.repository_contributors[0]['commits']
            except:
                # Fallback to manually counting up to 100 commits
                commits = self.project.commits.list(per_page=100, get_all=False)
                commit_count = len(commits)
            
            return {
                'branch_count': branch_count,
                'commit_count': commit_count
            }
        except Exception as e:
            print(f"Error fetching project stats: {str(e)}")
        return None

    def _time_ago(self, timestamp_str):
        """Convert timestamp to more precise 'time ago' format"""
        try:
            # Ensure we're working with a timezone-aware datetime
            from dateutil import parser
            
            # Parse the timestamp and convert to UTC if it's not already
            commit_time = parser.parse(timestamp_str)
            if commit_time.tzinfo is None:
                commit_time = commit_time.replace(tzinfo=timezone.utc)
            
            # Convert to UTC if not already
            now = datetime.now(timezone.utc)
            diff = now - commit_time
            
            # Calculate time difference
            seconds = diff.total_seconds()
            if seconds < 60:
                return f"{int(seconds)} sec ago"
            minutes = seconds / 60
            if minutes < 60:
                return f"{int(minutes)} min ago"
            hours = minutes / 60
            if hours < 24:
                return f"{int(hours)} hr ago"
            days = hours / 24
            if days < 30:
                return f"{int(days)} days ago"
            months = days / 30
            if months < 12:
                return f"{int(months)} months ago"
            years = months / 12
            return f"{int(years)} years ago"
        except Exception as e:
            print(f"Error calculating time ago: {str(e)}")
            return "just now"

    def _get_user_avatar(self, commit):
        """Fetch the avatar for the commit author"""
        try:
            # Ensure we have a connection
            if not self.gl:
                self.connect()
            
            # Try to find the user by email
            users = self.gl.users.list(search=commit.author_email)
            
            if users:
                # Return the first user's avatar URL
                return users[0].avatar_url
            
            # Fallback to Gravatar if no GitLab user found
            return self._get_gravatar_url(commit.author_email)
        
        except Exception as e:
            print(f"Error fetching user avatar: {str(e)}")
            return None

    def _get_gravatar_url(self, email, size=80):
        """Generate Gravatar URL for an email"""
        import hashlib
        email = email.lower().strip()
        email_hash = hashlib.md5(email.encode('utf-8')).hexdigest()
        return f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d=identicon"

    def get_multiple_commits(self, count=4):
        """Get multiple recent commits"""
        if not self.project:
            if not self.connect():
                return None
                
        try:
            commits = self.project.commits.list(per_page=count, get_all=False)
            return [
                {
                    'id': commit.id,
                    'short_id': commit.short_id,
                    'title': commit.title,
                    'author_name': commit.author_name,
                    'author_email': commit.author_email,
                    'author_avatar': self._get_user_avatar(commit),
                    'created_at': commit.created_at,
                    'time_ago': self._time_ago(commit.created_at)
                }
                for commit in commits
            ]
        except Exception as e:
            print(f"Error fetching commits: {str(e)}")
        return None

    def _get_author_avatar(self, commit):
        """Try to get author avatar (you might need to implement this based on your GitLab setup)"""
        try:
            # This is a placeholder. You might need to implement actual avatar fetching
            # For example, you could use Gravatar or GitLab's avatar API
            return f"https://www.gravatar.com/avatar/{hash(commit.author_email)}?d=identicon"
        except:
            return None
import os
import gitlab

# Print environment variables (without printing the actual token value)
print(f"GITLAB_URL: {os.environ.get('GITLAB_URL', 'Not set')}")
print(f"GITLAB_PROJECT_ID: {os.environ.get('GITLAB_PROJECT_ID', 'Not set')}")
print(f"GITLAB_API_TOKEN: {'Set' if os.environ.get('GITLAB_API_TOKEN') else 'Not set'}")

try:
    # Try to connect to GitLab
    gl = gitlab.Gitlab(
        os.environ.get('GITLAB_URL', 'https://gitlab.com'),
        private_token=os.environ.get('GITLAB_API_TOKEN')
    )
    gl.auth()
    print("GitLab authentication successful!")
    
    # Try to get the project
    project_id = os.environ.get('GITLAB_PROJECT_ID', 'fajeth-modpack/megamodpack-reforged')
    print(f"Attempting to fetch project: {project_id}")
    project = gl.projects.get(project_id)
    print(f"Project found: {project.name}")
    
    # Try to get latest commit
    commits = project.commits.list(per_page=1)
    if commits:
        commit = commits[0]
        print(f"Latest commit: {commit.title} by {commit.author_name}")
    else:
        print("No commits found")
    
except Exception as e:
    print(f"Error: {str(e)}")
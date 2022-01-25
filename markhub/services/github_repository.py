from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Union, Optional
from django.contrib.auth.models import User
from django.http.request import HttpRequest

from github import Github
from github.ContentFile import ContentFile
from github.Repository import Repository

def get_github_handler(user: User) -> Union[Github, None]:
    """ Get github handler for user

    Args:
        user: Django User

    Returns:
        Github object for user if it has a token, otherwise None
    """
    social_account = user.socialaccount_set
    if social_account.exists() and social_account.first().provider == 'github':
        social_login = social_account.first().socialtoken_set
        if social_login.exists():
            return Github(social_login.first().token)    

class GitHubRepository:
    """GitHub Repository handler via session"""

    def __init__(self, request: HttpRequest, repo_name: str) -> None:
        """ Create Repository object for repo from session or via GitHub request
        
        Args: 
            request: Django request object
            repo_name: Repository name
        """
        if repo_name in request.session:
            self.handler: Repository =  request.session[repo_name]
            self.branches = request.session[f'{repo_name}__branches']
            self.branch = request.session[f'{repo_name}__current_branch']
        else:
            user: User = request.user
            g: Github = get_github_handler(user)
            if g:
                self.handler = g.get_repo(f"{user.username}/{repo_name}")
                if self.handler:
                    self.branches: List = [branch.name for branch in self.handler.get_branches()]
                    request.session[repo_name] = self.handler
                    request.session[f'{repo_name}__branches'] = self.branches
                    self.save_current_branch(request, self.handler.default_branch)
        request.session['__current_repo__'] = repo_name

    def save_current_branch(self, request: HttpRequest, branch: str) -> None:
        """ Save repository in session
        
        Args:
            request: Django request object
            branch: branch name
        """
        self.branch = branch
        request.session[f'{self.handler.name}__current_branch'] = self.branch

    @property
    def name(self) -> Optional[str]:
        """Returns repository name"""
        if self.handler:
            return self.handler.name
    
    def _get_user_repo(self, user: User, repo: str) -> Union[Repository, None]:
        """ Get user repo
        
        Args: 
            user: Django User
            repo: Repository name

        Returns: 
            Repository object if it exists, otherwise None
        """
        g: Github = get_github_handler(user)
        if g:
            repo = g.get_repo(f"{user.username}/{repo}")
            if repo:
                return repo

    def get_path_parts(self, path: str) -> Dict:
        """ Get path parts dict for path
        
        Args:
            path: repository item path

        Returns:
            Path parts dict (dir: path to dir)
        """

        path_parts = Path(path).parts
        path_parts_dict = {}
        for i in range(len(path_parts)):
            path_parts_dict[path_parts[i]] = '/'.join(path_parts[:i+1])
        return path_parts_dict

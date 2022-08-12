from pathlib import Path, PurePosixPath
from typing import Dict, List, Optional, Union

from django.contrib.auth.models import User
from django.http import Http404
from django.http.request import HttpRequest
from django.utils.html import format_html
from github import Github, UnknownObjectException
from github.ContentFile import ContentFile
from github.Repository import Repository
from markhub.models import PrivatePublish
from markhub.settings import log_error_with_404, logger


@logger.catch
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
                try:
                    self.handler = g.get_repo(f"{user.username}/{repo_name}")
                    if self.handler:
                        self.branches: List = [branch.name for branch in self.handler.get_branches()]
                        request.session[repo_name] = self.handler
                        request.session[f'{repo_name}__branches'] = self.branches
                        self.save_current_branch(request, self.handler.default_branch)
                        logger.info(f"{user.username}/{repo_name} have got from GitHub")
                except UnknownObjectException as e:
                    log_error_with_404(f"Repository not found - {e}")
        if self.handler:
            self.user = self.handler.owner.name
            request.session['__current_repo__'] = repo_name

    def create_file(self, path: str, content: str, branch: str = '') -> str:
        """Create a new file in the repository if success otherwise raise 404 exception

        Args:
            path (str): path to the new file
            updated_content (str): new file content
            branch (str): repository branch. Defaults to '' (current repository branch)

        Returns:
            str: success message in html
        """
        branch = branch if branch else self.branch
        try: 
            status: dict = self.handler.create_file(
                path=path, 
                message=f"Add {PurePosixPath(path).name} at MarkHub", 
                content=content, 
                branch=branch
            )
            return format_html(
                'File {} was successfully created with commit <a href="{}" target="_blank">{}</a>.',
                path,
                status["commit"].html_url,
                status["commit"].sha[:7]
            )
        except UnknownObjectException as e:
            log_error_with_404(f"File not created - {e}")
    
    def delete_file(self, path: str, branch: str = '') -> str:
        """Delete a file in the repository if success otherwise raise 404 exception

        Args:
            path (str): path to the deleted file
            branch (str): repository branch. Defaults to '' (current repository branch)

        Returns:
            str: success message in html
        """
        branch = branch if branch else self.branch
        try:
            contents = self.handler.get_contents(path, ref=branch)
            status: dict = self.handler.delete_file(
                contents.path, 
                f"Delete {PurePosixPath(path).name} at MarkHub", 
                contents.sha, 
                branch
            )
            return format_html(
                    'File {} was successfully deleted with commit <a href="{}" target="_blank">{}</a>.',
                    path,
                    status["commit"].html_url,
                    status["commit"].sha[:7]
            )
        except UnknownObjectException as e:
            log_error_with_404(f"Path not found - {e}")

    def get_contents(self, path: str, branch: str) -> ContentFile:
        """Get contents for path, otherwise raise Http404 exception

        Args:
            path (str): repository item path
            branch (str): repository branch

        Returns:
            ContentFile: repository item contents
        """
        if not branch:
            branch = self.branch
        try:
            return self.handler.get_contents(path, ref=branch)
        except UnknownObjectException as e:
            log_error_with_404(f"Path not found - {e}")
    
    def get_context(self, path: str, extra: Dict) -> Dict:
        """Get template context dict with repository data

        Args:
            path: repository item path
            extra: dictionary to extend result
        
        Returns:
            Dict: template context
        """
        context = {
            'repo': self.name,
            'private': self.handler.private,
            'branch': self.branch,
            'branches': self.branches,
            'path': path,
        }
        if path:
            context['path_parts'] = self.get_path_parts(path)
            context['parent_path'] = str(Path(path).parent)
        context.update(extra)
        return context

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
    
    @property
    def name(self) -> Optional[str]:
        """Returns repository name"""
        if self.handler:
            return self.handler.name
    
    def publish_file(self, request: HttpRequest, path: str) -> str:
        """Save file in PrivatePublish model for sharing

        Args:
            request (HttpRequest): _Django request instance_
            path (str): _File path_

        Returns:
            str: _description_
        """
        content = repository.get_contents(path, self.branch).decoded_content.decode('UTF-8')
        published_file = PrivatePublish(
            user=self.user,
            repo=self.repo,
            path=self.name,
            content=content,
            owner=request.user
        )
        published_file.save()
        return format_html(
            'File {%1} was successfully published with the link <a href="{%2}">{%2}</a>',
            path,
            "{% url 'share' user_name repo branch path %}"
        )

    def save_current_branch(self, request: HttpRequest, branch: str) -> None:
        """ Save repository in session
        
        Args:
            request: Django request object
            branch: branch name
        """
        self.branch = branch
        request.session[f'{self.handler.name}__current_branch'] = self.branch
    
    def update_file(self, path: str, updated_content: str, branch: str = '') -> str:
        """Update a file in the repository if success otherwise raise 404 exception

        Args:
            path (str): path to the updated file
            updated_content (str): updated content
            branch (str): repository branch. Defaults to '' (current repository branch)

        Returns:
            str: success message in html
        """
        branch = branch if branch else self.branch
        try:
            contents = self.get_contents(path, branch)
            status: dict = self.handler.update_file(
                path=path, 
                message=f"Update {PurePosixPath(path).name} at MarkHub", 
                content=updated_content,
                sha=contents.sha,
                branch=branch)
            return format_html(
                'File {} was successfully updated with commit <a href="{}" target="_blank">{}</a>.',
                path,
                status["commit"].html_url,
                status["commit"].sha[:7]
            )
        except UnknownObjectException as e:
            log_error_with_404(f"File not updated - {e}")

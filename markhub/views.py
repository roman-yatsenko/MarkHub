from typing import Any, Dict, Union, List
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User

from pathlib import Path
from github import Github

def get_github_handler(user: User) -> Union[Github, None]:
    """ Get github handler for user

    Args:
        user: User from request

    Returns:
        Github object for user if it has a token, otherwise None
    """
    
    social_account = user.socialaccount_set
    if social_account.exists() and social_account.first().provider == 'github':
        social_login = social_account.first().socialtoken_set
        if social_login.exists():
            return Github(social_login.first().token)    

def get_path_parts(path: str) -> Dict:
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


class HomeView(TemplateView):
    """ Home page view """
    
    template_name = 'home.html'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data for home page view"""

        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            g = get_github_handler(user)
            if g:
                context['repos'] = [repo.name for repo in g.get_user().get_repos()]
        return context


class RepoView(LoginRequiredMixin, TemplateView):
    """ Repository view """
    
    template_name = 'repo.html'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data for repository view"""

        context = super().get_context_data(**kwargs)
        user = self.request.user
        path = context.get('path')
        g: Github = get_github_handler(user)
        if g:
            repo = g.get_repo(f"{user.username}/{context['repo']}")
            if not path:
                contents = repo.get_contents('')
            else:
                contents = repo.get_dir_contents(path)
                context['path_parts'] = get_path_parts(path)
            if len(contents) > 0:
                context['repo_contents'] = contents
            elif contents:
                context['repo_contents'] = [contents]
        return context


class FileView(LoginRequiredMixin, TemplateView):
    """Repository file view"""

    template_name = 'file.html'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data for file view"""

        context = super().get_context_data(**kwargs)
        user = self.request.user
        path = context.get('path')
        g: Github = get_github_handler(user)
        if g:
            repo = g.get_repo(f"{user.username}/{context['repo']}")
            context['contents'] = repo.get_contents(path).decoded_content.decode('UTF-8')
        return context

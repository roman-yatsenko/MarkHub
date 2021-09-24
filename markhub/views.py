from typing import Any, Dict, Union
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User

from github import Github

def get_github_handler(user: User) -> Union[Github, None]:
    """Get github handler for user

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


class HomeView(TemplateView):
    """Home page view"""
    
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
    """Repository page view"""
    
    template_name = 'repo.html'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data for home page view"""

        context = super().get_context_data(**kwargs)
        g: Github = get_github_handler(self.request.user)
        if g:
            print(context['repo'])
            repo = g.get_repo(context['repo'])
            contents = repo.get_contents('')
            context['repo_files'] = []
            while contents:
                context['repo_files'].append(contents.pop(0).path)
        return context

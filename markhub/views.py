from typing import Any, Dict
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from github import Github

def get_github_handler(user):
    social_account = user.socialaccount_set
    if social_account.exists() and social_account.first().provider == 'github':
        social_login = social_account.first().socialtoken_set
        if social_login.exists():
            return Github(social_login.first().token)    


class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            g = get_github_handler(user)
            if g:
                context['repos'] = [repo.name for repo in g.get_user().get_repos()]
        return context


class RepoView(LoginRequiredMixin, TemplateView):
    template_name = 'repo.html'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        return context

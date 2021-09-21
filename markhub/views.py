from django.views.generic import TemplateView

from github import Github


class Home(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            social_account = user.socialaccount_set
            if social_account.exists() and social_account.first().provider == 'github':
                social_login = social_account.first().socialtoken_set
                if social_login.exists():
                    g = Github(social_login.first().token)
                    context['repos'] = [repo.name for repo in g.get_user().get_repos()]
        return context

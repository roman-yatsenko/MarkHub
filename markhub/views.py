from django.views.generic import TemplateView


class Home(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        social_account = self.request.user.socialaccount_set
        if social_account.exists() and social_account.first().provider == 'github':
            social_login = social_account.first().socialtoken_set
            if social_login.exists():
                print(social_login.first().token)
        return context

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse


class PrivatePublish(models.Model):
    """Published files from private repos
    
        Add 'private_repos' permission to work with private repositories
    """

    # 39, 100, 4096 - git's max lengthes
    user = models.CharField(max_length=39, verbose_name='Username')
    repo = models.TextField(max_length=100, verbose_name='Repository name')
    branch = models.TextField(max_length=255, verbose_name='Branch name', default='master')
    path = models.TextField(max_length=4096, verbose_name='File path')
    published = models.DateTimeField(auto_now_add=True, verbose_name='Publication time')
    content = models.TextField(null=True, blank=True, verbose_name='Markdown content')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="User - Repository owner")

    class Meta:
        get_latest_by = 'published'
        index_together = ['user', 'repo', 'branch', 'path']
        unique_together = ['user', 'repo', 'branch', 'path']
        ordering = ['user', 'repo', 'branch', 'path']
        verbose_name = 'Published file'
        verbose_name_plural = 'Published files'
        permissions = (
            ('private_repos', 'Work with private repositories'),
        )

    def __str__(self) -> str:
        """String instance representation

        Returns:
            _str_: _string instance representation_
        """
        return '/'.join([self.user, self.repo, self.branch, self.path])
    
    def get_absolute_url(self):
        """Get absolute url for the published file

        Returns:
            _str_: _Published file absolute url_
        """
        return reverse('share', kwargs={
            'user': self.user,
            'repo': self.repo,
            'path': self.path
        })
from pathlib import Path, PurePosixPath
from typing import Any, Dict
from urllib.error import HTTPError
from urllib.request import urlopen

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import FileResponse, Http404
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import redirect, render
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView
from github import GithubException, UnknownObjectException
from markdown import Markdown

from .forms import NewFileForm, UpdateFileForm
from .models import PrivatePublish
from .services.github_repository import GitHubRepository, get_github_handler
from .settings import (MARTOR_MARKDOWN_EXTENSION_CONFIGS,
                       MARTOR_MARKDOWN_EXTENSIONS, log_error_with_404, logger)


@login_required
def delete_file_ctr(request: HttpRequest, repo: str, path: str) -> HttpResponse:
    """ Delete File Controller
    
    Args:
        request: request from form
        repo: repository name
        path: repository file path

    Returns:
        rendered page
    """
    if repository := GitHubRepository(request, repo):
        messages.success(request, repository.delete_file(path))
        if path:
            path_object = PurePosixPath(path)
            parent_path = '' if str(path_object.parent) == '.' else str(path_object.parent)
            return redirect('repo', repo=repo, branch=repository.branch, path=parent_path)
        else:
            return redirect('repo', repo=repo)
    else:
        raise Http404("Repository not found")


def get_webmanifest(request: HttpRequest) -> FileResponse:
    """ _Get webmanifest file in the DEBUG mode_

    Args:
        request (HttpRequest): _request object_

    Returns:
        FileResponse: _webmanifest as FileResponse_
    """
    return FileResponse(open('manifest.webmanifest', 'rb'))


@login_required
def new_file_ctr(request: HttpRequest, repo: str, path: str = '') -> HttpResponse:
    """ New File Controller
    
    Args:
        request: request from form
        repo: repository name
        path: repository path (empty str for root) for the new file

    Returns:
        rendered page
    """
    if repository := GitHubRepository(request, repo):
        context = repository.get_context(path, extra={
            'title': 'New file in',
            'disable_branch_selector': True,
        })
        if request.method == 'POST':
            new_file_form = NewFileForm(request.POST)
            if new_file_form.is_valid():
                newfile_path: str = f'{path + "/" if path else ""}{new_file_form.cleaned_data["filename"]}'
                messages.success(request, repository.create_file(
                                            path=newfile_path, 
                                            content=new_file_form.cleaned_data['content']
                ))
                return redirect('file', repo=repo, branch=repository.branch, path=newfile_path)
        else:
            new_file_form = NewFileForm()
        context['form'] = new_file_form
        return render(request, 'edit_file.html', context)
    else:
        raise Http404("Repository not found")


@login_required
def publish_file_ctr(request: HttpRequest, user: str, repo: str, branch: str, path: str) -> HttpResponse:
    """Publish file from private repository

    Args:
        request (HttpRequest): _Django request instance_
        user (str): _user name_
        repo (str): _repository name_
        branch (str): _branch name_
        path (str): _file path_

    Raises:
        Http404: _Repository not found_

    Returns:
        HttpResponse: redirect to share page
    """
    if repository := GitHubRepository(request, repo):
        content = repository.get_contents(path, repository.branch).decoded_content.decode('UTF-8')
        published_file = PrivatePublish(
            user=user,
            repo=repo,
            path=path,
            content=content,
            owner=request.user
        )
        published_file.save()
        return redirect('share', user=user, repo=repo, branch=branch, path=path)
    else:
        raise Http404("Repository not found")

@login_required
def update_file_ctr(request: HttpRequest, repo: str, path: str) -> HttpResponse:
    """ Update File Controller
    
    Args:
        request: request from form
        repo: repository name
        path: repository file path

    Returns:
        rendered page
    """
    if repository := GitHubRepository(request, repo):
        context = repository.get_context(path, extra={
            'update': True,
            'title': 'Update file',
            'disable_branch_selector': True,
        })
        if request.method == 'POST':
            update_file_form = UpdateFileForm(request.POST)
            if update_file_form.is_valid():
                messages.success(request, repository.update_file(
                                            path, 
                                            updated_content=update_file_form.cleaned_data['content']
                ))
                return redirect('file', repo=repo, branch=repository.branch, path=path)
        else:
            update_file_form = UpdateFileForm(data={
                'filename': path,
                'content': repository.get_contents(path, repository.branch).decoded_content.decode('UTF-8'),
            })
        context['form'] = update_file_form
        return render(request, 'edit_file.html', context)
    else:
        raise Http404("Repository not found")


class HomeView(TemplateView):
    """ Home page view """
    template_name = 'home.html'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data for home page view"""
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated and (g := get_github_handler(user)):
            context['repos'] = [
                (repo.name, repo.created_at, repo.private) 
                for repo in g.get_user().get_repos() 
                if user.username == repo.owner.login 
                and (not repo.private or user.has_perm('markhub.private_repos'))
            ]
        return context


class BaseRepoView(LoginRequiredMixin, TemplateView):
    """ Base Repository view """

    def setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
        super().setup(request, *args, **kwargs)
        self.user_name = request.user.username
        self.repo = GitHubRepository(request, kwargs['repo'])
        self.path = kwargs.get('path', '')
        self.branch = kwargs.get('branch', self.repo.branch)
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data for repository view"""
        context = super().get_context_data(**kwargs)
        context.update(self.repo.get_context(self.path, extra={
            'user_name': self.user_name,
        }))
        return context

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """POST request handler to change current branch"""
        if request.POST.get('selected_branch', False):
            self.branch = request.POST.get('selected_branch')
            self.repo.save_current_branch(request, self.branch)
        return self.get(request, *args, **kwargs)


class RepoView(BaseRepoView):
    """ Repository view """
    template_name = 'repo.html'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data for repository view"""
        context = super().get_context_data(**kwargs)
        if not self.path:
            contents = self.repo.handler.get_contents('', self.branch)
        else:
            try:
                contents = self.repo.handler.get_dir_contents(self.path, self.branch)
            except (UnknownObjectException, GithubException) as e:
                logger.error(f"Path not found - {e}")
                raise Http404(f"Path not found - {e}")
        if isinstance(contents, list):
            context['repo_contents'] = contents
            contents.sort(
                key=lambda item: item.type + item.name
            )
        elif contents:
            context['repo_contents'] = [contents]
        context['html_url'] = f'{self.repo.handler.html_url}/tree/{self.branch}/{self.path if self.path else ""}'
        return context


class FileView(BaseRepoView):
    """Repository file view"""
    template_name = 'file.html'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data for file view"""
        context = super().get_context_data(**kwargs)
        try:
            contents = self.repo.handler.get_contents(self.path, context['branch'])
            context['contents'] = contents.decoded_content.decode('UTF-8')
        except GithubException as e:
            logger.error(f"File not found - {e}")
            raise Http404(
                "The '{user_name}/{repo}' repository doesn't contain the '{path}' path in '{branch}'.".format(
                    **context
                )
            )
        except UnicodeDecodeError as e:
            context['decode_error'] = True
            context['contents'] = f"Unicode decode error during openning {self.path}"
            logger.error(context['contents'])
        context['html_url'] = contents.html_url
        return context


class ShareView(TemplateView):
    """ Share page view """
    template_name = 'share.html'
    GITHUB_USERCONTENT_TEMPLATE = 'https://raw.githubusercontent.com/{user}/{repo}/{branch}/{path}'
    GITHUB_URL_TEMPLATE = 'https://github.com/{user}/{repo}//blob/{branch}/{path}'

    def _markdown(self) -> Markdown:
        """
        Rerurn the Markdown object with martor settings

        Returns:
            Markdown object
        """
        return Markdown(
            extensions=MARTOR_MARKDOWN_EXTENSIONS,
            extension_configs=MARTOR_MARKDOWN_EXTENSION_CONFIGS,
            output_format="html5",
        )
    
    def _render_file(self, context: dict) -> Markdown:
        """Render file from repository

        Args:
            context (dict): context dict with request parameters

        Returns:
            Markdown: Markdown instance with rendered file
        """
        pass

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data for share page view"""
        context = super().get_context_data(**kwargs)
        params = ('user', 'repo', 'branch', 'path')
        if all(x in context for x in params):
            try:
                usercontent_url = ShareView.GITHUB_USERCONTENT_TEMPLATE.format(**context)
                markdown = self._markdown()
                context['contents'] = mark_safe(markdown.convert(urlopen(usercontent_url).read().decode('utf-8')))
                context['toc'] = mark_safe(markdown.toc)
            except HTTPError as e:
                error_message = f"Url not found - {usercontent_url}"
                logger.error(error_message)
                raise Http404(error_message)
            except UnicodeDecodeError as e:
                context['decode_error'] = True
                context['contents'] = f"Unicode decode error during openning {context['path']}"
                logger.error(context['contents'])
            finally:
                context['html_url'] = ShareView.GITHUB_URL_TEMPLATE.format(**context)
        return context

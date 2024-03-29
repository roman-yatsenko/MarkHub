from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Optional, Tuple
from urllib.error import HTTPError
from urllib.request import urlopen

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView
from github import GithubException, UnknownObjectException
from loguru import logger

from .forms import NewFileForm, UpdateFileForm
from .models import PrivatePublish
from .services.bootstrap_icons import FILETYPE_EXTENSIONS
from .services.github_repository import (GitHubRepository, get_github_handler,
                                         get_repository_or_error)
from .services.markdown_render import markdownify                                         
from .settings import (log_error_with_404, logger)


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
    repository = get_repository_or_error(request, repo)
    messages.success(request, repository.delete_file(path))
    if path:
        path_object = PurePosixPath(path)
        parent_path = '' if str(path_object.parent) == '.' else str(path_object.parent)
        return redirect('repo', repo=repo, branch=repository.branch, path=parent_path)
    else:
        return redirect('repo', repo=repo)


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
    repository = get_repository_or_error(request, repo)
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


@login_required
def publish_file_ctr(request: HttpRequest, username: str, repo: str, branch: str, path: str) -> HttpResponse:
    """Publish file from private repository

    Args:
        request (HttpRequest): Django request instance
        username (str): user name
        repo (str): repository name
        branch (str): branch name
        path (str): file path

    Raises:
        Http404: _Repository not found_

    Returns:
        HttpResponse: redirect to share page
    """
    repository = get_repository_or_error(request, repo)
    context = repository.get_context(path, extra={
        'content': repository.get_contents(path, branch).decoded_content.decode('UTF-8'),
        'owner': request.user,
    })
    PrivatePublish.publish_file(context)
    messages.success(request, format_html(
        'File {0} was successfully published with the link <a href="{1}" target="_blank">{1}</a>',
        path, request.build_absolute_uri(reverse('share', args=[username, repo, branch, path]))
    ))
    return redirect('share', username=username, repo=repo, branch=branch, path=path)


@login_required
def unpublish_file_ctr(request: HttpRequest, username: str, repo: str, branch: str, path: str) -> HttpResponse:
    """Unpublish file from private repository

    Args:
        request (HttpRequest): _Django request instance_
        username (str): user name
        repo (str): repository name
        branch (str): branch name
        path (str): file path

    Raises:
        Http404: _Repository not found_

    Returns:
        HttpResponse: redirect to file page with result message
    """
    repository = get_repository_or_error(request, repo)
    try:
        published_file = PrivatePublish.lookup_published_file(locals())
        published_file.delete()
        messages.success(request, f'File {path} was successfully unpublished')
    except:
        messages.warning(request, f'Error was happened during unpublishing {path}')
    finally:
        return redirect('file', repo=repo, branch=branch, path=path)


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
    repository = get_repository_or_error(request, repo)
    context = repository.get_context(path, extra={
        'update': True,
        'title': 'Update file',
        'disable_branch_selector': True,
    })
    context['published'] = bool(context['private'] and PrivatePublish.lookup_published_file(context))
    if request.method == 'POST':
        update_file_form = UpdateFileForm(request.POST)
        if update_file_form.is_valid():
            updated_content = update_file_form.cleaned_data['content']
            if status := repository.update_file(path, updated_content):
                if update_file_form.cleaned_data['republish']:
                    context['content'] = updated_content
                    context['owner'] = request.user
                    PrivatePublish.publish_file(context)
                messages.success(request, status)
            return redirect('file', repo=repo, branch=repository.branch, path=path)
    else:
        update_file_form = UpdateFileForm(data={
            'filename': path,
            'content': repository.get_contents(path, repository.branch).decoded_content.decode('UTF-8'),
        })
    context['form'] = update_file_form
    return render(request, 'edit_file.html', context)


class HomeView(TemplateView):
    """ Home page view """
    template_name = 'home.html'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data for home page view"""
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated and (g := get_github_handler(user)):
            context['repos'] = sorted([
                                    (repo.name, repo.pushed_at, repo.private) 
                                    for repo in g.get_user().get_repos() 
                                    if user.username == repo.owner.login 
                                    and (not repo.private or user.has_perm('markhub.private_repos'))
                                ], key=lambda item: item[1], reverse=True)
        return context


class BaseRepoView(LoginRequiredMixin, TemplateView):
    """ Base Repository view """

    def setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
        super().setup(request, *args, **kwargs)
        if request.user.username:
            self.username = request.user.username
            self.repo = get_repository_or_error(request, kwargs['repo'])
            self.path = kwargs.get('path', '')
            self.branch = kwargs.get('branch', self.repo.branch)
        else:
            raise PermissionDenied
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data for repository view"""
        context = super().get_context_data(**kwargs)
        context.update(self.repo.get_context(self.path, extra={
            'username': self.username,
        }))
        return context

    def post(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """POST request handler to change current branch"""
        if request.POST.get('selected_branch', False):
            self.branch = request.POST.get('selected_branch')
            self.repo.save_current_branch(request, self.branch)
        return self.get(request, *args, **kwargs)

    def _add_file_contents(self, context: dict, path: str) -> None:
        """Add file contents to context

        Args:
            context (dict): template context
            path (str): file path in repository

        Raises:
            Http404: if file not found in repository
        """
        try:
            contents = self.repo.get_contents(path, context['branch'])
            context['contents'] = contents.decoded_content.decode('UTF-8')
            context['html_url'] = contents.html_url
            if context.get('private'):
                context['published'] = PrivatePublish.lookup_published_file(context)
        except GithubException as e:
            logger.error(f"File not found - {e}")
            raise Http404(
                "The '{username}/{repo}' repository doesn't contain the '{path}' path in '{branch}'.".format(
                    **context
                )
            )
        except UnicodeDecodeError as e:
            context['decode_error'] = True
            context['contents'] = f"Unicode decode error during openning {self.path}"
            logger.error(context['contents'])

    def _add_file_last_update(self, context: dict, path: str) -> Optional[datetime]:
        """Add file last update datetime to context

        Args:
            context (dict): template context
            path (str): file path in repository

        Raises:
            Http404: if file not found in repository
        """
        try:
            if path and (last_update := self.repo.get_file_last_update(path, context['branch'])):
                context['last_update'] = last_update
        except GithubException as e:
            logger.error(f"File not found - {e}")
            raise Http404(
                "The '{username}/{repo}' repository doesn't contain the '{path}' path in '{branch}'.".format(
                    **context
                )
            )
        

class RepoView(BaseRepoView):
    """ Repository view """
    template_name = 'repo.html'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data for repository view"""
        context = super().get_context_data(**kwargs)
        context['last_update'] = self.repo.handler.get_commit(self.branch).commit.committer.date
        if not self.path:
            contents = self.repo.handler.get_contents('', self.branch)
            readme_file = sorted([
                item.name
                for item in contents
                if item.type != 'dir' and item.name.lower() in ('readme.md', 'index.md')
            ], key=lambda item: item.lower(), reverse=True)
            if readme_file:
                context['readme_file'] = readme_file[0]
                self._add_file_contents(context, context['readme_file'])
        else:
            try:
                contents = self.repo.handler.get_dir_contents(self.path, self.branch)
            except (UnknownObjectException, GithubException) as e:
                log_error_with_404(f"Path not found - {e}")
        if isinstance(contents, list):
            contents.sort(key=lambda item: item.type + item.name)
            context['repo_contents'] = contents
        elif contents:
            context['repo_contents'] = [contents]
        for content in contents:
            extension = Path(content.name).suffix[1:]
            content.icon = f'bi-filetype-{extension}' if extension in FILETYPE_EXTENSIONS else 'bi-file-earmark'
        context['html_url'] = f'{self.repo.handler.html_url}/tree/{self.branch}/{self.path if self.path else ""}'
        return context


class FileView(BaseRepoView):
    """Repository file view"""
    template_name = 'file.html'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data for file view"""
        context = super().get_context_data(**kwargs)
        self._add_file_contents(context, self.path)
        self._add_file_last_update(context, self.path)
        return context

class ShareView(TemplateView):
    """ Share page view """
    template_name = 'share.html'
    GITHUB_USERCONTENT_TEMPLATE = 'https://raw.githubusercontent.com/{username}/{repo}/{branch}/{path}'
    GITHUB_URL_TEMPLATE = 'https://github.com/{username}/{repo}//blob/{branch}/{path}'

    def _add_file_content_and_toc(self, context: dict) -> Tuple[str, str]:
        """Add file content & toc from PrivatePublish or public repository to context with caching

        Args:
            context (dict): context dict with request parameters
        """
        content = ''
        if shared_file := PrivatePublish.lookup_published_file(context):
            context['contents'] = mark_safe(shared_file.content)
            context['toc'] = mark_safe(shared_file.toc)
            context['private'] = True
        else:
            usercontent_url = ShareView.GITHUB_USERCONTENT_TEMPLATE.format(**context)
            if cache.has_key(usercontent_url):
                context['contents'], context['toc'] = cache.get(usercontent_url)    
            else: 
                try:
                    content = urlopen(usercontent_url).read().decode('utf-8')
                except HTTPError:
                    log_error_with_404(f"Url not found - {usercontent_url}")
                except UnicodeDecodeError:
                    context['decode_error'] = True
                    context['contents'] = f"Unicode decode error during openning {context['path']}"
                    logger.error(context['contents'])
                context['contents'], context['toc'] = (mark_safe(x) for x in markdownify(content))
                if content:
                    cache.add(usercontent_url, (context['contents'], context['toc']))
            context['html_url'] = ShareView.GITHUB_URL_TEMPLATE.format(**context)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data for share page view"""
        context = super().get_context_data(**kwargs)
        if all(x in context for x in ('username', 'repo', 'branch', 'path')):
            self._add_file_content_and_toc(context)
        return context

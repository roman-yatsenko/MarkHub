from pathlib import Path, PurePosixPath
from typing import Any, Dict
from urllib.request import urlopen
from urllib.error import HTTPError

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render, redirect
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.views.generic import TemplateView

from github import GithubException, UnknownObjectException
from markdown import Markdown

from .forms import NewFileForm, UpdateFileForm
from .services.github_repository import GitHubRepository, get_github_handler
from .settings import (
    MARTOR_MARKDOWN_EXTENSIONS,
    MARTOR_MARKDOWN_EXTENSION_CONFIGS,
    logger,
)

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
    if request.method == 'POST':
        new_file_form = NewFileForm(request.POST)
        if new_file_form.is_valid() and (repository := GitHubRepository(request, repo)):
            filename: str = new_file_form.cleaned_data["filename"]
            newfile_path: str = f'{path + "/" if path else ""}{filename}' 
            status: dict = repository.handler.create_file(
                path=newfile_path, 
                message=f"Add {filename} at MarkHub", 
                content=new_file_form.cleaned_data['content'], 
                branch=repository.branch)
            message: str = format_html(
                'File {} was successfully created with commit <a href="{}" target="_blank">{}</a>.',
                newfile_path,
                status["commit"].html_url,
                status["commit"].sha[:7]
            )
            messages.success(request, message)
            return redirect('file', repo=repo, branch=repository.branch, path=newfile_path)
    else:
        new_file_form = NewFileForm()
    context = {
        'form': new_file_form,
        'title': 'New file in'
    }
    return render(request, 'edit_file.html', context)
    

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
        context = {
            'update': True,
            'title': 'Update file',
            'repo': repository.name,
            'branch': repository.branch,
            'path': path,
        }
        try:
            contents = repository.handler.get_contents(path, ref=repository.branch)
        except UnknownObjectException as e:
                logger.error(f"Path not found - {e}")
                raise Http404(f"Path not found - {e}")
        if request.method == 'POST':
            update_file_form = UpdateFileForm(request.POST)
            if update_file_form.is_valid():
                path_object = PurePosixPath(path)
                status: dict = repository.handler.update_file(
                    path=path, 
                    message=f"Update {path_object.name} at MarkHub", 
                    content=update_file_form.cleaned_data['content'],
                    sha=contents.sha,
                    branch=repository.branch)
                message: str = format_html(
                    'File {} was successfully updated with commit <a href="{}" target="_blank">{}</a>.',
                    path,
                    status["commit"].html_url,
                    status["commit"].sha[:7]
                )
                messages.success(request, message)
                return redirect('file', repo=repo, branch=repository.branch, path=path)
        else:
            data = {
                'filename': path,
                'content': contents.decoded_content.decode('UTF-8'),
            }
            update_file_form = UpdateFileForm(data)
        context['form'] = update_file_form
        return render(request, 'edit_file.html', context)
    else:
        raise Http404("Repository not found")

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
        path_object = PurePosixPath(path)
        parent_path = '' if str(path_object.parent) == '.' else str(path_object.parent)
        try:
            contents = repository.handler.get_contents(path, ref=repository.branch)
            status: dict = repository.handler.delete_file(
                contents.path, 
                f"Delete {path_object.name} at MarkHub", 
                contents.sha, 
                branch=repository.branch
            )
            message: str = format_html(
                    'File {} was successfully deleted with commit <a href="{}" target="_blank">{}</a>.',
                    path,
                    status["commit"].html_url,
                    status["commit"].sha[:7]
                )
            messages.success(request, message)
        except UnknownObjectException as e:
            logger.error(f"Path not found - {e}")
            raise Http404(f"Path not found - {e}")
        if path:
            return redirect('repo', repo=repo, branch=repository.branch, path=parent_path)
        else:
            return redirect('repo', repo=repo)
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
                (repo.name, repo.created_at) 
                for repo in g.get_user().get_repos() 
                if user.username == repo.owner.login
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
        context['user_name'] = self.user_name
        context['repo'] = self.repo.name
        context['branch'] = self.branch
        context['branches'] = self.repo.branches
        context['path'] = self.path
        if self.path:
            context['path_parts'] = self.repo.get_path_parts(self.path)
            context['parent_path'] = str(Path(self.path).parent)
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
    
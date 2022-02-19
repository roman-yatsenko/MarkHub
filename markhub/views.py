from typing import Any, Dict
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import Http404
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.generic import TemplateView

from pathlib import PurePosixPath
from github import GithubException, UnknownObjectException

from .forms import NewFileForm, UpdateFileForm
from .services.github_repository import GitHubRepository, get_github_handler

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
        if new_file_form.is_valid():
            repository = GitHubRepository(request, repo)
            if repository:
                newfile_path = f'{path + "/" if path else ""}{new_file_form.cleaned_data["filename"]}' 
                repository.handler.create_file(
                    path=newfile_path, 
                    message=f"Add {new_file_form.cleaned_data['filename']} at MarkHub", 
                    content=new_file_form.cleaned_data['content'], 
                    branch=repository.branch)
                request.method = 'GET'
                if path:
                    return redirect('repo', repo=repo, branch=repository.branch, path=path)
                else:
                    return redirect('repo', repo=repo)
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
    repository = GitHubRepository(request, repo)
    if repository:
        context = {
            'update': True,
            'title': 'Update file'
        }
        try:
            contents = repository.handler.get_contents(path, ref=repository.branch)
        except UnknownObjectException as e:
                raise Http404(f"Path not found - {e}")
        if request.method == 'POST':
            update_file_form = UpdateFileForm(request.POST)
            if update_file_form.is_valid():
                path_object = PurePosixPath(path)
                parent_path = '' if str(path_object.parent) == '.' else str(path_object.parent)
                repository.handler.update_file(
                    path=path, 
                    message=f"Update {path_object.name} at MarkHub", 
                    content=update_file_form.cleaned_data['content'],
                    sha=contents.sha,
                    branch=repository.branch)
                if path:
                    return redirect('repo', repo=repo, branch=repository.branch, path=parent_path)
                else:
                    return redirect('repo', repo=repo)
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
    repository = GitHubRepository(request, repo)
    if repository:
        path_object = PurePosixPath(path)
        parent_path = '' if str(path_object.parent) == '.' else str(path_object.parent)
        try:
            contents = repository.handler.get_contents(path, ref=repository.branch)
            repository.handler.delete_file(
                contents.path, 
                f"Delete {path_object.name} at MarkHub", 
                contents.sha, 
                branch=repository.branch
            )
        except UnknownObjectException as e:
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
        if user.is_authenticated:
            g = get_github_handler(user)
            if g:
                context['repos'] = [repo.name for repo in g.get_user().get_repos()]
        return context


class BaseRepoView(LoginRequiredMixin, TemplateView):
    """ Base Repository view """

    def setup(self, request: HttpRequest, *args: Any, **kwargs: Any) -> None:
        super().setup(request, *args, **kwargs)
        self.repo = GitHubRepository(request, kwargs['repo'])
        self.path = kwargs.get('path', '')
        self.branch = kwargs.get('branch', self.repo.branch)
    
    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data for repository view"""
        context = super().get_context_data(**kwargs)
        context['repo'] = self.repo.name
        context['branch'] = self.branch
        context['branches'] = self.repo.branches
        return context

    def post(self, request: HttpRequest, *args: str, **kwargs: Any) -> HttpResponse:
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
            context['path'] = ''
        else:
            try:
                contents = self.repo.handler.get_dir_contents(self.path, self.branch)
            except UnknownObjectException as e:
                raise Http404(f"Path not found - {e}")
            except GithubException as e:
                raise Http404(f"Path not found - {e}")
            context['path_parts'] = self.repo.get_path_parts(self.path)
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
        context['path_parts'] = self.repo.get_path_parts(self.path)
        try:
            contents = self.repo.handler.get_contents(self.path, context['branch'])
            context['contents'] = contents.decoded_content.decode('UTF-8')
        except GithubException as e:
            raise Http404(f"File not found - {e}")
        except UnicodeDecodeError as e:
            context['decode_error'] = True
            context['contents'] = f"Unicode decode error during openning {self.path}"
        context['html_url'] = contents.html_url
        return context

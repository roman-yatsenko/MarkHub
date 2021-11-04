from typing import Any, Dict, Union
from django.http.request import HttpRequest
from django.http.response import HttpResponse
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import Http404

from pathlib import Path, PurePosixPath
from github import Github
from github.ContentFile import ContentFile
from github.Repository import Repository

from .forms import NewFileForm, UpdateFileForm

def get_github_handler(user: User) -> Union[Github, None]:
    """ Get github handler for user

    Args:
        user: Django User

    Returns:
        Github object for user if it has a token, otherwise None
    """
    
    social_account = user.socialaccount_set
    if social_account.exists() and social_account.first().provider == 'github':
        social_login = social_account.first().socialtoken_set
        if social_login.exists():
            return Github(social_login.first().token)    

def get_user_repo(user: User, repo: str) -> Union[Repository, None]:
    """ Get user repo
    
    Args: 
        user: Django User
        repo: Repository name

    Returns: 
        Repository object if it exists, otherwise None
    """
    g: Github = get_github_handler(user)
    if g:
        repo = g.get_repo(f"{user.username}/{repo}")
        if repo:
            return repo

def get_session_repo(request: HttpRequest, repo: str) -> Union[Repository, None]:
    """ Get Repository object for repo from session or via GitHub request
    
    Args: 
        request: Django request object
        repo: Repository name

    Returns: 
        Repository object cached in session or via GitHub request, otherwise None
    """

    if repo in request.session :
        return request.session[repo]
    else:
        user = request.user
        g: Github = get_github_handler(user)
        if g:
            repository = g.get_repo(f"{user.username}/{repo}")
            if repository:
                request.session[repo] = repository
                return repository

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
            repository = get_session_repo(request, repo)
            if repository:
                newfile_path = f'{path + "/" if path else ""}{new_file_form.cleaned_data["filename"]}' 
                repository.create_file(
                    path=newfile_path, 
                    message=f"Add {new_file_form.cleaned_data['filename']} at MarkHub", 
                    content=new_file_form.cleaned_data['content'], 
                    branch=repository.default_branch)
                request.method = 'GET'
                return RepoView.as_view()(request, repo=repo, path=path)
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

    repository = get_session_repo(request, repo)
    if repository:
        context = {
            'update': True,
            'title': 'Update file'
        }
        contents = repository.get_contents(path)
        if request.method == 'POST':
            update_file_form = UpdateFileForm(request.POST)
            if update_file_form.is_valid():
                path_object = PurePosixPath(path)
                parent_path = '' if str(path_object.parent) == '.' else str(path_object.parent)
                repository.update_file(
                    path=path, 
                    message=f"Update {path_object.name} at MarkHub", 
                    content=update_file_form.cleaned_data['content'],
                    sha=contents.sha)
                request.method = 'GET'
                return RepoView.as_view()(request, repo=repo, path=parent_path)
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

    repository = get_session_repo(request, repo)
    if repository:
        path_object = PurePosixPath(path)
        parent_path = '' if str(path_object.parent) == '.' else str(path_object.parent)
        contents = repository.get_contents(path)
        repository.delete_file(contents.path, f"Delete {path_object.name} at MarkHub", contents.sha)
        return RepoView.as_view()(request, repo=repo, path=parent_path)
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


class RepoView(LoginRequiredMixin, TemplateView):
    """ Repository view """
    
    template_name = 'repo.html'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data for repository view"""

        context = super().get_context_data(**kwargs)
        path = context.get('path')
        repo = get_session_repo(self.request, context['repo'])
        if repo:
            if not path:
                contents = repo.get_contents('')
                context['path'] = ''
            else:
                contents = repo.get_dir_contents(path)
                context['path_parts'] = get_path_parts(path)
            if isinstance(contents, list):
                context['repo_contents'] = contents
                contents.sort(
                    key=lambda item: item.type + item.name
                )
            elif contents:
                context['repo_contents'] = [contents]
            context['branch'] = repo.default_branch
            context['html_url'] = f'{repo.html_url}/tree/{repo.default_branch}/{path if path else ""}'
        return context


class FileView(LoginRequiredMixin, TemplateView):
    """Repository file view"""

    template_name = 'file.html'

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Get context data for file view"""

        context = super().get_context_data(**kwargs)
        path = context.get('path')
        repo = get_session_repo(self.request, context['repo'])
        if repo:
            context['path_parts'] = get_path_parts(path)
            context['branch'] = repo.default_branch
            contents = repo.get_contents(path)
            context['contents'] = contents.decoded_content.decode('UTF-8')
            context['html_url'] = contents.html_url
        return context

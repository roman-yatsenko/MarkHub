# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added

### Changed

### Deprecated

### Removed

### Fixed
- MathJax preview bug

### Security

## [0.3.2] - 2022-09-23
### Added
- sort repos on the homepage by last update
- history button for repo, repo path and file
- README.md or index.md rendering at the repo root

### Changed
- move New file button to the toolbar

## [0.3.1] - 2022-09-13
### Fixed
- private share bug for users with full name
- direct private repo access with no permission

## [0.3.0] - 2022-09-07
### Added
- toolbar to new and edit file pages
- PyMdown SaneHeaders Extension
- repository type on the Home page
- PrivatePublish model
- show private repos if you have private_repos permission
- repository type on the Home page
- PrivatePublish model
- private_repos permission to show private repos
- add publish_file_ctr and unpublish_file_ctr
- private files publishing
- Publish/Unpublish button for shared private files
- Republish checkbox in the edit page
- 403 page template

### Changed
- rename Share button to Publish for private repos
- refactor file actions in file-actions component
- Publish button icon
- refactor controllers with get_repository_or_404 in 

### Fixed
- error log
- 500 error for files from private repos without login
- user and username conflict in context

## [0.2.2] - 2022-07-27
### Added
- profile menu icon
- processing repository and anchor links in rendered markdown

### Changed
- update dependencies
- enlarge editor font size

### Security
- add SOCIALACCOUNT_LOGIN_ON_GET=True to django-allauth config

## [0.2.1] - 2022-07-18
### Fixed
- baseurl in new/update page

## [0.2.0] - 2022-07-15
### Added
- Successful messages for file operations
- Python-Markdown extensions
- PyMdown Extensions
- MathJax math rendering
- Pygments code highlightning
- Logging with Loguru
- Unauthorized view mode with toc navigation
- Enlarge editor field
- Back-to-top button
- Parent folder link
- Imgur image uploading
- 404 page
- favicon
- Bootstrap icons
- UI titles
- baseurl to templates
- meta tags
- Google Analytics
- favicon set
- webmanifest
- gunicorn
- Production secure policies
- markdown-link-attr-modifier extension

### Changed
- Home page description
- Settings stucture
- Context preparing in class views
- Refactor views with components
- Header, footer colors

### Removed
- Font Awesome

### Fixed
- Disable non-owner repo access
- New-file bug

## [0.1.0] - 2022-03-09
### Added
- GitHub authentication with [django-allauth](https://github.com/pennersr/django-allauth) 
- Base file and branch repository operations with [PyGithub](https://github.com/PyGithub/PyGithub)
- markdown editor with preview [Martor](https://github.com/agusmakmun/django-markdown-editor)
- user interface with [Bootstrap 5](https://getbootstrap.com)

[Unreleased]: https://github.com/roman-yatsenko/MarkHub/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/roman-yatsenko/MarkHub/releases/tag/v0.1.0

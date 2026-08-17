# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2026-08-16

### Changed

- `image_url` is now returned as a single string instead of a nested Street View object.
- Street View image URLs preserve the camera parameters returned by Maps and only use full-HD dimensions.
- `panoid` is kept internal and is no longer exposed in `PlaceResult`.
- Release validation now checks the workflow input, project metadata, lockfile, changelog, PyPI, tags, and GitHub releases together.
- GitHub releases use the matching changelog section as their release notes.

## [0.1.0] - 2026-08-15

### Added

- Google Maps search results with normalized addresses, coordinates, and Maps links.
- Street View panorama IDs and ready-to-fetch full-HD thumbnails.
- GitHub checks, security scanning, dependency updates, and PyPI release automation.

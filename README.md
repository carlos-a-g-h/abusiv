# ABUSIV

## What is this?

ABUSIV is a recursive downloader for websites that do static file serving with autoindexing

## Usage

```$ abusiv {BaseDir} {AType} {URL}```

- The **BaseDir** argument is the local directory where all the files/folders will be downloaded. THe base directory cannot match the program's directory
- The **AType** argument is the type of autoindex that is used by the website
- The **URL** argument is the starting URL, this URL cannot be a direct link from a file, it has to be a directory that leads to other files and/or directories

## Available Autoindex types

- apache2
- h5ai

## Changelog

### 2023-05-29

- Made some rewrites (said bye bye to some mutable shared states) and changed some names
- Added some logging: The log file is saved in the base directory and any download failures will be logged as errors
- The output directory for all the downloaded content will be the initial directory (the initial directory name is taken from the initial URL) inside the base directory instead of the base directory itself
- While downloading a file or a page, you can hit Ctrl+C to skip it. In the case of skipping a file, the partially downloaded file will be eliminated and logged as an error

### 2023-05-27

- Bugfixes and added some guardrails
- Added support for Apache2's default autoindex

### 2023-05-26

- First release

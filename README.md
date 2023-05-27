# ABUSIV

## What is this?

ABUSIV is a recursive downloader for websites that do static file serving with autoindexing

## Usage

```$ abusiv {BaseDir} {AType} {URL}```

- The **BaseDir** argument is the local directory where all the files/folders will be downloaded. THe base directory cannot match the program's directory
- The **AType** argument is the type of autoindex that is used by the website
- The **URL** argument is the starting URL, this URL cannot be a direct link from a file, it has to be a directory that leads to other files/directories

## Available Autoindex types

- h5ai
- apache2

## Changelog

### 2023-05-27

- Bugfixes and added some guardrails
- Added support for Apache2's default autoindex

### 2023-05-26

- First release

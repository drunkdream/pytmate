# pytmate

## 什么是tmate

[tmate](https://tmate.io/)是一款可以用于终端分享的工具，同时也提供了平台能力，用户可以使用平台将内网中的终端分享到外网访问。

## 什么是pytmate

tmate本身只支持类Unix系统（MacOS、Linux等），不支持Windows。而pytmate使用纯Python开发，可以支持全系统，使用也更加方便。

## 环境要求

* Windows 7以上（推荐使用`Windows 10 1809`以上，低版本不支持`pty`）
* Linux
* MacOS

Python版本要求`>=3.6`

## 安装

```bash
$ pip install tmate
```

## 如何使用

```bash
$ tmate
[TMateClient] Connect SSH server ssh.tmate.io:22...
[Notify] web session read only: https://tmate.io/t/ro-Q5VKGqmt24FxTnUqtdzCZHhtR
[Notify] ssh session read only: ssh ro-Q5VKGqmt24FxTnUqtdzCZHhtR@xxx.tmate.io
[Notify] web session: https://tmate.io/t/9bv76cP3W95ftZFbWtYtW4xJ7
[Notify] ssh session: ssh 9bv76cP3W95ftZFbWtYtW4xJ7@xxx.tmate.io

```

Web端访问终端可以在浏览器中打开`web session: `后面的URL。

SSH访问可以使用`ssh session: `后面的命令行。


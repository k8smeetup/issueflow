# -*- coding: UTF-8 -*-
import os
import github
import githubutil
from githubutil.github import GithubOperator
from gitutil.configure import Configuration as RepoConfig
from gitutil.commands import GitCommand
from transutil.transutil import TranslateUtil
from errbot import BotPlugin, botcmd, arg_botcmd

import re,logging
logger = logging.getLogger('k8smeetup')

MAX_RESULT = int(os.getenv("MAX_RESULT"))
MAX_WRITE = int(os.getenv("MAX_WRITE"))
OPEN_CACHE = "/errbot/config/open_cache.txt"
REPOSITORY_CONFIG_FILE = os.getenv("REPOSITORY_CONFIG_FILE")
REPOSITORY_NAME = os.getenv("REPOSITORY")
TARGET_LANG = os.getenv("TARGET_LANG")

def limit_result(result_set):
    """
    Limit result list with "MAX_RESULT"
    :type result_set: list of str
    :rtype: list of str
    """
    max_result = MAX_RESULT
    result = []
    if max_result > 0:
        result = result_set[:max_result]
    result.append("Total result: {}".format(len(result_set)))
    return result


class TransBot(BotPlugin):
    """
    ChatBot for Kubernetes & Istio
    """

    def _asset_bind(self, msg):
        assert self._github_bound(msg.frm.person), \
            "Bind your Github token please."

    def _github_bound(self, person):
        """
        Check if user had bound their github token.
        :param person:
        :rtype: bool
        """
        result = True
        try:
            result = len(self[person + "github_token"]) > 0
        except:
            result = False
        return result

    def _translation_util(self, msg):
        """
        Get an Translation Util
        :param msg:
        :rtype: TranslateUtil
        """
        token = self[msg.frm.person + "github_token"]
        return TranslateUtil(REPOSITORY_CONFIG_FILE, token, REPOSITORY_NAME, logger)

    @arg_botcmd('token', type=str)
    def github_bind(self, msg, token):
        client = github.Github(token)
        from_user = msg.frm.person
        user = client.get_user()
        self[from_user + "github_token"] = token
        self[from_user + "github_login"] = user.login
        return "Hello {}, Welcome.".format(user.login)

    @botcmd
    def github_whoami(self, msg, args):
        from_user = msg.frm.person
        try:
            yield ("**Github Token:**" + self[from_user + "github_token"])
            yield ("**Github Login:**" + self[from_user + "github_login"])
        except:
            yield ("**Bind your Github token please.**")

    @botcmd
    def show_limit(self, msg, args):
        self._asset_bind(msg)
        trans = self._translation_util(msg)
        limit = trans.show_limit()

        core_pattern = "Core-Limit: {}\nCore-Remaining: {}\nCore-Reset: {}\n"
        search_pattern = "Search-Limit: {}\nSearch-Remaining: {}\nSearch-Reset: {}\n"
        return (core_pattern + search_pattern).format(
            limit["core"]["limit"],
            limit["core"]["remaining"],
            limit["core"]["reset"],
            limit["search"]["limit"],
            limit["search"]["remaining"],
            limit["search"]["reset"],
        )

    @botcmd
    def whatsnew(self, msg, args):
        """
        Find issues with the label "welcome"
        :param msg:
        :param args:
        :return:
        """
        self._asset_bind(msg)
        trans = self._translation_util(msg)
        issue_list = trans.whatsnew(REPOSITORY_NAME)

        result = limit_result(
            ["{}: {}".format(i.number, i.title)
             for i in issue_list])

        return "\n".join(result)

    @botcmd
    def cache_issue(self, msg, args):
        """
        Save opening issues into a text file
        :param msg:
        :param args:
        """
        self._asset_bind(msg)
        trans = self._translation_util(msg)
        query = "repo:{} is:open is:issue".format(
            trans.remote_repository_name(REPOSITORY_NAME)
        )
        res = trans.cache_issues(query, OPEN_CACHE, MAX_RESULT)
        return "{} records had been cached".format(res)
                                 
    # http://errbot.io/en/latest/user_guide/plugin_development/botcommands.html
    @arg_botcmd('query', type=str)
    def search_issues(self, msg, query):
        """
        Search for issues.
        :param query: content
        :return: Issue list.
        """
        self._asset_bind(msg)
        trans = self._translation_util(msg)

        issue_list = trans.search_issues(REPOSITORY_NAME, query)

        return "\n".join(limit_result(
            ["{}: {}".format(i.number, i.title)
             for i in issue_list]
        ))

    @arg_botcmd('issue_id', type=int)
    def show_issue(self, msg, issue_id):
        """
        Show issue url by its id.
        :param issue_id: ID of the issue.
        :type issue_id: int
        :return: URL
        :rtype: str
        """
        self._asset_bind(msg)
        trans = self._translation_util(msg)
        return "https://github.com/{}/issues/{}".format(trans.remote_repository_name(REPOSITORY_NAME),
                                                        issue_id)     
    # issue 查重
    @botcmd
    def find_dupe_issues(self, msg, args):
        """
        Find duplicated titles
        :param msg:
        :return:
        """
        trans = self._translation_util(msg)
        issue_list = trans.find_open_issues(REPOSITORY_NAME, MAX_RESULT)
 
        tuple_list = [(issue.title, issue.number) for issue in issue_list]
        tuple_list.sort()
        count_list = {}
        for title, number in tuple_list:
            if title in count_list.keys():
                count_list[title].append(number)
            else:
                count_list[title] = [number]
        result = ""
        count = 0
        for title, number_list in count_list.items():
            if len(number_list) == 1:
                continue
            result += "{} \n {}\n".format(
                title, " ".join([str(i) for i in number_list]))
            count += 1
        result += "\n{} duplicated issues found.".format(count)
        return result

    # 初始化 file 到数据库任务表 taskfiles
    @botcmd
    @arg_botcmd('branch', type=str)
    def init_files(self, msg, branch):
        """
        Initialize the issue of the specified version into the database.
        :param msg:
        :param branch:
        :return:
        """
        self._asset_bind(msg)
        trans = self._translation_util(msg)
        new_count, skip_count = trans.init_files(REPOSITORY_NAME, branch, TARGET_LANG, True)
        yield ("{} files had been created. {} files had been skipped.".format(
                new_count, skip_count))

    # 翻译文件对应的原始文档有更新, 更新数据到任务表 taskfiles
    @botcmd
    @arg_botcmd('branch', type=str)
    def update_files(self, msg, branch):
        """
        Initialize the issue of the specified version into the database.
        :param msg:
        :param branch:
        :return:
        """
        self._asset_bind(msg)
        trans = self._translation_util(msg)
        _, update_count = trans.init_files(REPOSITORY_NAME, branch, TARGET_LANG, False)
        yield ("{} files had been update. ".format(
                update_count))

    # 基于任务表 taskfiles 调用 github api 创建 issue
    @botcmd
    @arg_botcmd('branch', type=str)
    @arg_botcmd('--create_issue', type=int, default=0)
    def init_issue(self, msg, branch, create_issue):
        """
        Initialize the specified version of the issue.
        :param msg:
        :param branch:
        :return:
        """
        self._asset_bind(msg)
        trans = self._translation_util(msg)
        status = 1 # tatus 待生成 issue 2.需要更新的 issue
        issues = trans.init_issue_files(REPOSITORY_NAME, branch, TARGET_LANG, status, create_issue, MAX_WRITE, MAX_RESULT)
        tuple_list = [(issue.files) for issue in issues]

        if create_issue == 0:
            yield ("\n".join(limit_result(tuple_list)))
        else:
            yield ("{} Issues had been created.".format(len(tuple_list)))

    # 基于任务表 taskfiles 调用 github api 更新 issue
    @botcmd
    @arg_botcmd('branch', type=str)
    @arg_botcmd('--create_issue', type=int, default=0)
    def update_issue(self, msg, branch,create_issue):
        """
        update the specified version of the issue.
        :param msg:
        :param branch:
        :return:
        """
        self._asset_bind(msg)
        trans = self._translation_util(msg)
        status = 2 # tatus 待生成 issue 2.需要更新的 issue
        issues = trans.init_issue_files(REPOSITORY_NAME, branch, 
            TARGET_LANG, status, create_issue, MAX_WRITE, MAX_RESULT)

        tuple_list = [(issue.files) for issue in issues]

        if update_issue == 0:
            yield ("\n".join(limit_result(tuple_list)))
        else:
            yield ("{} Issues had been updated.".format(len(tuple_list)))

    @arg_botcmd('issue_id', type=int)
    @arg_botcmd('--comment', type=str)
    def comment_issue(self, msg, issue_id, comment):
        """
        Create comment for an issue
        :param msg:
        :param issue_id: Issue number
        :type issue_id: int
        :param comment: comment body
        :return: HTML
        """
        self._asset_bind(msg)
        trans = self._translation_util(msg)
        comment_obj = trans.comment_issue(REPOSITORY_NAME, issue_id, comment)
        return comment_obj.html_url
    
    @arg_botcmd('--comment', type=str)
    def batch_comment_issue(self, msg, comment):
        self._asset_bind(msg)
        trans = self._translation_util(msg)
        res = trans.batch_comment_issue(REPOSITORY_NAME, comment, MAX_RESULT)
        return "{} records had been cached".format(res)

    # 获取 kubernetes/website 所有的翻译 PR
    @botcmd
    def get_trans_pr(self,msg,args):
        self._asset_bind(msg)
        trans = self._translation_util(msg)
        trans_pr = trans.get_trans_pr(REPOSITORY_NAME, MAX_RESULT)
        yield("{} pr records had been create".format(trans_pr))
        
    # 获取 kubernetes/website 所有的翻译 files
    @botcmd
    def get_trans_files(self,msg,args):
        self._asset_bind(msg)
        trans = self._translation_util(msg)
        trans_files = trans.get_trans_files(REPOSITORY_NAME, MAX_RESULT)
        yield("{} pr file records had been create".format(trans_files))

    # 每周报表更新
    @botcmd
    @arg_botcmd('branch', type=str)
    def update_report(self, msg, branch):
        """
        update the specified version of the report.
        :param msg:
        :param branch:
        :return:
        """
        self._asset_bind(msg)
        trans = self._translation_util(msg)
        result = trans.report_update(REPOSITORY_NAME, branch, MAX_RESULT)
        yield("已完成周报更新！")

    @botcmd
    def list_branches(self, msg, args):
        """
        List all branches in current repository
        :param msg:
        :param args:
        :return:
        """
        trans = self._translation_util(msg)
        return "\n".join(trans.list_branches(REPOSITORY_NAME))

    @botcmd
    def refresh_repositories(self, msg, args):
        config = RepoConfig(REPOSITORY_CONFIG_FILE)
        branches = config.get_repository(REPOSITORY_NAME)["branches"]
        for branch in branches:
            cmd = GitCommand(branch["path"])
            cmd.checkout(branch["value"])
            cmd.pull()
            yield ("{} had been updated.".format((branch["value"])))

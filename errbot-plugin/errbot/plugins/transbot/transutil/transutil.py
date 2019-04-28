from gitutil.commands import GitCommand
from gitutil.configure import Configuration
from os.path import splitext
from githubutil.github import GithubOperator
from transdb.transdb import TransDB, Taskfiles
import os,json,re
from datetime import datetime

class TranslateUtil:
    _git_path = ""
    _github_token = ""
    _configure = None
    _connstr = ""
    _github_client = None
    _trans_db = None

    def __init__(self, config_file, github_token, repository_name, logger, git_path="git"):
        """
        Initialization.

        :param config_file: Name of the repository config file.
        :type config_file: str
        :param github_token: Github token
        :type github_token: str
        :param git_path: Executable git path.
        :type git_path: str
        """
        self._git_path = git_path
        self._configure = Configuration(config_file)
        self._github_token = github_token

        self._connstr = self._configure.get_conn(repository_name)
        self._github_client = GithubOperator(self._github_token)
        self._trans_db = TransDB(self._connstr, logger)
       
    def _filter_file_type(self, repository_name, file_name_list):
        """
        Only files with extensions in the list will left.
        :param repository_name: Repository name (in the config file)
        :type repository_name: str
        :param file_name_list:
        :type file_name_list: list
        :rtype: list
        """
        ext_list = self._configure.get_valid_extensions(repository_name)
        result = []
        for file_name in file_name_list:
            _, ext = splitext(file_name)
            if ext in ext_list:
                result.append(file_name)
        return result

    def _get_git_commander(self, repo):
        return GitCommand(repo, self._git_path)

    def _get_repo_path(self, repository_name, branch_name):
        self._configure.repository = repository_name
        branch_item = self._configure.get_branch(repository_name, branch_name)

        return branch_item

    def __is_ignore(self, file_name, ignore_list):
        result = False
        for pattern in ignore_list:
            if re.match(pattern, file_name):
                result = True
                break
        return result

    def _remove_ignore_files(self, file_list, repository, branch):
        ignore_list = self._configure.get_ignore_re_list(repository, branch)
        result_list = [item for item in file_list if not self.__is_ignore(item, ignore_list)]
        return result_list

    def _get_clean_files(self, repository, branch_path, path):
        """
        Get file list in specified path.

        :param path: Relative path of the files we want.
        :type path: str
        :rtype: list
        """
        file_list = self._get_git_commander(branch_path).list_files()
        file_list = self._filter_file_type(repository, file_list)
        path_sep = path.split(os.sep)
        result = [file_name[len(path):]
                  for file_name in file_list
                  if file_name.split(os.sep)[:len(path_sep)] == path_sep]
        return result

    def list_branches(self, repository_name):
        return self._configure.list_branch(repository_name)

    def wait_for_limit(self, core_limit=10, search_limit=10):
        self._github_client.check_limit(core_limit, search_limit)


    def find_files_comm(self, repository_name, branch_name, language, is_create):

        """
        Find files which is in the source path, but not in the
        target path, and return it as a List of string.

        :param branch_name:
        :param repository_name:
        :rtype: list of str
        :param language: Language name (in the configure file)
        :param is_create true 创建issue false 更新 issue
        :type language: str
        """

        target_path = self._configure.get_languages(
            repository_name, language)["path"]

        source_path = self._configure.get_source(
            repository_name)["path"]

        branch_item = self.checkout_branch(repository_name, branch_name)
        branch_path = branch_item['path']

        # List files in source/language path
        source_list = self._get_clean_files(repository_name,
                                            branch_path, source_path)
        target_list = self._get_clean_files(repository_name,
                                            branch_path, target_path)

        # return the different files list
        # 差集用于新建 issue（即翻译文档不存在）
        result_diff = list(set(source_list) - set(target_list))
        result_diff.sort()
        # return the intersection files list
        # 交集用于更新 issue(即翻译文档已经存在，可能需要更新)
        result_inter = list(set(source_list) & set(target_list))
        result_inter.sort()

        diff = self._remove_ignore_files(result_diff, repository_name, branch_name)
        inter_list = self._remove_ignore_files(result_inter, repository_name, branch_name)

        if is_create == True:
            inter = inter_list
        else:
            git_cmd = self._get_git_commander(branch_path)
            inter_result = {}
            for file_name in inter_list:
                source_last_commit = git_cmd.get_last_commit(source_path + file_name)
                target_commit = git_cmd.get_last_commit(target_path + file_name)

                target_time = git_cmd.get_hash_time(target_commit)

                source_base_commit = git_cmd.get_file_hash_before(
                    source_path + file_name, target_time)
                # 返回差异文件
                if source_base_commit != source_last_commit:
                    diff_file = git_cmd.get_diff_by_hash(
                        source_path + file_name,
                        source_last_commit, source_base_commit)
                    inter_result[file_name] = diff_file

            inter = inter_result

        return {"diff": diff, "inter": inter}

    # checkout branch
    def checkout_branch(self, repository_name, branch_name):
        branch_item = self._get_repo_path(repository_name, branch_name)
        cmd = GitCommand(branch_item['path'])
        cmd.checkout(branch_item['value'])
        cmd.pull()
        return branch_item

    def init_files(self, repository_name, branch_name, language, is_create):
        """
        Find all documents for a branch
        status: 
        初始化阶段
            0 未生成 issue (对应翻译文件已存在- 这里标记不生新的 issue)
            1 待生成 issue (对应翻译文件不存在- 标记生成初始化 issue)
        文档更新阶段
            2 翻译文件对应的原始文件有更新(标记需要在生成 issue) 
        issue 生成状态
            3 对应的翻译文件(issue 已生成)
        """
        result = self.find_files_comm(repository_name, branch_name, language, is_create)

        
        if is_create == True:
            self._trans_db.add_issue(result['diff'], branch_name, 1)
            self._trans_db.add_issue(result['inter'], branch_name, 0)
        else:
            self._trans_db.add_issue(result['inter'], branch_name, 2)

        return len(result['diff']), len(result['inter'])

    def init_issue_files(self, repository_name, branch_name, language, status, create_issue, max_write, max_result):
        #status 待生成 issue 2.需要更新的 issue 3.已生成 issue
        tasks = self._trans_db.pending_issues(branch_name, status)
        
        if create_issue == 1:
            new_count = 0
            skip_count = 0
            for task in tasks:
                file_name = task.files
                if status == 1:
                    type_label = "sync/new"
                    diff = ""
                    body = "Source File: [{}]({})"
                    body = body.format(
                        file_name,
                        self.gen_source_url(repository_name, branch_name, file_name),
                    )
                elif status == 2:
                    type_label = "sync/update"
                    diff = task.diff_content
                    body = "Source File: [{}]({})\nDiff:\n~~~diff\n {}\n~~~"
                    body = body.format(
                        file_name,
                        self.gen_source_url(repository_name, branch_name, file_name),
                        diff
                    )
                else:
                    break
                
                default_label = self.get_default_label(repository_name, branch_name, language)
                search_label = default_label

                default_label.append(type_label)

                if file_name.find("/docs/") == -1:
                    docs = False 
                    default_label.append('priority/P1')
                else:
                    docs = True  #Docs 文档
                    default_label.append('priority/P0')

                # create issue
                new_issue = self.create_issue(
                    self.remote_repository_name(repository_name),
                    file_name, body, default_label, default_label,
                    "", False
                )
                if new_issue is None:
                    skip_count += 1
                else:
                    # new_count += 1
                    self._trans_db.add_update_issues(file_name, diff, task.version, docs, 3, new_issue.number)

                    # if new_count >= max_write:
                    #     break
                    # if (new_count + skip_count) % max_result:
                    #     self.wait_for_limit(max_result, max_result)
        return tasks

    def remote_repository_name(self, repository_name):
        repo_obj = self._configure.get_repository(repository_name)
        repo_owner = repo_obj["github"]["owner"]
        repo_name = repo_obj["github"]["repository"]
        return "{}/{}".format(repo_owner, repo_name)

    def website_repository_name(self, repository_name):
        repo_obj = self._configure.get_repository(repository_name)
        repo_owner = repo_obj["website"]["owner"]
        repo_name = repo_obj["website"]["repository"]
        return "{}/{}".format(repo_owner, repo_name)

    def k8s_official_repository_name(self, repository_name):
        repo_obj = self._configure.get_repository(repository_name)
        repo_owner = repo_obj["k8s-official"]["owner"]
        repo_name = repo_obj["k8s-official"]["repository"]
        return "{}/{}".format(repo_owner, repo_name)


    def cache_issues(self, query, file_name, search_limit=30):
        """
        :param search_limit:
        :param query: Github query string
        :param file_name: Save search result into a json file

        record = {"query": query,
            "timestamp": 1234567
            items:
            [
                {
                "number": 1234,
                "title": "Issue Title",
                labels: ["version/1.12", "translating"]
                },
            ]
        }
        """
        issue_list = self._github_client.search_issue(query, search_limit)
        result = []
        for issue in issue_list:
            issue_item = {
                "number": issue.number,
                "title": issue.title,
                "labels": []
            }
            for label in issue.labels:
                issue_item["labels"].append(label.name)
            result.append(issue_item)
        with open(file_name, "w") as handle:
            json.dump(result, handle, indent=2)
        return len(result)

    def get_default_label(self, repository_name, branch, language):
        """
        :param repository_name:
        :param branch:
        :param language:
        :return:
        """
        labels = self._configure.get_branch(repository_name, branch)["labels"]
        labels += self._configure.get_languages(repository_name, language)["labels"]
        return labels

    def create_issue(self, github_repository, title, body, labels=[],
                     search_labels=[],
                     search_cache="",
                     search_online=False):
        """
        :param labels: Labels for new issue
        :type labels: list of str
        :param search_online: Search duplicated issues online
        :param github_repository: Name of the repository.
        :param title: Title of the new issue.

        :param body: Body of the new issue.
        :param search_labels: Search duplicated issues with title & labels.
        :type search_labels: list of str
        :param search_cache: Search in the cache file
        :type search_cache: str
        :rtype: github.Issue.Issue
        """
        dupe = False
        if len(search_cache) > 0:
            with open(search_cache, "r") as handler:
                obj = json.load(handler)
                for issue_record in obj:
                    if issue_record["title"] == title:
                        if len(search_labels) == 0:
                            dupe = True
                            break
                        else:
                            if set(search_labels).issubset(issue_record["labels"]):
                                dupe = True
                            break
        if search_online:
            search_cmd = "repo:{} state:open is:issue in:title {}".format(github_repository, title)
            if len(search_labels) > 0:
                search_cmd = "{} {}".format(search_cmd,
                                            " ".join(
                                                ["label:{}".format(i) for i in search_labels])
                                            )
            issue_list = self._github_client.search_issue(search_cmd)
            for issue in issue_list:
                if issue.title == title:
                    dupe = True
        if dupe:
            return None
        new_issue = self._github_client.create_issue(github_repository, title, body)
        # Add labels
        for label_name in labels:
            new_issue.add_to_labels(label_name)
        return new_issue

    def gen_source_url(self, repo, branch, file_name):
        """
        :param repo:
        :param branch:
        :param file_name:
        """
        prefix = self._configure.get_branch(repo, branch)["url_prefix"]["source"]
        middle = ""
        if file_name[:1] != "/":
            middle = "/"
        return "{}{}{}".format(prefix, middle, file_name)

    def gen_web_url(self, repo, branch, file_name):
        """
        :param repo:
        :param branch:
        :param file_name:
        """
        prefix = self._configure.get_branch(repo, branch)["url_prefix"]["web"]
        middle = ""
        if file_name[:1] != "/":
            middle = "/"
        return "{}{}{}".format(prefix, middle, file_name)

    def whatsnew(self, repository_name ):
        cmd = "repo:{} label:welcome is:open type:issue".format(
            self.remote_repository_name(repository_name))
        issue_list = self._github_client.search_issue(cmd, 10)
        return issue_list

    def comment_issue(self, repository_name, issue_id, comment):
        comment_obj = self._github_client.issue_comment(self.remote_repository_name(repository_name),
                                           issue_id, comment)
        return comment_obj

    # 批量确认 issue 状态
    def batch_comment_issue(self,repository_name, comment, max_result):

        issue_list = self.find_open_issues(repository_name, max_result)
        for issue in issue_list:
            self._github_client.issue_comment(
                self.remote_repository_name(repository_name),
                issue.number, comment)

        return len(issue_list)

    def search_issues(self, repository_name, query):
        # tmpstr = "{} label:version/1.12 is:open type:issue repo:{}".format(query, remote_repository_name())
        tmpstr = "{} is:open type:issue repo:{}".format(
            query, self.remote_repository_name(repository_name))

        issue_list = self._github_client.search_issue(tmpstr, 10)
        return issue_list

    def show_limit(self):
        limit = self._github_client.get_limit()
        return limit

    def find_open_issues(self, repository_name, max_result):
        query = "repo:{} is:open is:issue".format(self.remote_repository_name(repository_name))
        issue_list = self._github_client.search_issue(query, max_result)
        return issue_list

    # https://developer.github.com/v3/pulls/
    def get_trans_pr(self, repository_name, max_result):
        query = "repo:{} is:pr label:language/zh".format(self.website_repository_name(repository_name))
        pr_list = self._github_client.search_issue(query, max_result)
        
        self._trans_db.add_update_pr(pr_list)
        return len(pr_list) 
    
    # 获取翻译文件
    def get_trans_files(self, repository_name, max_result):
        prs = self._trans_db.get_prs()

        new_count = 0
        for pr in prs:
            pr_doc = self._github_client.pr_files(self.website_repository_name(repository_name), pr.number)
            self._trans_db.add_update_files(pr, pr_doc) 

            new_count = new_count + 1
            if new_count % max_result:
                self.wait_for_limit(max_result, max_result)
        return len(prs)

    # 更新译者信息
    def _update_author(self, max_result):
        users = self._trans_db.user_list()
        new_count = 0
        for user in users:
            user_info = self._github_client.get_user(user.author)
            self._trans_db._add_update_author(user_info) 
            new_count = new_count + 1
            if new_count % max_result:
                self.wait_for_limit(max_result, max_result)
        return list(users)

    # 更新周报
    def _update_report(self,repository_name, file_name, comment, repeat):
        content = self._trans_db._week_report(repeat)
        tmp_file = self._github_client.create_file(
            self.k8s_official_repository_name(repository_name),
            file_name, 
            comment,
            content)
        return tmp_file['content'].path

    def report_update(self, repository_name, branch_name, max_result):
        # 1. 译者信息更新
        user_count = self._update_author(max_result)
        # 2. 指定版本翻译文档中文字数统计
        branch_item = self.checkout_branch(repository_name, branch_name)
        files_count = self._trans_db._files_cn_word_count(branch_item)
        # 3. 译者翻译字数统计(含翻译+更新)
        author_count = self._trans_db._author_files_cn_word_count()
        # 4. 以周为单位进行数据统计(更新 week_trans 数据表 0.新增 1.更新)
        self._trans_db._week_author_cn_word_count(0) 
        self._trans_db._week_author_cn_word_count(1)
        # 5. 生成翻译周报(含翻译+更新)
        file_create_name = self._update_report(repository_name, 
            "report/contribution-stage2.md", "周报更新-(新增)", 0)
        file_update_name = self._update_report(repository_name, 
            "report/contribution-stage2-update.md", "周报更新-(更新)", 1)
        # 6. 生成图表展示文件 - data.json
        json_data = self._trans_db.get_echarjs_data()
        tmp_file = self._github_client.create_file(
            self.k8s_official_repository_name(repository_name),
            "data.json","报表更新", json_data)

        return {"user_count": user_count, "files_count": files_count, 
            "author_count":author_count, "file_create_name": file_create_name,
            "file_update_name":file_update_name, "json_file": tmp_file['content'].path}

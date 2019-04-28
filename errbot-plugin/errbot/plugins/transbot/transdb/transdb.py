# -*- coding: utf-8 -*-

# https://docs.sqlalchemy.org/en/latest/orm/tutorial.html
from sqlalchemy import Column,PrimaryKeyConstraint,UniqueConstraint,create_engine,and_, or_
from sqlalchemy.types import CHAR,Boolean,Integer,String,Text,Date
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime,timedelta
from copy import deepcopy
import re, os, json


# # 创建对象的基类:
Base = declarative_base()

# 定义 Author 对象:
class Author(Base):
  __tablename__ = 'author'
  id = Column(Integer, primary_key=True)
  author = Column(String)
  username = Column(String)
  chinese_name = Column(String)
  company = Column(String)
  blog = Column(String)
  email = Column(String)
  join_date = Column(Date)
  sign_cla = Column(Boolean)
  cn_word_count = Column(Integer)

# label:
  # "welcome" 
  # "pending"
  # "translating"
  # "pushed"
  # "finished"
# status:
  # 0 跳过 issue 
  # 1 待生成 issue 
  # 2 待更新 issue
  # 3 已生成 issue
# confirm:
  # 0 issue 未确认
  # 1 issue 已确认
class Taskfiles(Base):
  __tablename__ = 'taskfiles'
  issue_id = Column(Integer, primary_key=True)
  files = Column(String)
  version = Column(String)
  docs = Column(Boolean)
  status = Column(Integer) 
  diff_content = Column(Text)
  label = Column(String)
  translator = Column(String)
  reviewer = Column(String)
  pull_request_link = Column(String)
  priority = Column(String)
  number = Column(Integer)
  confirm = Column(Integer) 
  note = Column(String)
  UniqueConstraint('files', 'version', name='unique_files_version')

class Requestpull(Base):
  __tablename__ = 'request_pull'
  id = Column(Integer, primary_key=True)
  title = Column(String)
  html_url = Column(String)
  number = Column(Integer)
  state = Column(String)
  create_at = Column(Date)
  author = Column(String)
  username = Column(String)
  process = Column(Integer)
  
# repeat:
  # 0 文件没有重复
  # 1 文件有重复
class RequestPullDocs(Base):
  __tablename__ = 'request_pull_docs'
  id = Column(Integer, primary_key=True)
  pid = Column(Integer)
  number = Column(Integer)
  files = Column(String)
  author = Column(String)
  review_author = Column(String)
  create_at = Column(String)
  week_number = Column(Integer)
  repeat = Column(Integer)
  is_merged = Column(Boolean)
  pr_version = Column(String)
  cn_word_count = Column(Integer)

class Transweek(Base):
  __tablename__ = 'trans_week'
  id = Column(Integer, primary_key=True)
  author = Column(String)
  week_number = Column(Integer)
  week_string = Column(String)
  repeat = Column(Integer)
  cn_word_count = Column(Integer)

class TransDB:
  # 构造函数
  def __init__(self, config, logger):
    # 创建对象的基类:
    engine = create_engine(config)
    Base.metadata.create_all(engine)
    # 创建DBSession类型:
    self.DBSession = sessionmaker(bind=engine)
    self.logger = logger

  # Author
  def add_author(self):
    session = self.DBSession()

    session.commit()
    session.close()

  def del_author(self):
    session = self.DBSession()

    session.commit()
    session.close()

  # 获取待生成的 issue 列表
  def pending_issues(self, branch_name, status):
    session = self.DBSession()
    tasks = session.query(Taskfiles).filter(and_(Taskfiles.version==branch_name, Taskfiles.status==status)).all()
    session.close()
    return tasks

  # Taskfiles
  def add_issue(self, issues, branch_name, status):
    """
    status: 
      初始化阶段
        0 未生成 issue (对应翻译文件已存在- 这里标记不生新的 issue)
        1 待生成 issue (对应翻译文件不存在- 标记生成初始化 issue)
      文档更新阶段
        2 翻译文件对应的原始文件有更新(标记需要在生成 issue) 
      issue 生成状态
        3 对应的翻译文件(issue 已生成)
    """
    diff_content=""
    docs = ""
    number = 0
    if type(issues) == dict:
      file_list = list(issues.keys())
      for issue in file_list:
        diff_content = issues[issue]
        file_name = issue
        self.add_update_issues(file_name, diff_content, branch_name, docs, status, number)
    else:
      for i in range(0, len(issues)):
        file_name = issues[i]
        self.add_update_issues(file_name, diff_content, branch_name, docs, status, number)

  # issue 任务表状态
  def add_update_issues(self, file_name, diff_content, branch_name, docs, status, number):
    session = self.DBSession()
    is_exist = session.query(Taskfiles).filter(and_(Taskfiles.files==file_name, Taskfiles.version==branch_name)).first()
    if is_exist is None:
        try:
          session.add(Taskfiles(files = file_name, diff_content = diff_content, version= branch_name, status = status, docs = docs, number = number))
        except BaseException as e:
          self.logger.error(e)
          self.logger.info(file_name)
    else:
      # 翻译 issue 对应的原始文件有更新
      session.execute("update taskfiles set diff_content=:diff_content, number=:number, status=:status where files=:files and version=:version", 
        {
          "status": status, 
          "number": number,
          "diff_content": diff_content,
          "files": file_name, 
          "version": branch_name
        })
    session.commit()
    session.close()

  # Requestpull
  def add_update_pr(self, pr_list):
    """
    功能: 存储所有 `is:pr label:language/zh` 状态的 PR，用于后续翻译文章抽取
    """
    session = self.DBSession()
    process = 0 # 0 未处理 1 已处理
    for pr in pr_list:
      is_exist = session.query(Requestpull).filter(Requestpull.number==pr.number).first()
      if is_exist is None:
        try:
          session.add(Requestpull(title = pr.title, 
                  number= pr.number, 
                  html_url = pr.html_url,
                  create_at = pr.created_at, 
                  state = pr.state, 
                  author = pr.user.login,
                  username = pr.user.name,
                  process = process ))
        except BaseException as e:
          self.logger.error(e)
          self.logger.info(pr.html_url)
      session.commit()
    session.close()

  # 获取 PR 文档列表
  def get_prs(self):
    session = self.DBSession()
    # 根据 PR Number 排序
    prs = session.query(Requestpull).filter(Requestpull.process==0).order_by(Requestpull.number).all()
    session.close()
    return prs

  def add_update_files(self, pr, pr_docs):
    """
    功能: 抽取 PR 对应的翻译文档
      获取 PR 的 review 作者, 更新 PR 数据表
      获取 PR 的 files 列表，更新 PR 文档数据表
    """
    session = self.DBSession()

    reviews = pr_docs['reviews']
    files = pr_docs['files']
    is_merged = pr_docs['is_merged']
    pr_version = pr_docs['pr_version']

    # 获取 PR review 作者
    tmp_author = []
    for review in reviews:
      author=review.user.login
      tmp_author.append(author)

    tmp_review = list(set(tmp_author))
    review_author = ",".join(tmp_review)

    for tmp_file in files:
      file_name = tmp_file.filename
      is_exit = True
      if (os.path.splitext(file_name)[1] == '.md' 
        or os.path.splitext(file_name)[1] == '.htm'
        or os.path.splitext(file_name)[1] == '.html'):
        if file_name.find("content/zh/") == -1:
          is_exit = False
      else:
        is_exit = False

      if is_exit == True:
        is_exist = session.query(RequestPullDocs).filter(and_(RequestPullDocs.files==file_name, RequestPullDocs.pr_version==pr_version)).first()
        if is_exist is None:
          repeat = 0
        else:
          repeat = 1

        week_number = pr.create_at.strftime("%W")
        session.add(RequestPullDocs(
            pid = pr.id, 
            number = pr.number, 
            files= file_name, 
            author = pr.author, 
            review_author = review_author, 
            create_at = pr.create_at,
            week_number = week_number,
            repeat = repeat,
            is_merged=is_merged,
            pr_version = pr_version
          ))
    # 更新 PR 状态
    session.execute("update request_pull set process=:process where number=:number", {"process": 1, "number": pr.number})
    session.commit()
    session.close()

  # 下述函数均用于报表统计生成
  
  def user_list(self):
    """
    功能: 从翻译文档中提取译者列表
    """
    session = self.DBSession()
    sql = "select author from request_pull_docs group by author"
    users = session.execute(sql)
    session.close
    return users

  def _add_update_author(self, userinfo):
    """
    功能: 从 PR files 文件中提取作者信息
    """
    session = self.DBSession()
    # https://api.github.com/users/markthink
    is_exist = session.query(Author).filter(Author.author==userinfo.login).first()
    if is_exist is None:
        session.add(Author(
          author = userinfo.login, 
          username = userinfo.name, 
          company= userinfo.company, 
          email = userinfo.email, 
          blog = userinfo.blog,
          join_date = userinfo.created_at
        ))
    else:
      session.execute("update author set username=:username, company=:company,email=:email, blog =:blog where author=:author", 
        {
          "username": userinfo.name, 
          "company": userinfo.company, 
          "email": userinfo.email, 
          "blog": userinfo.blog,
          "author": userinfo.login
        })
    session.commit()
    session.close()

  def _cn_WordCount(self, transfile):
    """
    功能: 单文件-中文翻译字数统计
    """
    regex=re.compile(r"[\u4e00-\u9fa5]")
    count = 0
    if os.path.exists(transfile):
      with open(transfile, 'r') as f:
          for line in f.readlines():
              word = [w for w in regex.split(line.strip())]
              count += len(word)-1
    # print(transfile +':'+ str(count))
    return count

  # 
  def _files_cn_word_count(self, branch_item):
    """
    功能: 对上游已经 merge 的翻译文件进行中文字数统计
    参数: branch_item 获取配置的分支信息
    """
    session = self.DBSession()
    # 查询所有 release-x 版本已 merge 的文件
    sql_files = "select * from request_pull_docs where is_merged=true and pr_version=:branch_name order by create_at"
    files = session.execute(sql_files,{"branch_name":branch_item['value']})
    for tmp_file in files:
      count = self._cn_WordCount(branch_item['path']+'/'+tmp_file.files)
      session.execute("update request_pull_docs set cn_word_count=:cn_word_count where id=:id", 
        {
          "cn_word_count": count, 
          "id": tmp_file.id
        })
      session.commit()
    session.close
    return files.rowcount

  def _author_files_cn_word_count(self):
    """
    功能: 统计译者所译文字(含翻译+更新)
    """
    session = self.DBSession()
    sql_files = "select sum(cn_word_count) as trans_count,author from request_pull_docs \
	      where is_merged=true and cn_word_count!=0 group by author order by trans_count"
    author_rs = session.execute(sql_files)
    for author_group in author_rs:
      session.execute("update author set cn_word_count=:cn_word_count where author=:author", 
        {
          "cn_word_count": author_group.trans_count, 
          "author": author_group.author
        })
      session.commit()
    session.close()
    return author_rs.rowcount
  
  def _week_author_cn_word_count(self, repeat):
    """
    功能: 对每周所有译者进行翻译统计
    参数: repeat
      0 表示新增翻译
      1 表示更新翻译
    """
    sql_author = "select author from author where cn_word_count!=0 order by join_date"
    # 获取指定译者周翻译字数
    sql_files ="select sum(cn_word_count) as word_count,week_number,min(create_at) as create_at from request_pull_docs where is_merged=true  \
	      and cn_word_count!=0 and repeat=:repeat and author=:author  group by week_number"
    sql_week = "select * from trans_week where author=:author and  week_number=:week_number and repeat=:repeat"
    session = self.DBSession()
    authors =  session.execute(sql_author)
    for author_group in authors:
      author = author_group.author
      week_info =  session.execute(sql_files, {"author":author, "repeat": repeat}).first()
      if week_info is not None:
        word_count = week_info.word_count
        word_number = week_info.week_number
        week_time = datetime.strptime(week_info.create_at, '%Y-%m-%d')

        week_number = self._fixUpdateWeek(week_time, word_number)
        week_string = self._getWeekArea(week_time)

        is_exist = session.execute(sql_week,{"author":author, "week_number":week_number, "repeat": repeat}).first()
        if is_exist is None:
          session.add(Transweek(
              author = author, 
              week_number = week_number, 
              week_string= week_string, 
              repeat = repeat,
              cn_word_count = word_count
            ))
        else:
          session.execute("update author set cn_word_count=:cn_word_count where author=:author", 
          {
            "cn_word_count": word_count, 
            "author": author,
            "week_number": week_number,
            "repeat": repeat
          })
      session.commit()
    session.close()

  def _getWeekArea(self, curtime):
    """
    功能: 根据当前周数返回周区间字符串
    """
    dayscount = timedelta(days=curtime.isoweekday())
    dayfrom = curtime - dayscount + timedelta(days=1)
    dayto = curtime - dayscount + timedelta(days=7)
    week_info = ' ~ '.join([str(dayfrom.strftime('%Y-%m-%d')), str(dayto.strftime('%Y-%m-%d'))])
    return week_info

  def _fixUpdateWeek(self, curtime, week_number):
    """
    功能: 翻译周期校正 (因为每年 52 周，对不同年份要区分处理)
      sql: select cn_word_count, author,create_at,week_number from request_pull_docs 
      where is_merged=true and cn_word_count!=0 and repeat=0 
      order by create_at
      第二阶段翻译获取的基准周期值: 43 
      一年有 52 周，故2019年修正值为: 52-43 = 9, 2020年修正值为 52+9=61 后续年份以此类推
    """
    if (curtime.year == 2018):
        exist_number = week_number - 43
    elif (curtime.year == 2019):
        exist_number = week_number + 9
    elif (curtime.year == 2020):
      exist_number = week_number + 61
    return exist_number

  def _getWeekInfo(self, week_number, curtime, repeat):
    """
    功能: 报表头处理
    参数:
      week_number: 当前周期
      curtime: 当前时间
      repeat: 0 新增 1 更新
    """
    week_info = self._getWeekArea(curtime)
    year = curtime.year
    week_head = ""

    # 统计合并文章数量
    session = self.DBSession()
    week_sql = "select count(*) as week_count from request_pull_docs \
      where is_merged=true and cn_word_count!=0 and repeat=:repeat and week_number=:week_number and create_at like :param"
    file_count = session.execute(week_sql, {"repeat":repeat, "week_number": week_number, "param": str(year)+"%"}).fetchone()
    if file_count is not None:
      exist_number = self._fixUpdateWeek(curtime, week_number)
      week_head = "### 第 " + str(exist_number) + " 周：" + week_info + " - 有效合并 " + str(file_count.week_count) + " 篇"
    return week_head

  def _week_report(self,repeat):
    """
    功能: 生成周报(提交到 github)
    参数:
      repeat: 0 新增 1 更新
    """
    session = self.DBSession()
    select_sql = "select * from request_pull_docs \
        where is_merged=true and cn_word_count!=0 and repeat=:repeat order by create_at desc"
    files =  session.execute(select_sql, {"repeat": repeat}).fetchall()


    file_head = "# K8SMeetup 中文翻译社区每周文章贡献汇编\n\n本文档只包含新增更新，[更新参考](contribution-stage2-update.md)\n\n"
    if repeat == 1:
      file_head = "# K8SMeetup 中文翻译社区每周文章更新汇编\n\n"

    context = []
    context.append(file_head)

    # 初始化周数字
    cur_week = 0
    for art in files:
      week_time = datetime.strptime(art.create_at, '%Y-%m-%d')
      exist_number = self._fixUpdateWeek(week_time, art.week_number)
      
      if cur_week == 0:
        week_info = self._getWeekInfo(art.week_number, week_time, repeat)+"\n\n"
        cur_week = exist_number
        context.append(week_info)
      elif exist_number < cur_week:
        week_info = self._getWeekInfo(art.week_number, week_time, repeat)+"\n\n"
        cur_week = exist_number
        context.append(week_info)

      report = "- ["+ art.files +"](https://github.com/kubernetes/website/blob/"+ \
        art.pr_version+"/"+art.files+") **version:" + art.pr_version + \
        "** by ["+art.author+"](https://github.com/"+ art.author+")\n\n"

      context.append(report)
    session.close()
    return ''.join(context)


  def get_echarjs_data(self):
    """
    功能: 生成 echarjs 报表数据
    """
    session = self.DBSession()
    chartjs_data = []

    sql = "select author,cn_word_count from author where cn_word_count!=0 order by cn_word_count desc"
    author_group =  session.execute(sql).fetchall()

    pie_dict = self._week_author_pie_data(author_group)
    bar_dict = self._week_author_bar_data(author_group)
    week_dict_create = self._week_timeline_data(author_group, 0)
    week_dict_update = self._week_timeline_data(author_group, 1)

    chartjs_data.append(pie_dict)
    chartjs_data.append(bar_dict)
    chartjs_data.append(week_dict_create)
    chartjs_data.append(week_dict_update)
    return json.dumps(chartjs_data)

  def get_overview_date(self):
    """
    功能: 返回各个分支的整体情况
    """
    return []

  def _week_author_pie_data(self, author_group):
    """
    功能: 饼图生成 - 汇总每个人的翻译总量
    """
    author_data = []
    word_count_data = []
    for author in author_group:
      author_data.append(author.author)
      seriesData = {"name":  author.author, "value": author.cn_word_count}
      word_count_data.append(seriesData)
    pie_dict = {"legendData": author_data, "seriesData": word_count_data}
    return pie_dict

    # with open('data.json', 'w') as f:
    #   f.write(json.dumps(chartjs_data))

  def _week_author_bar_data(self, author_group):
    """
    功能: 柱图生成 - 汇总每个人的翻译总量
    """
    author_data = ["总翻译字数"]
    series_data = [0]
    # 统计翻译总字数
    accumlate = 0
    for author in author_group:
      author_data.append(author.author)
      series_data.append(author.cn_word_count)
      accumlate += author.cn_word_count
    series_data[0] = accumlate
    
    demo = deepcopy(series_data)
    demo.reverse()

    cn_word_count = len(demo) - 1 
    series_title = [0]
    for key in range(cn_word_count):
      if key == 0:
        count = demo[key]
        series_title.append(count)
        continue
      count += demo[key]
      series_title.append(count)
    series_title[cn_word_count] = 0

    series_title.reverse()
    bar_dict = {"author": author_data, "series_title":series_title, "series_data": series_data}
    return bar_dict

  def _week_timeline_data(self, author_group, repeat):
    """
      每人每周翻译文件更新动态 查找所有的翻译周期
      repeat:
        0 新增翻译内容
        1 更新翻译内容
    """
    session = self.DBSession()
    sql_week = "select week_number,week_string from trans_week \
        group by week_number,week_string order by week_number"
    week_group =  session.execute(sql_week).fetchall()
    # 查找所有的译者
    author_data = []
    series_data = []
    for author in author_group:
      author_data.append(author.author)
      tmp_word = []
      for week in week_group:
        week_number = week.week_number
        sql = "select cn_word_count from trans_week \
          where author=:author and week_number=:week_number and repeat=:repeat"
        tmp =  session.execute(sql, {"author": author.author, "week_number": week_number,"repeat": repeat}).first()
        if tmp is None:
          cn_word_count = 0
        else:
          cn_word_count = tmp.cn_word_count
        tmp_word.append(cn_word_count)

      author_word = {"name": author.author, "type": "bar", "data": tmp_word}
      series_data.append(author_word)
    
    category = list(map(lambda x: x["week_string"], week_group))
    week_dict = {"legend": author_data, "category": category, "series": series_data}
    return week_dict
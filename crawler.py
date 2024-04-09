import time
from typing import List
import config
import threading
import traceback
import crawler_utils
from post_model import Post
from post_search_extractor import PostMobileSearchExtractor
from post_search_extractor import PostDesktopSearchExtractor
from post_search_extractor import LinkPostDesktopSearchExtractor
from post_search_extractor import PostSearchExFromLink, Test
from utils.log_utils import logger
from browser import WebBrowser
from account_utils import * #get_cookie_from_account_fb, update_account_to_local_json_file
from crawler_utils import *
from clawer_post_group import PostGroupExFromLink, PostsDesktopGroupExtractor, PostGroupDeskopExFromLink



class CrawlerThread(threading.Thread):
    def __init__(self, account, addition_data, mode = 0, mobile_device = False, **kwargs):
        threading.Thread.__init__(self)
        self.mode = mode
        self.mobile_device = mobile_device
        self.kwargs = kwargs
        self.account = account
        #self.keywords = keywords
        self.thread_name = "Thread_" + account.username
        self.is_active = False
        self.web_browser = None
        self.work_thread = None
        self.bCheckout = False
        array_data = addition_data.split("+")
        if len(array_data) > 2:
            self.proxy = addition_data.split("+")[2]
        else:
            self.proxy = None
        
    def run(self):
        print("Start clawer thread")
        try:
            #is_login = self.login() #mở cmt dòng này nếu login bằng cokie và 2fa
            is_login = self.login_with_userpass() #mở cmt dòng này nếu chỉ login bằng user, pass
            if is_login == 1:
                print("in duoc -----------")
                self.work()
        except Exception as ex:
            print(traceback.format_exc())
            print("Exception: run: " + str(ex))

    # [QUAN : 14/07/2023] -- Hàm login bằng user với pass 
    def login_with_userpass(self):
        self.web_browser = WebBrowser(proxy=self.account.proxy)
        self.web_browser.get_url(url=config.url_facebook)
        self.web_browser.login(self.account.username, self.account.password)
        time.sleep(config.time_wait_after_login_fb)
        if check_login(self.web_browser) == False:
            return 0
        elif check_nick_die(self.web_browser) == False:
            return 0
        self.is_active = True
        return 1

    def login(self):
        if not self.account.has_cookies():
            self.account.cookies = get_cookie_from_account_fb(account=self.account)

            update_account_to_local_json_file(account=self.account, file_path=config.account_path)
        time.sleep(2)

        print("Login accountFB: " + self.account.username)
        self.web_browser = WebBrowser(proxy=self.proxy)
        self.web_browser.get_url(url=config.url_facebook)
        result = self.web_browser.login_fb_with_cookie(self.account.get_cookies())
        # HoangLM: sua o day
        # result = self.web_browser.submit_2fakey_to_fb(297327)
        print("aaaa:", result)
        if result == 1:
            self.is_active = True
            return 1
        return 0

    def re_login(self):
        web_browser = WebBrowser(proxy=self.proxy)
        web_browser.get_url(url=config.url_facebook)
        web_browser.login_fb_with_cookie(cookie=self.account.get_cookies())
        return web_browser

    def on_post_available_callback(self, post: Post):
        with open("result.txt", "a", encoding="utf-8") as file:
            file.write(f"{str(post)}\n")
            # NguyenNH: in màu cho dễ debug
            if post.is_valid:
                file.write(f"🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷🇧🇷\n")
            else:
                file.write(f"🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈🎈\n")
    
    def work2(self):
        visit_url = "/" + "groups/1497469973862055"
        self.web_browser.driver.get("https://facebook.com" + visit_url)
        get_list_post_from_account(self.web_browser)

    def work(self):
        print("chuan bi in")
        
        while self.is_active:
            if self.mode == 1: 
                try:
                    logger.info(f"Crawler post search facebook")
                    print(self.kwargs['keywords'])
                    # #crawler post search facebook
                    for keyword in self.kwargs['keywords']:
                        if self.kwargs['mode_search'] == 'get_link':
                            link_post_search_extractor : LinkPostDesktopSearchExtractor = LinkPostDesktopSearchExtractor(driver=self.web_browser.driver, keyword=keyword,share_queue=self.kwargs['share_queue'])
                            link_post_search_extractor.start_get_link_posts()
                        elif self.kwargs['mode_search'] == 'ex_post':
                            post_search_extractor : PostSearchExFromLink = PostSearchExFromLink(driver=self.web_browser.driver,type="facebook search",keyword=keyword, keyword_noparse=self.kwargs['keyword_noparse'],share_queue=self.kwargs['share_queue'], callback=self.on_post_available_callback)
                            for posts in post_search_extractor.start():
                                logger.info(f"số bài post group đẩy qua kafka là {len(posts)}")
                                # crawler_utils.push_kafka(posts=posts, comments=None)
                except Exception as e:
                    logger.error(e)
            elif self.mode == 2:
                try:
                    ## extract post group
                    logger.info(f"Crawler post group facebook")
                    if self.kwargs['mode_group'] == "get_link":
                        posts_link_group : PostsDesktopGroupExtractor = PostsDesktopGroupExtractor(driver=self.web_browser.driver, group_id=self.kwargs['group_id'], share_queue=self.kwargs['share_queue'])
                        posts_link_group.start_get_link_posts()
                    elif self.kwargs['mode_group'] == "ex_post":
                        post_group_extractor : PostGroupDeskopExFromLink = PostGroupDeskopExFromLink(driver=self.web_browser.driver,type="facebook group", group_id = self.kwargs['group_id'], share_queue=self.kwargs['share_queue'], callback=self.on_post_available_callback)
                        for posts in post_group_extractor.start():
                            logger.info(f"số bài post group đẩy qua kafka là {len(posts)}")
                            # crawler_utils.push_kafka(posts=posts, comments=None)
                except Exception as e:
                    logger.error(e)
            else:
                logger.error("Error mode")     
              
            if self.bCheckout:
                break
            slepp_time = 60
            print(f"Dang sleep {slepp_time}s -- {self.thread_name}")
            time.sleep(slepp_time)
            print("Da xong 1 lan lam viec cua 1 tai khoan")


    def work_after_get_list_post(self, status_crawl, keyword):
        if status_crawl == config.crawl_complete_one_run:
            print("Hoan thanh lay tat ca bai viet cua tu khoa: " + str(keyword))
            pass
        elif status_crawl == config.crawl_re_login:
            print("Dang nhap lai")
            self.web_browser.driver.quit()
            self.web_browser = None
            self.web_browser = self.re_login()
            time.sleep(5)
        elif status_crawl == config.crawl_stop:
            print("Stop chuong trinh")
            self.web_browser.driver.quit()
            time.sleep(5)
            self.bCheckout = True

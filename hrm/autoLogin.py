"""
自动登录工具模块-提供HRM系统的自动登录功能
"""
import base64
import json
import logging
import time
import ddddocr
import requests
from io import BytesIO
from typing import Optional, Dict, List
from PIL import Image

# ============ 日志配置 ============
def setup_logger(name: str = "auto_login") -> logging.Logger:
    """配置日志记录器"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


logger = setup_logger()

# ============ 用户账号配置 ============
USER_ACCOUNTS = [
    {
        "name": "涂晓帆",
        "username": "112054",
        "password": "algo1129",
        "default": True
    },
    {
        "name": "董事长",
        "username": "100001",
        "password": "Admin@123",
        "default": False
    },
    {
        "name": "杨林",
        "username": "100025",
        "password": "Admin@123",
        "default": False
    }
]


class AuthService:
    """认证服务类 - 处理验证码获取和登录"""

    @staticmethod
    def get_captcha() -> dict:
        """
        获取验证码并自动识别

        返回: {
            'success': bool,
            'checkKey': str,
            'captcha': str,
            'image_base64': str,
            'message': str
        }
        """
        logger.info("=" * 60)
        logger.info("开始获取验证码流程")

        try:
            check_key = str(int(time.time() * 1000))
            captcha_url = f"https://hrm-apitest.whrhkj.com/sys/randomImage/{check_key}?_t={int(time.time())}"

            logger.info(f"生成checkKey: {check_key}")
            logger.info(f"验证码请求URL: {captcha_url}")

            start_time = time.time()
            response = requests.get(captcha_url, timeout=10)
            elapsed_time = time.time() - start_time

            logger.info(f"验证码接口响应状态码: {response.status_code}")
            logger.info(f"验证码接口响应时间: {elapsed_time:.3f}秒")

            result = response.json()
            logger.info(f"验证码接口响应code: {result.get('code')}")
            logger.info(f"验证码接口响应success: {result.get('success')}")

            if result.get('code') == 0 and result.get('success'):
                logger.info("验证码获取成功")
                img_data = result.get('result', '')

                if img_data.startswith('data:image/jpg;base64,'):
                    img_base64 = img_data.split(',')[1]
                    logger.info(f"Base64图片数据长度: {len(img_base64)}")

                    img_bytes = base64.b64decode(img_base64)
                    img = Image.open(BytesIO(img_bytes))
                    logger.info(f"图片尺寸: {img.size}")

                    logger.info("开始OCR识别验证码")
                    ocr_start = time.time()
                    ocr = ddddocr.DdddOcr(show_ad=False)
                    captcha_text = ocr.classification(img)
                    ocr_elapsed = time.time() - ocr_start

                    logger.info(f"OCR识别耗时: {ocr_elapsed:.3f}秒")
                    logger.info(f"OCR识别结果: {captcha_text}")
                    logger.info("验证码获取流程完成")
                    logger.info("=" * 60)

                    return {
                        'success': True,
                        'checkKey': check_key,
                        'captcha': captcha_text,
                        'image_base64': img_base64,
                        'message': "验证码获取成功"
                    }
                else:
                    logger.error(f"验证码接口返回格式异常")
                    logger.info("=" * 60)
                    return {
                        'success': False,
                        'message': "验证码接口返回格式异常"
                    }
            else:
                error_msg = result.get('message', '未知错误')
                logger.error(f"获取验证码失败: {error_msg}")
                logger.info("=" * 60)
                return {
                    'success': False,
                    'message': f"获取验证码失败：{error_msg}"
                }

        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求异常: {e}"
            logger.error(f"网络请求异常详情: {str(e)}")
            logger.exception(e)
            logger.info("=" * 60)
            return {'success': False, 'message': error_msg}
        except Exception as e:
            error_msg = f"验证码处理异常: {e}"
            logger.error(f"验证码处理异常详情: {str(e)}")
            logger.exception(e)
            logger.info("=" * 60)
            return {'success': False, 'message': error_msg}

    @staticmethod
    def login(username: str, password: str, captcha: str, check_key: str) -> dict:
        """
        用户登录

        返回: {
            'success': bool,
            'token': str,
            'userInfo': dict,
            'message': str
        }
        """
        logger.info("=" * 60)
        logger.info("开始用户登录流程")
        logger.info(f"登录用户名: {username}")
        logger.info(f"验证码: {captcha}")
        logger.info(f"checkKey: {check_key}")

        try:
            login_url = "https://hrm-apitest.whrhkj.com/user/login"
            login_data = {
                "username": username,
                "password": password,
                "captcha": captcha,
                "checkKey": check_key
            }

            logger.info(f"登录请求URL: {login_url}")
            logger.info(f"登录请求数据: {json.dumps(login_data, ensure_ascii=False)}")

            start_time = time.time()
            response = requests.post(login_url, json=login_data, timeout=10)
            elapsed_time = time.time() - start_time

            logger.info(f"登录接口响应状态码: {response.status_code}")
            logger.info(f"登录接口响应时间: {elapsed_time:.3f}秒")

            result = response.json()
            logger.info(f"登录接口响应success: {result.get('success')}")
            logger.info(f"登录接口响应message: {result.get('message')}")
            logger.info(f"登录接口完整响应: {json.dumps(result, ensure_ascii=False)}")

            if response.status_code == 200 and result.get('success', False):
                logger.info("登录成功")
                token = result.get('result', {}).get('token')
                user_info = result.get('result', {}).get('userInfo', {})
                logger.info(f"获取到的token: {token[:50]}..." if token else "token为空")
                logger.info(f"用户信息: {json.dumps(user_info, ensure_ascii=False)}")

                if token:
                    logger.info(f"登录成功，用户: {user_info.get('realname', username)}")
                    logger.info("=" * 60)
                    return {
                        'success': True,
                        'token': token,
                        'userInfo': user_info,
                        'message': f"登录成功，欢迎 {user_info.get('realname', username)}"
                    }
                else:
                    logger.error("登录响应中未找到Token")
                    logger.info("=" * 60)
                    return {
                        'success': False,
                        'message': "登录响应中未找到Token"
                    }
            else:
                error_msg = result.get('message', '未知错误')
                logger.error(f"登录失败: {error_msg}")
                logger.info("=" * 60)
                return {
                    'success': False,
                    'message': error_msg
                }

        except requests.exceptions.RequestException as e:
            error_msg = f"网络请求异常: {e}"
            logger.error(f"登录网络请求异常详情: {str(e)}")
            logger.exception(e)
            logger.info("=" * 60)
            return {'success': False, 'message': error_msg}
        except Exception as e:
            error_msg = f"登录处理异常: {e}"
            logger.error(f"登录处理异常详情: {str(e)}")
            logger.exception(e)
            logger.info("=" * 60)
            return {'success': False, 'message': error_msg}


class AutoLogin:
    """自动登录工具类"""

    def __init__(self, username: str = None, password: str = None):
        """
        初始化自动登录工具

        Args:
            username: 用户名（可选）
            password: 密码（可选）
        """
        self.username = username
        self.password = password
        self.auth_service = AuthService()
        self._login_result = None

    def set_credentials(self, username: str, password: str) -> 'AutoLogin':
        """设置登录凭证"""
        self.username = username
        self.password = password
        return self

    def set_user_by_name(self, name: str) -> 'AutoLogin':
        """通过姓名设置用户凭证"""
        for user in USER_ACCOUNTS:
            if user["name"] == name:
                self.username = user["username"]
                self.password = user["password"]
                return self
        raise ValueError(f"未找到用户: {name}")

    def set_default_user(self) -> 'AutoLogin':
        """使用默认用户（涂晓帆）"""
        for user in USER_ACCOUNTS:
            if user.get("default", False):
                self.username = user["username"]
                self.password = user["password"]
                return self
        # 如果没有默认用户，使用第一个
        if USER_ACCOUNTS:
            self.username = USER_ACCOUNTS[0]["username"]
            self.password = USER_ACCOUNTS[0]["password"]
        return self

    def get_user_info(self) -> Optional[Dict]:
        """获取当前登录的用户信息"""
        if self._login_result and self._login_result.get('success'):
            return self._login_result.get('userInfo')
        return None

    def get_token(self) -> Optional[str]:
        """获取当前登录的Token"""
        if self._login_result and self._login_result.get('success'):
            return self._login_result.get('token')
        return None

    def is_logged_in(self) -> bool:
        """检查是否已登录"""
        return self._login_result is not None and self._login_result.get('success', False)

    def login(self) -> dict:
        """
        执行自动登录

        返回: {
            'success': bool,
            'token': str,
            'userInfo': dict,
            'message': str
        }
        """
        if not self.username or not self.password:
            return {
                'success': False,
                'message': "未设置用户名或密码，请先调用 set_credentials() 或 set_user_by_name()"
            }

        logger.info("=" * 60)
        logger.info("开始执行自动登录流程")
        logger.info(f"登录用户: {self.username}")

        try:
            # 1. 获取验证码
            logger.info("步骤1: 获取验证码")
            captcha_result = self.auth_service.get_captcha()

            if not captcha_result.get('success'):
                error_msg = captcha_result.get('message', '获取验证码失败')
                logger.error(f"自动登录失败: {error_msg}")
                return {'success': False, 'message': error_msg}

            captcha_text = captcha_result.get('captcha')
            check_key = captcha_result.get('checkKey')

            logger.info(f"步骤1完成: 验证码获取成功, captcha={captcha_text}, checkKey={check_key}")

            # 2. 执行登录
            logger.info("步骤2: 执行登录")
            login_result = self.auth_service.login(
                self.username,
                self.password,
                captcha_text,
                check_key
            )

            if login_result.get('success'):
                self._login_result = login_result
                logger.info(f"自动登录成功: {login_result.get('userInfo', {}).get('realname', self.username)}")
            else:
                logger.error(f"自动登录失败: {login_result.get('message')}")

            logger.info("=" * 60)
            return login_result

        except Exception as e:
            error_msg = f"自动登录异常: {e}"
            logger.error(f"自动登录异常详情: {str(e)}")
            logger.exception(e)
            return {'success': False, 'message': error_msg}

    def login_and_get_token(self) -> Optional[str]:
        """
        登录并返回Token

        Returns:
            str: Token，登录失败返回None
        """
        result = self.login()
        if result.get('success'):
            return result.get('token')
        return None

    def login_and_get_userinfo(self) -> Optional[Dict]:
        """
        登录并返回用户信息

        Returns:
            dict: 用户信息，登录失败返回None
        """
        result = self.login()
        if result.get('success'):
            return result.get('userInfo')
        return None

    @staticmethod
    def quick_login(username: str, password: str) -> dict:
        """
        快速登录（静态方法）

        Args:
            username: 用户名
            password: 密码

        Returns:
            dict: 登录结果
        """
        auto_login = AutoLogin(username, password)
        return auto_login.login()

    @staticmethod
    def quick_login_by_name(name: str) -> dict:
        """
        通过姓名快速登录

        Args:
            name: 用户名

        Returns:
            dict: 登录结果
        """
        auto_login = AutoLogin()
        auto_login.set_user_by_name(name)
        return auto_login.login()

    @staticmethod
    def quick_login_default() -> dict:
        """使用默认用户快速登录"""
        auto_login = AutoLogin()
        auto_login.set_default_user()
        return auto_login.login()


# ============ 使用示例 ============
if __name__ == "__main__":
    # 示例1: 使用默认用户登录
    print("=== 示例1: 默认用户登录 ===")
    result = AutoLogin.quick_login_default()
    print(f"登录结果: {result.get('success')}")
    print(f"消息: {result.get('message')}")
    if result.get('success'):
        print(f"Token: {result.get('token')[:50]}...")
        print(f"用户: {result.get('userInfo', {}).get('realname')}")

    print("\n" + "=" * 60 + "\n")

    # 示例2: 通过姓名登录
    print("=== 示例2: 通过姓名登录 ===")
    result = AutoLogin.quick_login_by_name("董事长")
    print(f"登录结果: {result.get('success')}")
    print(f"消息: {result.get('message')}")

    print("\n" + "=" * 60 + "\n")

    # 示例3: 链式调用
    print("=== 示例3: 链式调用 ===")
    auto_login = AutoLogin()
    result = (auto_login
              .set_user_by_name("杨林")
              .login())
    print(f"登录结果: {result.get('success')}")
    print(f"消息: {result.get('message')}")

    print("\n" + "=" * 60 + "\n")

    # 示例4: 获取Token
    print("=== 示例4: 获取Token ===")
    token = AutoLogin().set_default_user().login_and_get_token()
    if token:
        print(f"Token: {token[:50]}...")
    else:
        print("获取Token失败")
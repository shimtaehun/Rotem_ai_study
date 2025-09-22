import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
import json
import logging
from datetime import datetime
import random
import threading
from queue import Queue

class TicketLinkMacro:
    def __init__(self, headless=False, auto_purchase=False, max_retry=3):
        """
        티켓링크 매크로 클래스
        
        Args:
            headless (bool): 브라우저를 백그라운드에서 실행할지 여부
            auto_purchase (bool): 자동 구매 여부
            max_retry (int): 최대 재시도 횟수
        """
        self.driver = None
        self.wait = None
        self.headless = headless
        self.auto_purchase = auto_purchase
        self.max_retry = max_retry
        self.purchase_queue = Queue()
        self.setup_logging()
        
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('ticket_macro.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_driver(self):
        """Chrome 드라이버 설정"""
        try:
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 10)
            
            self.logger.info("Chrome 드라이버가 성공적으로 설정되었습니다.")
            return True
            
        except Exception as e:
            self.logger.error(f"드라이버 설정 중 오류 발생: {e}")
            return False
    
    def login(self, username, password, login_url):
        """
        로그인 기능
        
        Args:
            username (str): 사용자명
            password (str): 비밀번호
            login_url (str): 로그인 페이지 URL
        """
        try:
            self.driver.get(login_url)
            self.logger.info(f"로그인 페이지 접속: {login_url}")
            
            # 로그인 폼 요소 찾기 (실제 사이트에 맞게 수정 필요)
            username_field = self.wait.until(
                EC.presence_of_element_located((By.NAME, "username"))
            )
            password_field = self.driver.find_element(By.NAME, "password")
            
            username_field.send_keys(username)
            password_field.send_keys(password)
            
            # 로그인 버튼 클릭
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            self.logger.info("로그인 시도 완료")
            
            # 로그인 성공 확인
            time.sleep(3)
            if "dashboard" in self.driver.current_url or "mypage" in self.driver.current_url:
                self.logger.info("로그인 성공!")
                return True
            else:
                self.logger.warning("로그인 실패 또는 확인 필요")
                return False
                
        except TimeoutException:
            self.logger.error("로그인 페이지 로딩 시간 초과")
            return False
        except NoSuchElementException as e:
            self.logger.error(f"로그인 요소를 찾을 수 없습니다: {e}")
            return False
        except Exception as e:
            self.logger.error(f"로그인 중 오류 발생: {e}")
            return False
    
    def search_tickets(self, search_url, search_params):
        """
        티켓 검색 기능
        
        Args:
            search_url (str): 검색 페이지 URL
            search_params (dict): 검색 조건
        """
        try:
            self.driver.get(search_url)
            self.logger.info(f"검색 페이지 접속: {search_url}")
            
            # 검색 조건 입력 (실제 사이트에 맞게 수정 필요)
            if 'date' in search_params:
                date_field = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "date"))
                )
                date_field.send_keys(search_params['date'])
            
            if 'location' in search_params:
                location_field = self.driver.find_element(By.NAME, "location")
                location_field.send_keys(search_params['location'])
            
            if 'category' in search_params:
                category_select = self.driver.find_element(By.NAME, "category")
                category_select.send_keys(search_params['category'])
            
            # 검색 버튼 클릭
            search_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            search_button.click()
            
            self.logger.info("티켓 검색 완료")
            time.sleep(2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"티켓 검색 중 오류 발생: {e}")
            return False
    
    def get_available_tickets(self):
        """사용 가능한 티켓 목록 가져오기"""
        try:
            # 티켓 목록 요소 찾기 (실제 사이트에 맞게 수정 필요)
            ticket_elements = self.driver.find_elements(By.CLASS_NAME, "ticket-item")
            
            tickets = []
            for ticket in ticket_elements:
                try:
                    title = ticket.find_element(By.CLASS_NAME, "title").text
                    price = ticket.find_element(By.CLASS_NAME, "price").text
                    date = ticket.find_element(By.CLASS_NAME, "date").text
                    location = ticket.find_element(By.CLASS_NAME, "location").text
                    
                    tickets.append({
                        'title': title,
                        'price': price,
                        'date': date,
                        'location': location
                    })
                except NoSuchElementException:
                    continue
            
            self.logger.info(f"총 {len(tickets)}개의 티켓을 찾았습니다.")
            return tickets
            
        except Exception as e:
            self.logger.error(f"티켓 목록 가져오기 중 오류 발생: {e}")
            return []
    
    def select_ticket(self, ticket_index=0):
        """티켓 선택"""
        try:
            ticket_elements = self.driver.find_elements(By.CLASS_NAME, "ticket-item")
            if ticket_index < len(ticket_elements):
                ticket_elements[ticket_index].click()
                self.logger.info(f"티켓 {ticket_index + 1} 선택 완료")
                return True
            else:
                self.logger.warning("선택할 티켓이 없습니다.")
                return False
                
        except Exception as e:
            self.logger.error(f"티켓 선택 중 오류 발생: {e}")
            return False
    
    def human_like_delay(self, min_delay=0.5, max_delay=2.0):
        """사람처럼 랜덤한 지연 시간 생성"""
        delay = random.uniform(min_delay, max_delay)
        time.sleep(delay)
    
    def safe_click(self, element, retry_count=3):
        """안전한 클릭 (요소가 클릭 가능할 때까지 대기)"""
        for attempt in range(retry_count):
            try:
                # 요소가 클릭 가능할 때까지 대기
                WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable(element)
                )
                
                # 스크롤하여 요소가 보이도록 함
                self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                self.human_like_delay(0.5, 1.0)
                
                # ActionChains를 사용한 클릭
                ActionChains(self.driver).move_to_element(element).click().perform()
                return True
                
            except ElementClickInterceptedException:
                self.logger.warning(f"클릭 시도 {attempt + 1} 실패 - 요소가 가려짐")
                if attempt < retry_count - 1:
                    self.human_like_delay(1, 2)
                    continue
            except Exception as e:
                self.logger.warning(f"클릭 시도 {attempt + 1} 실패: {e}")
                if attempt < retry_count - 1:
                    self.human_like_delay(1, 2)
                    continue
        
        return False
    
    def fill_payment_info(self, payment_info):
        """결제 정보 입력"""
        try:
            self.logger.info("결제 정보 입력 시작")
            
            # 카드 번호 입력
            if 'card_number' in payment_info:
                card_field = self.wait.until(
                    EC.presence_of_element_located((By.NAME, "cardNumber"))
                )
                card_field.clear()
                card_field.send_keys(payment_info['card_number'])
                self.human_like_delay(0.5, 1.0)
            
            # 만료일 입력
            if 'expiry_date' in payment_info:
                expiry_field = self.driver.find_element(By.NAME, "expiryDate")
                expiry_field.clear()
                expiry_field.send_keys(payment_info['expiry_date'])
                self.human_like_delay(0.5, 1.0)
            
            # CVV 입력
            if 'cvv' in payment_info:
                cvv_field = self.driver.find_element(By.NAME, "cvv")
                cvv_field.clear()
                cvv_field.send_keys(payment_info['cvv'])
                self.human_like_delay(0.5, 1.0)
            
            # 카드 소유자명 입력
            if 'cardholder_name' in payment_info:
                name_field = self.driver.find_element(By.NAME, "cardholderName")
                name_field.clear()
                name_field.send_keys(payment_info['cardholder_name'])
                self.human_like_delay(0.5, 1.0)
            
            self.logger.info("결제 정보 입력 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"결제 정보 입력 중 오류 발생: {e}")
            return False
    
    def select_seat(self, seat_preference="best"):
        """좌석 선택"""
        try:
            self.logger.info(f"좌석 선택 시작 - 선호도: {seat_preference}")
            
            # 좌석 선택 페이지 로딩 대기
            time.sleep(3)
            
            # 좌석 선택 로직 (실제 사이트에 맞게 수정 필요)
            if seat_preference == "best":
                # 최고 등급 좌석 선택
                best_seats = self.driver.find_elements(By.CLASS_NAME, "premium-seat")
                if best_seats:
                    self.safe_click(best_seats[0])
                    self.human_like_delay(1, 2)
            elif seat_preference == "cheapest":
                # 가장 저렴한 좌석 선택
                cheap_seats = self.driver.find_elements(By.CLASS_NAME, "economy-seat")
                if cheap_seats:
                    self.safe_click(cheap_seats[0])
                    self.human_like_delay(1, 2)
            else:
                # 랜덤 좌석 선택
                available_seats = self.driver.find_elements(By.CLASS_NAME, "available-seat")
                if available_seats:
                    random_seat = random.choice(available_seats)
                    self.safe_click(random_seat)
                    self.human_like_delay(1, 2)
            
            # 좌석 선택 확인
            confirm_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '선택완료')]"))
            )
            self.safe_click(confirm_button)
            
            self.logger.info("좌석 선택 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"좌석 선택 중 오류 발생: {e}")
            return False
    
    def book_ticket(self, payment_info=None, seat_preference="best"):
        """티켓 예약 (고급 기능 포함)"""
        try:
            self.logger.info("티켓 예약 프로세스 시작")
            
            # 1단계: 예약 버튼 클릭
            book_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '예약') or contains(text(), '구매')]"))
            )
            self.safe_click(book_button)
            self.human_like_delay(2, 3)
            
            # 2단계: 좌석 선택
            if not self.select_seat(seat_preference):
                self.logger.error("좌석 선택 실패")
                return False
            
            # 3단계: 수량 선택
            if not self.select_quantity():
                self.logger.error("수량 선택 실패")
                return False
            
            # 4단계: 결제 정보 입력 (자동 구매 모드인 경우)
            if self.auto_purchase and payment_info:
                if not self.fill_payment_info(payment_info):
                    self.logger.error("결제 정보 입력 실패")
                    return False
            
            # 5단계: 최종 확인 및 결제
            if self.auto_purchase:
                return self.process_payment()
            else:
                return self.confirm_reservation()
                
        except Exception as e:
            self.logger.error(f"티켓 예약 중 오류 발생: {e}")
            return False
    
    def select_quantity(self, quantity=1):
        """수량 선택"""
        try:
            # 수량 선택 드롭다운 또는 버튼 찾기
            quantity_selectors = [
                "//select[@name='quantity']",
                "//input[@name='quantity']",
                "//button[contains(@class, 'quantity')]"
            ]
            
            for selector in quantity_selectors:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    if element.tag_name == "select":
                        select = Select(element)
                        select.select_by_value(str(quantity))
                    elif element.tag_name == "input":
                        element.clear()
                        element.send_keys(str(quantity))
                    else:
                        # 버튼인 경우 클릭으로 수량 조절
                        for _ in range(quantity - 1):
                            self.safe_click(element)
                            self.human_like_delay(0.5, 1.0)
                    
                    self.logger.info(f"수량 {quantity}개 선택 완료")
                    return True
                except NoSuchElementException:
                    continue
            
            self.logger.warning("수량 선택 요소를 찾을 수 없습니다. 기본값 사용")
            return True
            
        except Exception as e:
            self.logger.error(f"수량 선택 중 오류 발생: {e}")
            return False
    
    def process_payment(self):
        """결제 처리"""
        try:
            self.logger.info("결제 처리 시작")
            
            # 결제 버튼 클릭
            payment_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '결제') or contains(text(), '구매')]"))
            )
            self.safe_click(payment_button)
            self.human_like_delay(2, 3)
            
            # 결제 완료 확인
            success_indicators = [
                "//div[contains(text(), '결제완료')]",
                "//div[contains(text(), '구매완료')]",
                "//div[contains(text(), '성공')]"
            ]
            
            for indicator in success_indicators:
                try:
                    success_element = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, indicator))
                    )
                    if success_element:
                        self.logger.info("결제 성공!")
                        return True
                except TimeoutException:
                    continue
            
            # URL로 성공 확인
            if any(keyword in self.driver.current_url.lower() for keyword in ['success', 'complete', 'confirm']):
                self.logger.info("결제 성공! (URL 확인)")
                return True
            
            self.logger.warning("결제 상태 확인 필요")
            return False
            
        except Exception as e:
            self.logger.error(f"결제 처리 중 오류 발생: {e}")
            return False
    
    def confirm_reservation(self):
        """예약 확인 (자동 구매가 아닌 경우)"""
        try:
            self.logger.info("예약 확인 프로세스")
            
            # 예약 확인 버튼 클릭
            confirm_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), '확인') or contains(text(), '예약')]"))
            )
            self.safe_click(confirm_button)
            self.human_like_delay(2, 3)
            
            # 예약 완료 확인
            if any(keyword in self.driver.current_url.lower() for keyword in ['reservation', 'booking', 'confirm']):
                self.logger.info("예약 성공!")
                return True
            else:
                self.logger.warning("예약 상태 확인 필요")
                return False
                
        except Exception as e:
            self.logger.error(f"예약 확인 중 오류 발생: {e}")
            return False
    
    def auto_retry_booking(self, max_attempts=5):
        """자동 재시도 예약"""
        for attempt in range(max_attempts):
            self.logger.info(f"예약 시도 {attempt + 1}/{max_attempts}")
            
            try:
                # 페이지 새로고침
                self.driver.refresh()
                self.human_like_delay(2, 3)
                
                # 다시 티켓 검색
                if self.get_available_tickets():
                    if self.select_ticket(0):
                        if self.book_ticket():
                            self.logger.info("예약 성공!")
                            return True
                
                # 실패 시 대기
                if attempt < max_attempts - 1:
                    wait_time = random.uniform(5, 10)
                    self.logger.info(f"{wait_time:.1f}초 후 재시도...")
                    time.sleep(wait_time)
                    
            except Exception as e:
                self.logger.error(f"재시도 {attempt + 1} 중 오류: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(5)
        
        self.logger.error("모든 예약 시도 실패")
        return False
    
    def run_macro(self, config_file="config.json"):
        """매크로 실행 (고급 기능 포함)"""
        try:
            # 설정 파일 로드
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 드라이버 설정
            if not self.setup_driver():
                return False
            
            # 로그인
            if not self.login(config['username'], config['password'], config['login_url']):
                return False
            
            # 티켓 검색
            if not self.search_tickets(config['search_url'], config['search_params']):
                return False
            
            # 사용 가능한 티켓 확인
            tickets = self.get_available_tickets()
            if not tickets:
                self.logger.warning("사용 가능한 티켓이 없습니다.")
                return False
            
            # 티켓 정보 출력
            self.logger.info("=== 사용 가능한 티켓 목록 ===")
            for i, ticket in enumerate(tickets):
                self.logger.info(f"{i+1}. {ticket['title']} - {ticket['price']} - {ticket['date']}")
            
            # 첫 번째 티켓 선택
            if not self.select_ticket(0):
                return False
            
            # 결제 정보 설정
            payment_info = config.get('payment_info', None)
            seat_preference = config.get('seat_preference', 'best')
            
            # 티켓 예약/구매
            if self.auto_purchase and payment_info:
                success = self.book_ticket(payment_info, seat_preference)
            else:
                success = self.book_ticket(seat_preference=seat_preference)
            
            if not success:
                # 자동 재시도
                if config.get('auto_retry', False):
                    self.logger.info("자동 재시도 모드 활성화")
                    success = self.auto_retry_booking(config.get('max_retry_attempts', 5))
            
            if success:
                self.logger.info("매크로 실행 완료!")
                return True
            else:
                self.logger.error("매크로 실행 실패")
                return False
            
        except FileNotFoundError:
            self.logger.error(f"설정 파일을 찾을 수 없습니다: {config_file}")
            return False
        except Exception as e:
            self.logger.error(f"매크로 실행 중 오류 발생: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
    
    def run_scheduled_macro(self, config_file="config.json", schedule_time=None):
        """예약된 시간에 매크로 실행"""
        if schedule_time:
            self.logger.info(f"매크로가 {schedule_time}에 실행되도록 예약되었습니다.")
            # 실제 구현에서는 스케줄러를 사용
            pass
        
        return self.run_macro(config_file)
    
    def monitor_tickets(self, config_file="config.json", check_interval=30):
        """티켓 모니터링 (지속적으로 확인)"""
        try:
            self.logger.info("티켓 모니터링 시작")
            
            while True:
                try:
                    # 설정 파일 다시 로드
                    with open(config_file, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    # 드라이버가 없으면 설정
                    if not self.driver:
                        if not self.setup_driver():
                            time.sleep(check_interval)
                            continue
                    
                    # 로그인 확인
                    if not self.is_logged_in():
                        if not self.login(config['username'], config['password'], config['login_url']):
                            time.sleep(check_interval)
                            continue
                    
                    # 티켓 검색
                    if self.search_tickets(config['search_url'], config['search_params']):
                        tickets = self.get_available_tickets()
                        if tickets:
                            self.logger.info(f"새로운 티켓 발견! {len(tickets)}개")
                            
                            # 자동 구매 설정이 있으면 즉시 구매
                            if config.get('auto_purchase', False):
                                if self.select_ticket(0):
                                    payment_info = config.get('payment_info', None)
                                    if self.book_ticket(payment_info):
                                        self.logger.info("자동 구매 완료!")
                                        break
                    
                    self.logger.info(f"{check_interval}초 후 다시 확인...")
                    time.sleep(check_interval)
                    
                except Exception as e:
                    self.logger.error(f"모니터링 중 오류: {e}")
                    time.sleep(check_interval)
                    
        except KeyboardInterrupt:
            self.logger.info("모니터링 중단됨")
        finally:
            if self.driver:
                self.driver.quit()
    
    def is_logged_in(self):
        """로그인 상태 확인"""
        try:
            # 로그인 상태를 확인하는 요소 찾기
            login_indicators = [
                "//a[contains(text(), '로그아웃')]",
                "//a[contains(text(), '마이페이지')]",
                "//div[contains(@class, 'user-info')]"
            ]
            
            for indicator in login_indicators:
                try:
                    element = self.driver.find_element(By.XPATH, indicator)
                    if element:
                        return True
                except NoSuchElementException:
                    continue
            
            return False
            
        except Exception:
            return False
    
    def close(self):
        """드라이버 종료"""
        if self.driver:
            self.driver.quit()
            self.logger.info("드라이버가 종료되었습니다.")

def create_config_file():
    """설정 파일 생성 (고급 기능 포함)"""
    config = {
        "username": "your_username",
        "password": "your_password",
        "login_url": "https://example.com/login",
        "search_url": "https://example.com/search",
        "search_params": {
            "date": "2024-01-01",
            "location": "서울",
            "category": "콘서트"
        },
        "auto_purchase": False,
        "seat_preference": "best",
        "auto_retry": True,
        "max_retry_attempts": 5,
        "payment_info": {
            "card_number": "1234567890123456",
            "expiry_date": "12/25",
            "cvv": "123",
            "cardholder_name": "홍길동"
        },
        "monitoring": {
            "enabled": False,
            "check_interval": 30
        }
    }
    
    with open("config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print("config.json 파일이 생성되었습니다. 설정을 수정해주세요.")
    print("\n=== 설정 가이드 ===")
    print("1. username, password: 로그인 정보")
    print("2. login_url, search_url: 대상 사이트 URL")
    print("3. search_params: 검색 조건")
    print("4. auto_purchase: 자동 구매 여부 (true/false)")
    print("5. seat_preference: 좌석 선호도 (best/cheapest/random)")
    print("6. auto_retry: 자동 재시도 여부")
    print("7. payment_info: 결제 정보 (자동 구매 시 필요)")
    print("8. monitoring: 모니터링 설정")

def main():
    """메인 실행 함수"""
    print("=== 티켓링크 자동 예약/구매 매크로 ===")
    print("1. 일반 예약 모드")
    print("2. 자동 구매 모드")
    print("3. 모니터링 모드")
    print("4. 설정 파일 생성")
    
    choice = input("\n모드를 선택하세요 (1-4): ").strip()
    
    # 설정 파일이 없으면 생성
    try:
        with open("config.json", "r"):
            pass
    except FileNotFoundError:
        create_config_file()
        print("\n먼저 config.json 파일을 수정해주세요.")
        return
    
    if choice == "1":
        # 일반 예약 모드
        macro = TicketLinkMacro(headless=False, auto_purchase=False)
        try:
            success = macro.run_macro()
            if success:
                print("예약이 성공적으로 완료되었습니다!")
            else:
                print("예약에 실패했습니다.")
        finally:
            macro.close()
    
    elif choice == "2":
        # 자동 구매 모드
        macro = TicketLinkMacro(headless=False, auto_purchase=True)
        try:
            success = macro.run_macro()
            if success:
                print("자동 구매가 성공적으로 완료되었습니다!")
            else:
                print("자동 구매에 실패했습니다.")
        finally:
            macro.close()
    
    elif choice == "3":
        # 모니터링 모드
        macro = TicketLinkMacro(headless=False, auto_purchase=True)
        try:
            print("모니터링 모드를 시작합니다. Ctrl+C로 중단할 수 있습니다.")
            macro.monitor_tickets()
        except KeyboardInterrupt:
            print("\n모니터링이 중단되었습니다.")
        finally:
            macro.close()
    
    elif choice == "4":
        # 설정 파일 생성
        create_config_file()
    
    else:
        print("잘못된 선택입니다.")

if __name__ == "__main__":
    main()

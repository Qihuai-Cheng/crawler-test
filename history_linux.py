import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd

# 设置浏览器选项（Linux Server）
def setup_browser(chromedriver_path=None):
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-images")
    options.add_argument("--user-data-dir=/tmp/chrome_user_data")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument(
        "user-agent=Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0 Safari/537.36"
    )

    # 自动下载或使用指定 chromedriver
    if chromedriver_path:
        service = ChromeService(chromedriver_path)
    else:
        service = ChromeService(ChromeDriverManager().install())

    driver = webdriver.Chrome(service=service, options=options)

    # 隐藏自动化标识
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        delete navigator.__proto__.webdriver;
        window.chrome = {runtime: {}};
        """
    })
    return driver

# 等待元素可点击
def wait_for_clickable(driver, by, value, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable((by, value))
    )

# 等待元素存在
def wait_for_presence(driver, by, value, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )

# 解析表格数据
def parse_table_data(driver):
    try:
        table = wait_for_presence(driver, By.ID, "archiveTable")
        rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # 跳过表头
        headers = [
            '日期', '时间', '温度°C', '气象站大气压mmHg', '平均海平面大气压mmHg',
            '气压趋势mmHg', '相对湿度%', '风向', '平均风速m/s', '10分钟最大阵风m/s',
            '两次观测间最大阵风m/s', '总云量', '天气', '过去天气1', '过去天气2',
            '最低气温°C', '最高气温°C', '云层类型', '云量', '最低云层高度m',
            '高积云等', '卷云等', '水平能见度km', '露点温度°C', '降水量mm',
            '降水时间', '土壤状况', '夜间土壤最低温°C', '雪深cm'
        ]

        data = []
        current_date = None

        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if not cols:
                continue

            date_cell = row.find_elements(By.CLASS_NAME, "cl_dt")
            if date_cell:
                current_date = date_cell[0].text.strip()
            else:
                time_cell = ''
                try:
                    if len(cols) > 0:
                        dfs = cols[0].find_element(By.CLASS_NAME, "dfs")
                        time_cell = dfs.text.strip()
                except Exception:
                    pass

                if not current_date or not time_cell:
                    continue

                # 提取所有字段（容错版）
                def safe_get(col_idx, cls=None):
                    try:
                        col = cols[col_idx]
                        return col.find_element(By.CLASS_NAME, cls).text.strip() \
                            if cls and col.find_elements(By.CLASS_NAME, cls) \
                            else col.text.strip()
                    except Exception:
                        return ''

                temperature   = safe_get(2, "t_0")
                po            = safe_get(3, "p_0")
                p             = safe_get(4, "p_0")
                pa            = safe_get(5, "p_0")
                humidity      = safe_get(6)
                wind_dir      = safe_get(7)
                wind_speed    = safe_get(8, "wv_0")
                wind_gust_10  = safe_get(9, "wv_0")
                wind_gust_3   = safe_get(10, "wv_0")
                cloudiness    = safe_get(11)
                weather       = safe_get(12)
                weather1      = safe_get(13)
                weather2      = safe_get(14)
                min_temp      = safe_get(15, "t_0")
                max_temp      = safe_get(16, "t_0")
                cloud_type    = safe_get(17)
                cloud_amount  = safe_get(18)
                cloud_height  = safe_get(19)
                cloud_higher  = safe_get(20)
                cirrus        = safe_get(21)
                visibility    = safe_get(22, "vv_0")
                dew_point     = safe_get(23, "t_0")
                precipitation = safe_get(24, "pr_0")
                precipitation_time = safe_get(25)
                soil_condition = safe_get(26)
                soil_min_temp = safe_get(27, "t_0")
                snow_depth    = safe_get(29, "vv_0")

                data.append([
                    current_date, time_cell, temperature, po, p, pa, humidity,
                    wind_dir, wind_speed, wind_gust_10, wind_gust_3,
                    cloudiness, weather, weather1, weather2,
                    min_temp, max_temp, cloud_type, cloud_amount,
                    cloud_height, cloud_higher, cirrus, visibility,
                    dew_point, precipitation, precipitation_time,
                    soil_condition, soil_min_temp, snow_depth
                ])

        return pd.DataFrame(data, columns=headers)
    except Exception as e:
        print(f"解析表格失败: {e}")
        return pd.DataFrame(columns=headers)

# 主程序入口
def main():
    url = "https://rp5.ru/%E5%8D%97%E4%BA%AC%E5%B8%82(%E6%9C%BA%E5%9C%BA)%E5%8E%86%E5%8F%B2%E5%A4%A9%E6%B0%94_"
    chromedriver_path = None  # Linux 下自动下载
    driver = setup_browser(chromedriver_path)

    try:
        driver.get(url)
        print("等待页面加载完成...")
        wait_for_presence(driver, By.TAG_NAME, "body")

        print("切换到‘查阅历史天气’标签...")
        archive_tab = wait_for_clickable(driver, By.ID, "tabSynopArchive")
        driver.execute_script("arguments[0].click();", archive_tab)
        time.sleep(2)

        print("等待表格加载...")
        wait_for_presence(driver, By.ID, "archiveTable")

        print("点击‘仅最近7天’按钮...")
        seven_days_label = wait_for_clickable(driver, By.XPATH, '//label[@id="input_radio" and contains(., "7天")]')
        driver.execute_script("arguments[0].click();", seven_days_label)
        time.sleep(2)

        print("点击‘选择’按钮...")
        select_button = wait_for_clickable(driver, By.CSS_SELECTOR, "div.archButton > div.inner")
        driver.execute_script("arguments[0].click();", select_button)
        time.sleep(5)

        df = parse_table_data(driver)

        if not df.empty:
            df.to_excel("南京机场天气数据.xlsx", index=False)
            print("✅ 数据已保存到 '南京机场天气数据.xlsx'")
        else:
            print("❌ 未解析到任何数据")

    except Exception as e:
        print(f"❌ 发生错误: {e}")
    finally:
        driver.quit()

if __name__ == '__main__':
    main()

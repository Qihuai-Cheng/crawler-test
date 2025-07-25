import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd

# 设置浏览器选项（Linux Server）
def setup_browser(chromedriver_path):
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--headless")  # 无头模式
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-images")
    options.add_argument("--disable-javascript")
    options.add_argument("--user-data-dir=/tmp/chrome_user_data")  # 显式指定 user-data-dir
    options.add_argument("--remote-debugging-port=9222")  # 避免端口冲突
    options.add_argument("user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0 Safari/537.36")

    # 如果 chromedriver_path 为 None，则自动下载
    if chromedriver_path:
        service = Service(chromedriver_path)
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
        # 显式等待表格加载
        table = wait_for_presence(driver, By.ID, "archiveTable")
        rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # 跳过表头
        if not rows:
            print("❌ 表格中未找到数据行")
            return pd.DataFrame(columns=headers)

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

            # 提取日期单元格（rowspan）
            date_cell = row.find_elements(By.CLASS_NAME, "cl_dt")
            if date_cell:
                current_date = date_cell[0].text.strip()
            else:
                # 提取时间单元格
                time_cell = ''
                try:
                    if len(cols) > 0:
                        dfs = cols[0].find_element(By.CLASS_NAME, "dfs")
                        time_cell = dfs.text.strip()
                except: pass

                if not current_date or not time_cell:
                    continue  # 确保日期和时间有效

                # ✅ 每个字段独立提取（避免字段未定义）
                try:
                    temperature = cols[2].find_element(By.CLASS_NAME, "t_0").text.strip() if len(cols) > 2 and cols[2].find_elements(By.CLASS_NAME, "t_0") else ''
                except:
                    temperature = ''

                try:
                    po = cols[3].find_element(By.CLASS_NAME, "p_0").text.strip() if len(cols) > 3 and cols[3].find_elements(By.CLASS_NAME, "p_0") else ''
                except:
                    po = ''

                try:
                    p = cols[4].find_element(By.CLASS_NAME, "p_0").text.strip() if len(cols) > 4 and cols[4].find_elements(By.CLASS_NAME, "p_0") else ''
                except:
                    p = ''

                try:
                    pa = cols[5].find_element(By.CLASS_NAME, "p_0").text.strip() if len(cols) > 5 and cols[5].find_elements(By.CLASS_NAME, "p_0") else ''
                except:
                    pa = ''

                try:
                    humidity = cols[6].text.strip() if len(cols) > 6 else ''
                except:
                    humidity = ''

                try:
                    wind_dir = cols[7].text.strip() if len(cols) > 7 else ''
                except:
                    wind_dir = ''

                try:
                    wind_speed = cols[8].find_element(By.CLASS_NAME, "wv_0").text.strip() if len(cols) > 8 and cols[8].find_elements(By.CLASS_NAME, "wv_0") else ''
                except:
                    wind_speed = ''

                try:
                    wind_gust_10 = cols[9].find_element(By.CLASS_NAME, "wv_0").text.strip() if len(cols) > 9 and cols[9].find_elements(By.CLASS_NAME, "wv_0") else ''
                except:
                    wind_gust_10 = ''

                try:
                    wind_gust_3 = cols[10].find_element(By.CLASS_NAME, "wv_0").text.strip() if len(cols) > 10 and cols[10].find_elements(By.CLASS_NAME, "wv_0") else ''
                except:
                    wind_gust_3 = ''

                try:
                    cloudiness = cols[11].text.strip() if len(cols) > 11 else ''
                except:
                    cloudiness = ''

                try:
                    weather = cols[12].text.strip() if len(cols) > 12 else ''
                except:
                    weather = ''

                try:
                    weather1 = cols[13].text.strip() if len(cols) > 13 else ''
                except:
                    weather1 = ''

                try:
                    weather2 = cols[14].text.strip() if len(cols) > 14 else ''
                except:
                    weather2 = ''

                try:
                    min_temp = cols[15].find_element(By.CLASS_NAME, "t_0").text.strip() if len(cols) > 15 and cols[15].find_elements(By.CLASS_NAME, "t_0") else ''
                except:
                    min_temp = ''

                try:
                    max_temp = cols[16].find_element(By.CLASS_NAME, "t_0").text.strip() if len(cols) > 16 and cols[16].find_elements(By.CLASS_NAME, "t_0") else ''
                except:
                    max_temp = ''

                try:
                    cloud_type = cols[17].text.strip() if len(cols) > 17 else ''
                except:
                    cloud_type = ''

                try:
                    cloud_amount = cols[18].text.strip() if len(cols) > 18 else ''
                except:
                    cloud_amount = ''

                try:
                    cloud_height = cols[19].text.strip() if len(cols) > 19 else ''
                except:
                    cloud_height = ''

                try:
                    cloud_higher = cols[20].text.strip() if len(cols) > 20 else ''
                except:
                    cloud_higher = ''

                try:
                    cirrus = cols[21].text.strip() if len(cols) > 21 else ''
                except:
                    cirrus = ''

                try:
                    visibility = cols[22].find_element(By.CLASS_NAME, "vv_0").text.strip() if len(cols) > 22 and cols[22].find_elements(By.CLASS_NAME, "vv_0") else ''
                except:
                    visibility = ''

                try:
                    dew_point = cols[23].find_element(By.CLASS_NAME, "t_0").text.strip() if len(cols) > 23 and cols[23].find_elements(By.CLASS_NAME, "t_0") else ''
                except:
                    dew_point = ''

                try:
                    precipitation = cols[24].find_element(By.CLASS_NAME, "pr_0").text.strip() if len(cols) > 24 and cols[24].find_elements(By.CLASS_NAME, "pr_0") else ''
                except:
                    precipitation = ''

                try:
                    precipitation_time = cols[25].text.strip() if len(cols) > 25 else ''
                except:
                    precipitation_time = ''

                try:
                    soil_condition = cols[26].text.strip() if len(cols) > 26 else ''
                except:
                    soil_condition = ''

                try:
                    soil_min_temp = cols[27].find_element(By.CLASS_NAME, "t_0").text.strip() if len(cols) > 27 and cols[27].find_elements(By.CLASS_NAME, "t_0") else ''
                except:
                    soil_min_temp = ''

                try:
                    snow_depth = cols[29].find_element(By.CLASS_NAME, "vv_0").text.strip() if len(cols) > 29 and cols[29].find_elements(By.CLASS_NAME, "vv_0") else ''
                except:
                    snow_depth = ''

                # 添加当前行数据
                data.append([
                    current_date, time_cell, temperature, po, p, pa, humidity, wind_dir,
                    wind_speed, wind_gust_10, wind_gust_3, cloudiness, weather, weather1,
                    weather2, min_temp, max_temp, cloud_type, cloud_amount, cloud_height,
                    cloud_higher, cirrus, visibility, dew_point, precipitation, precipitation_time,
                    soil_condition, soil_min_temp, snow_depth
                ])

        return pd.DataFrame(data, columns=headers)
    except Exception as e:
        print(f"解析表格失败: {e}")
        return pd.DataFrame(columns=headers)

# 主程序入口
def main():
    url = "https://rp5.ru/%E5%8D%97%E4%BA%AC%E5%B8%82(%E6%9C%BA%E5%9C%BA)%E5%8E%86%E5%8F%B2%E5%A4%A9%E6%B0%94_"
    chromedriver_path = None # Linux 下让 Selenium Manager 自动下载 chromedriver
    driver = setup_browser(chromedriver_path)

    try:
        driver.get(url)

        # 等待页面加载完成
        print("等待页面加载完成...")
        wait_for_presence(driver, By.TAG_NAME, "body")

        # 切换到“查阅历史天气”标签页
        print("切换到‘查阅历史天气’标签...")
        archive_tab = wait_for_clickable(driver, By.ID, "tabSynopArchive")
        driver.execute_script("arguments[0].click();", archive_tab)
        time.sleep(2)

        # 等待表格加载
        print("等待表格加载...")
        wait_for_presence(driver, By.ID, "archiveTable")

        # 点击“仅最近7天”按钮（保持原逻辑）
        print("点击‘仅最近7天’按钮...")
        seven_days_label = wait_for_clickable(driver, By.XPATH, '//label[@id="input_radio" and contains(., "7天")]')
        driver.execute_script("arguments[0].click();", seven_days_label)
        time.sleep(2)

        # ✅ 新增：精准定位并点击“选择”按钮
        print("点击‘选择’按钮...")
        # 使用 CSS 选择器定位：外层 div.archButton 内的 div.inner
        select_button = wait_for_clickable(driver, By.CSS_SELECTOR, "div.archButton > div.inner")
        driver.execute_script("arguments[0].click();", select_button)
        time.sleep(5)  # 等待数据加载

        # 解析数据（保持不变）
        df = parse_table_data(driver)

        # 保存为 Excel（保持不变）
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

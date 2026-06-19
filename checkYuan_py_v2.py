import re
import yfinance as yf

def convert_yfinance():
    # The symbol for the KRW to CNY exchange rate in Yahoo Finance
    symbol = "CNYKRW=X"
    # Fetch data
    krw_cny = yf.Ticker(symbol)
    # Fetch the latest close price, which reflects the latest exchange rate
    hist = krw_cny.history(period="1d")
    latest_exchange_rate = hist['Close'].iloc[-1]  # Get the last closing price
    return latest_exchange_rate

def checkYuan(trText):
    global CNY_KRW_RT
    CNY_KRW_RT = 0
    # myPattern = re.compile(r'(\d+)위안')
    # myPattern = re.compile(r'(\d+(?:,\d+)*)위안')
    # myPattern = re.compile(r'(\d+(?:,\d+)*)(조|억|만)\s위안')
    trText = trText.replace(",","")
    # myPattern = re.compile(r'((\d+(?:조)?\d*(?:억)?)?\d*(?:만)?)(?:\s위안)')
    # Updated regex pattern to capture decimal numbers as well at the current time : 2025-10-27 20:50:02
    # Original pattern: r'((\d+(?:조)?\d*(?:억)?)?\d*(?:만)?)(?:\s위안)'
    # New pattern includes optional decimal part: (?:\.\d+)?
    myPattern = re.compile(r'((\d+(?:\.\d+)?(?:조)?\d*(?:\.\d+)?(?:억)?)?\d*(?:\.\d+)?(?:만)?)(?:위안)')
  
    match = re.search(myPattern, trText)
    print(f'{match=}')  # Display the match object
    
    if match:
        if "." in match.group(1):
            match_float = float(match.group(1))
            print(f"Extracted number is floating point: {match.group(1)} : {match_float}")
            # CNY_KRW_RT = convert_yfinance()
        # Remove commas from the matched group before converting to int
        # price_CNY = int(match.group(1).replace(',', ''))  # Extract the first group and convert to int
        price_CNY_str = match.group(1).replace(',', '')  # Extract the first group and convert to int
        print(f'{price_CNY_str=}')  # Display the extracted number
        # suffix = match.group(2)  # Capture the suffix (조, 억, 만) for pattern matching
        
        price_CNY = 0
        if r"조" in price_CNY_str:
            # print(f"조 found in trText: {trText}")
            myPattern1 = re.compile(r'(\d+)조')
            match = re.search(myPattern1, trText)
            print(f'{match=}')  # Display the match object
            if match:
                # print(f'{match.group(0)=}') # 6조
                print(f'{match.group(1)=}') # 6
                price_CNY_int = int(match.group(1))  # Extract the first group and convert to int
                price_CNY = price_CNY_int * 10**12
        if r"억" in price_CNY_str:
            # print(f"억 found in trText: {trText}")
            myPattern1 = re.compile(r'(\d+)억')
            match = re.search(myPattern1, trText)
            print(f'{match=}')  # Display the match object
            if match:
                # print(f'{match.group(0)=}') # 6억
                print(f'{match.group(1)=}') # 6
                price_CNY_int = int(match.group(1))  # Extract the first group and convert to int
                price_CNY += price_CNY_int * 10**8
        if r"만" in price_CNY_str:
            # print(f"만 found in trText: {trText}")
            myPattern1 = re.compile(r'(\d+)만')
            match = re.search(myPattern1, trText)
            print(f'{match=}')  # Display the match object
            if match:
                # print(f'{match.group(0)=}') # 6만
                print(f'{match.group(1)=}') # 6
                price_CNY_int = int(match.group(1))  # Extract the first group and convert to int
                price_CNY += price_CNY_int * 10**4
        
        if match_float:
            price_CNY += match_float 
        
        # else:
        #     print(":: CNY => " + f'{price_CNY:,}')  # Displays the extracted number with commas

        # price_CNY = int(price_CNY_str)  # Extract the first group and convert to int
        print(f'{price_CNY=:,}')  # Display the extracted number

        if CNY_KRW_RT == 0:  # Get the exchange rate only once
            # price_KRW = convert_(price_CNY)
            CNY_KRW_RT = convert_yfinance()
            # CNY_KRW_RT = 199.56
            price_KRW = price_CNY * CNY_KRW_RT
            print(f"*** checkYuan() :: CNY_KRW_RT = {CNY_KRW_RT:.2f}")
            print(f"*** checkYuan() :: price_KRW = {price_KRW:,.0f}")
        else:
            price_KRW = price_CNY * CNY_KRW_RT
            print(f"*** checkYuan() :: price_KRW = {price_KRW:,.0f}")
        return price_KRW
    else:
        print("*** No price in CNY found in checkYuan(trText).")
        return False
    
def checkYuan_RT(trText):
    # translated_text = r'지방 보조금 총액은 20조 위안이다.'
    # trText = r'간쑤성 지스산: 재건 및 정착을 위한 대출이 지급되기 시작했는데, 총액이 15억 위안을 초과했습니다.'
    translation_trText = re.sub(r'​', '', trText)
    if r"위안" in translation_trText:
        # myPattern = re.compile(r'(\d+(?:,\d+)*)(조|억|만| )\s위안')
        # match = re.search(myPattern, translation_trText)
        # if not match:
        #     return False
            
        price_KRW = checkYuan(translation_trText)  # if '위안' then convert CNY to KRW    
        if price_KRW:
            # match price_KRW:
            #     case price_KRW if price_KRW >= 10**12:
            #         print(f" :=> {price_KRW:,.0f} KRW = {(price_KRW/10**12):,.0f}조 KRW")
            #     case price_KRW if price_KRW >= 10**8:
            #         print(f" :=> {price_KRW:,.0f} KRW = {(price_KRW/10**8):,.0f}억 KRW")
            #     case price_KRW if price_KRW >= 10**4:
            #         print(f" :=> {price_KRW:,.0f} KRW = {(price_KRW/10**4):,.0f}만 KRW")
            #     case _:
            #         print(f" {trText} :=> {price_KRW:,.0f} KRW")
            if price_KRW >= 10**12:
                print(f" :=> {price_KRW:,.0f} KRW = {(price_KRW/10**12):,.0f}조 KRW")
            elif price_KRW >= 10**8:
                print(f" :=> {price_KRW:,.0f} KRW = {(price_KRW/10**8):,.0f}억 KRW")
            elif price_KRW >= 10**4:
                print(f" :=> {price_KRW:,.0f} KRW = {(price_KRW/10**4):,.0f}만 KRW")
            else:
                print(f" {trText} :=> {price_KRW:,.0f} KRW")
        else:
            print(f"if price_KRW={price_KRW}: Google==> {translation_trText}")
    else:
        print(f"if r\"위안\" in translation_trText: Google==> {translation_trText}")
    return price_KRW
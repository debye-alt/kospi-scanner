"""
KOSPI 종목 '저점 후 반등' 스캐너 (앱 연동용 JSON 출력 버전)
=================================================================
GitHub Actions에서 매일 자동 실행되어 data/results.json을 갱신하는 용도로 설계됨.
로직은 기존 콘솔용 스크립트와 동일하며, JSON 직렬화 출력만 추가됨.

※ 투자 참고용 스크리닝 도구입니다. 매수/매도 추천이 아닙니다.

사전 설치:
    pip install -r requirements.txt
"""

import argparse
import datetime as dt
import json
import sys
import time
from typing import Optional, Dict

import numpy as np
import pandas as pd

try:
    from pykrx import stock
except ImportError:
    print("pykrx가 설치되어 있지 않습니다. 'pip install -r requirements.txt' 실행 후 다시 시도하세요.")
    sys.exit(1)


def get_ticker_universe(top_n: int, base_date: str) -> pd.DataFrame:
    cap_df = stock.get_market_cap(base_date, market="KOSPI")
    cap_df = cap_df.sort_values("시가총액", ascending=False).head(top_n)
    tickers = cap_df.index.tolist()
    names = [stock.get_market_ticker_name(t) for t in tickers]
    return pd.DataFrame({"code": tickers, "name": names})


def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def analyze_one(code: str, name: str, start: str, end: str,
                 lookback: int, rebound_days: int,
                 rebound_pct: float) -> Optional[Dict]:
    df = stock.get_market_ohlcv(start, end, code)
    if df is None or len(df) < lookback + 5:
        return None

    df = df.rename(columns={"종가": "close", "거래량": "volume"})
    close = df["close"]

    window = close.iloc[-lookback:]
    low_price = window.min()
    low_date = window.idxmin()
    last_price = close.iloc[-1]
    last_date = close.index[-1]

    days_since_low = (last_date - low_date).days
    if days_since_low < 3:
        return None

    pct_from_low = (last_price - low_price) / low_price * 100
    if pct_from_low < rebound_pct:
        return None

    ma5 = close.rolling(5).mean()
    ma20 = close.rolling(20).mean()
    golden_cross = bool(ma5.iloc[-1] > ma20.iloc[-1] and ma5.iloc[-2] <= ma20.iloc[-2])
    above_ma20 = bool(ma5.iloc[-1] > ma20.iloc[-1])

    rsi = compute_rsi(close)
    rsi_now = rsi.iloc[-1]
    rsi_min_recent = rsi.iloc[-lookback:].min()
    rsi_recovering = bool(pd.notna(rsi_min_recent) and rsi_min_recent < 35 and rsi_now > rsi_min_recent + 5)

    vol = df["volume"]
    vol_recent = vol.iloc[-rebound_days:].mean()
    vol_before = vol.iloc[-lookback:-rebound_days].mean()
    volume_up = bool(vol_before > 0 and vol_recent > vol_before * 1.1)

    score = 0.0
    score += min(pct_from_low, 30)
    score += 20 if golden_cross else (10 if above_ma20 else 0)
    score += 20 if rsi_recovering else 0
    score += 10 if volume_up else 0

    return {
        "code": code,
        "name": name,
        "low_date": low_date.strftime("%Y-%m-%d"),
        "low_price": int(low_price),
        "last_price": int(last_price),
        "pct_from_low": round(pct_from_low, 1),
        "golden_cross": golden_cross,
        "rsi_now": round(rsi_now, 1) if pd.notna(rsi_now) else None,
        "rsi_recovering": rsi_recovering,
        "volume_up": volume_up,
        "score": round(score, 1),
    }


def main():
    parser = argparse.ArgumentParser(description="KOSPI 저점-반등 종목 스캐너 (JSON 출력)")
    parser.add_argument("--top", type=int, default=100)
    parser.add_argument("--lookback", type=int, default=60)
    parser.add_argument("--rebound-days", type=int, default=10)
    parser.add_argument("--rebound-pct", type=float, default=5.0)
    parser.add_argument("--min-score", type=float, default=40.0)
    parser.add_argument("--out", type=str, default=None, help="CSV로도 저장하려면 파일명 지정")
    parser.add_argument("--json-out", type=str, default="data/results.json", help="JSON 결과 파일 경로")
    args = parser.parse_args()

    today = dt.date.today()
    end = today.strftime("%Y%m%d")
    start = (today - dt.timedelta(days=int(args.lookback * 1.6) + 30)).strftime("%Y%m%d")
    base_date = end

    print(f"[1/3] 시가총액 상위 {args.top}개 종목 목록 가져오는 중...")
    universe = get_ticker_universe(args.top, base_date)

    results = []
    print(f"[2/3] 종목별 분석 중 (총 {len(universe)}개)...")
    for _, row in universe.iterrows():
        try:
            res = analyze_one(
                row["code"], row["name"], start, end,
                args.lookback, args.rebound_days, args.rebound_pct,
            )
            if res:
                results.append(res)
        except Exception as e:
            print(f"  - {row['name']}({row['code']}) 분석 실패: {e}")
        time.sleep(0.05)

    df_result = pd.DataFrame(results)
    if not df_result.empty:
        df_result = df_result[df_result["score"] >= args.min_score]
        df_result = df_result.sort_values("score", ascending=False)

    print(f"[3/3] 결과 {len(df_result)}건")

    if args.out:
        df_result.to_csv(args.out, index=False, encoding="utf-8-sig")
        print(f"CSV 저장: {args.out}")

    payload = {
        "generated_at": dt.datetime.now().isoformat(timespec="seconds"),
        "params": {
            "top": args.top,
            "lookback": args.lookback,
            "rebound_days": args.rebound_days,
            "rebound_pct": args.rebound_pct,
            "min_score": args.min_score,
        },
        "count": len(df_result),
        "candidates": df_result.to_dict(orient="records"),
    }
    with open(args.json_out, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"JSON 저장: {args.json_out}")


if __name__ == "__main__":
    main()

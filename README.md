# 코스피 저점-반등 스캐너 — 안드로이드 앱(PWA) 설치 가이드

이 프로젝트는 서버 없이 **GitHub(무료)** 만으로 동작합니다.
- GitHub Actions가 평일 16:00(KST) 자동으로 스캐너를 실행
- 결과를 `data/results.json`에 저장
- GitHub Pages가 그 결과를 보여주는 웹앱을 호스팅
- 안드로이드 크롬에서 "홈 화면에 추가"하면 일반 앱처럼 아이콘이 생김

## 1. 저장소 만들기
1. https://github.com 에서 무료 계정 생성 (이미 있다면 생략)
2. 우측 상단 `+` → `New repository`
3. 이름 예: `kospi-scanner` , **Public**으로 설정
   - GitHub Pages 무료 호스팅은 Public 저장소에서만 동작합니다.
   - 종목 스크리닝 결과만 들어가므로 공개되어도 문제없는 정보입니다.
4. `Create repository`

## 2. 파일 업로드
1. 저장소 페이지에서 `Add file` → `Upload files`
2. 이 zip 안의 모든 파일/폴더를 그대로 끌어다 놓기 (폴더 구조 유지)
   - `.github/workflows/scan.yml`
   - `data/results.json`
   - `icons/icon-192.png`, `icons/icon-512.png`
   - `index.html`, `manifest.json`, `sw.js`, `scanner.py`, `requirements.txt`
3. `Commit changes`

> 웹 업로드로는 빈 폴더가 잘 안 올라갈 수 있어요. 만약 `.github/workflows/scan.yml`이
> 안 보이면, 저장소 화면에서 직접 `Add file → Create new file`로 경로를 입력하며
> (`.github/workflows/scan.yml`) 내용을 복사해 넣어도 됩니다.

## 3. Actions 쓰기 권한 켜기 (필수)
자동으로 결과를 커밋하려면 권한이 필요합니다.
1. 저장소 `Settings` → `Actions` → `General`
2. 맨 아래 `Workflow permissions`에서 **Read and write permissions** 선택 → `Save`

## 4. GitHub Pages 켜기
1. 저장소 `Settings` → `Pages`
2. `Source`: `Deploy from a branch`
3. `Branch`: `main` / `/ (root)` 선택 → `Save`
4. 잠시 후 상단에 뜨는 주소가 앱 주소입니다.
   (예: `https://내아이디.github.io/kospi-scanner/`)

## 5. 첫 데이터 생성 (수동 실행)
첫 자동 실행 전까지는 데이터가 비어있습니다. 바로 채우려면:
1. 저장소 `Actions` 탭
2. 좌측 `KOSPI 저점-반등 스캔` 클릭
3. 우측 `Run workflow` → `Run workflow` 클릭
4. 1~3분 정도 후 완료되면 `data/results.json`이 자동으로 갱신됩니다.

이후로는 평일 16:00(KST)에 자동으로 실행됩니다 (cron 특성상 몇 분 정도 지연될 수 있어요).

## 6. 안드로이드에 앱처럼 설치하기
1. 안드로이드 폰 **Chrome**에서 4번에서 확인한 주소로 접속
2. 우측 상단 `⋮` 메뉴 → `홈 화면에 추가` (또는 화면 하단에 뜨는 설치 배너 사용)
3. 홈 화면에 아이콘이 생기고, 탭하면 주소창 없이 앱처럼 열립니다.

## 7. 조건 바꾸고 싶을 때
`.github/workflows/scan.yml`의 아래 부분 숫자만 수정하면 됩니다.
```
--top 100          # 분석 대상 종목 수 (시가총액 상위)
--lookback 60      # 저점을 찾는 기간 (거래일)
--rebound-pct 5    # 저점 대비 최소 반등률(%)
--min-score 40     # 결과에 포함할 최소 점수
```
수정 후 커밋하면 다음 실행부터 새 조건이 적용됩니다.

## 참고
- 이 도구는 종가 기준 기계적 스크리닝 결과이며, 매수·매도 추천이 아닙니다.
- pykrx는 KRX 공개 데이터를 사용하며, GitHub Actions 서버에서 실행되므로
  네트워크 문제로 가끔 특정 종목이 누락될 수 있습니다 (로그에서 확인 가능).

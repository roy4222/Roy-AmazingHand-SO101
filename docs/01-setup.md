# 01 — Setup

> 環境、相依、安裝、執行步驟。執行機為 Raspberry Pi 5；WSL repo 為真相源，腳本 rsync 到 Pi 跑。

## 環境需求

- **Pi 5**：`ssh pi5`（Tailscale alias），user `roy422`，在 `dialout` 群組。
- **USB-TTL serial bus driver**：CH343（QinHeng `1a86:55d3`），序號 `5B42133808`。程式一律用穩定路徑：
  `/dev/serial/by-id/usb-1a86_USB_Single_Serial_5B42133808-if00`（鎖此 adapter，不會誤指 SO-101 的 adapter）。
- **電源**：AmazingHand 外接 **5V**（≥2A；與 SO-101 7.4V 分開、與 USB-TTL 共地）。SCS0009 標稱 6V（可用 ~4–7.4V）。
- **Python**：`~/amazinghand/.venv`（uv，Python 3.10.20），`rustypot==1.5.0`、`numpy==2.2.6`。baud `1000000`。

## 安裝步驟（Pi）

```bash
~/.local/bin/uv venv ~/amazinghand/.venv --python 3.10
~/.local/bin/uv pip install --python ~/amazinghand/.venv/bin/python rustypot numpy
```

bring-up 腳本（WSL → Pi）：
```bash
rsync -az ~/RoyBot/RoyBot-Lab/src/Roy-AmazingHand-SO101/bringup/ pi5:amazinghand/bringup/
```

## Build / Run

無 build。腳本在 `~/amazinghand/bringup/`，env 參數化：

- 選手指：`AH_ID1`/`AH_ID2`（f1=1,2 f2=3,4 f3=5,6 f4=7,8）。
- 動作腳本要 `AH_BRINGUP_ARM=1` 才會動（否則 DRY RUN 唯讀）。`set_id.py` 要 `AH_SET_ID=1` 才寫入。

```bash
# 唯讀掃描
ssh pi5 'cd ~/amazinghand/bringup && ~/amazinghand/.venv/bin/python bus_scan.py'
# 某指回中位
ssh pi5 'cd ~/amazinghand/bringup && AH_ID1=3 AH_ID2=4 AH_BRINGUP_ARM=1 ~/amazinghand/.venv/bin/python middlepos_set.py'
# 某指開閉循環
ssh pi5 'cd ~/amazinghand/bringup && AH_ID1=3 AH_ID2=4 AH_BRINGUP_ARM=1 ~/amazinghand/.venv/bin/python finger_cycle.py'
```

**停 / 釋放：關 5V 最可靠**（Ctrl-C 只中斷腳本，servo 會停在當下位置 hold）。
